#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用轻小说插图文本提取与数字化工具 (General Illustration Text Extractor)

功能特性：
1. EPUB 资源自动扫描：从 EPUB 文件中自动提取封面、彩插与正文手写信/日记插图。
2. 图像增强预处理流水线：灰度化、自适应对比度增强、二值化去网点背景、智能边距裁剪，显著提升字迹辨识度。
3. 多后端识别架构 (Multi-Engine Architecture)：
   - Gemini Vision 大模型引擎：针对轻小说艺术手写体、竖排日文/繁体、复杂底纹日记的最佳实践（零错字、自然段落还原）。
   - 本地 OCR 引擎 (Pytesseract / EasyOCR)：支持离线环境下的文字识别。
4. 文本规范化与简繁转换：集成 zhconv 实现繁体字、异体字向标准简体转换，规范引号、破折号与换行排版。
5. 结构化多格式导出：支持导出为 Markdown 文档、JSON 数据集、或直接嵌入 convert_all.py 的 Python 列表模块。
"""

import os
import sys
import re
import io
import json
import base64
import argparse
import glob
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path

# 终端输出编码自适应
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 可选依赖按需导入
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    HAS_EBOOK = True
except ImportError:
    HAS_EBOOK = False

try:
    import zhconv
    HAS_ZHCONV = True
except ImportError:
    HAS_ZHCONV = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


# ==============================================================================
# 一、图像预处理管线 (Image Preprocessing Pipeline)
# ==============================================================================

class ImagePreprocessor:
    """图像增强器：针对轻小说扫描插图与手写体进行去噪与对比度增强"""

    @staticmethod
    def enhance_for_ocr(
        img: 'Image.Image',
        grayscale: bool = True,
        contrast_factor: float = 2.0,
        autocontrast: bool = True,
        binarize_threshold: Optional[int] = None,
        scale_factor: float = 1.0
    ) -> 'Image.Image':
        """
        对输入 PIL 图像执行预处理增强流水线
        """
        if not HAS_PIL:
            raise RuntimeError("PIL (Pillow) 未安装，无法执行图像预处理。请运行 pip install pillow")

        processed = img.copy()

        # 1. 转为 RGB 避免 RGBA 模式下的透明度干扰
        if processed.mode in ('RGBA', 'LA') or (processed.mode == 'P' and 'transparency' in processed.info):
            bg = Image.new('RGB', processed.size, (255, 255, 255))
            if processed.mode == 'P':
                processed = processed.convert('RGBA')
            bg.paste(processed, mask=processed.split()[3])
            processed = bg
        elif processed.mode != 'RGB':
            processed = processed.convert('RGB')

        # 2. 缩放尺寸（保证字迹高度足够）
        if scale_factor != 1.0:
            new_w = int(processed.width * scale_factor)
            new_h = int(processed.height * scale_factor)
            processed = processed.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 3. 灰度化
        if grayscale:
            processed = ImageOps.grayscale(processed)

        # 4. 自动对比度拉伸
        if autocontrast:
            processed = ImageOps.autocontrast(processed, cutoff=2)

        # 5. 对比度加强
        if contrast_factor != 1.0:
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(contrast_factor)

        # 6. 二值化去底纹
        if binarize_threshold is not None:
            table = [0 if i < binarize_threshold else 255 for i in range(256)]
            processed = processed.point(table, '1')

        return processed

    @staticmethod
    def auto_crop(img: 'Image.Image', padding: int = 10) -> 'Image.Image':
        """自动裁剪掉图像外围的多余纯白/黑边框"""
        if not HAS_PIL:
            return img
        gray = ImageOps.grayscale(img)
        # 求非白区域包围盒
        inverted = ImageOps.invert(gray)
        bbox = inverted.getbbox()
        if bbox:
            left = max(0, bbox[0] - padding)
            top = max(0, bbox[1] - padding)
            right = min(img.width, bbox[2] + padding)
            bottom = min(img.height, bbox[3] + padding)
            return img.crop((left, top, right, bottom))
        return img


# ==============================================================================
# 二、EPUB 插图提取器 (EPUB Illustration Extractor)
# ==============================================================================

class EpubIllustrationExtractor:
    """从 EPUB 电子书中批量解包与筛选插图"""

    @staticmethod
    def extract_images_from_epub(
        epub_path: str,
        output_dir: str,
        min_size_kb: int = 30,
        filter_covers: bool = False
    ) -> List[Dict[str, Union[str, int]]]:
        """
        解包 EPUB 中的所有图片资源并按顺序命名保存
        返回提取的图片元数据列表
        """
        if not HAS_EBOOK:
            raise RuntimeError("EbookLib 未安装，无法读取 EPUB 文件。请运行 pip install EbookLib")

        os.makedirs(output_dir, exist_ok=True)
        book = epub.read_epub(epub_path)
        extracted = []

        img_index = 1
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                content = item.get_content()
                size_kb = len(content) / 1024.0

                if size_kb < min_size_kb:
                    # 忽略图标、装饰分割线等极小图片
                    continue

                original_name = item.get_name()
                ext = os.path.splitext(original_name)[1].lower()
                if not ext:
                    ext = ".jpg"

                # 封面过滤判断
                is_cover = any(k in original_name.lower() for k in ['cover', 'titlepage'])
                if filter_covers and is_cover:
                    continue

                filename = f"{img_index:03d}{ext}"
                out_path = os.path.join(output_dir, filename)

                with open(out_path, 'wb') as f:
                    f.write(content)

                width, height = (0, 0)
                if HAS_PIL:
                    try:
                        with Image.open(out_path) as im:
                            width, height = im.size
                    except Exception:
                        pass

                extracted.append({
                    'index': img_index,
                    'filename': filename,
                    'path': out_path,
                    'original_name': original_name,
                    'size_kb': round(size_kb, 1),
                    'width': width,
                    'height': height,
                    'is_cover': is_cover
                })
                img_index += 1

        return extracted


# ==============================================================================
# 三、文字识别引擎管理器 (Multi-Engine OCR Manager)
# ==============================================================================

class OcrEngineManager:
    """多后端 OCR 识别调度器"""

    def __init__(self, engine: str = 'auto', api_key: Optional[str] = None):
        self.engine = engine.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def recognize_image(self, image_path: str, prompt_hint: str = "") -> str:
        """
        对指定图片执行 OCR，根据配置自动回退调度
        """
        if self.engine == 'gemini' or (self.engine == 'auto' and self.api_key):
            try:
                return self._recognize_via_gemini(image_path, prompt_hint)
            except Exception as e:
                print(f"[警告] Gemini Vision 识别失败: {e}，尝试本地备用引擎...", file=sys.stderr)

        if HAS_PYTESSERACT:
            return self._recognize_via_tesseract(image_path)

        raise RuntimeError(
            "未能成功调用任何 OCR 引擎！请确保设置了 GEMINI_API_KEY 环境变量，"
            "或安装本地 OCR 库（如 pytesseract 与 Tesseract-OCR）。"
        )

    def _recognize_via_gemini(self, image_path: str, prompt_hint: str = "") -> str:
        """调用 Gemini 视觉模型识别插图手写体或排版文本"""
        import urllib.request
        import urllib.error

        api_key = self.api_key
        if not api_key:
            raise ValueError("未检测到 GEMINI_API_KEY，无法调用 Gemini Vision API。")

        # 读取图像并转为 Base64
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
        b64_data = base64.b64encode(img_bytes).decode('utf-8')

        # 确定 MIME 类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
        mime_type = mime_map.get(ext, 'image/jpeg')

        default_prompt = (
            "这是一张轻小说中的插图/手写日记/信件/地图/设定图纸。"
            "请严格提取并逐字转录图片中的所有文字内容，不要遗漏任何段落。"
            "要求：\n"
            "1. 严格忠实于原图字句，保持原有的段落换行与标点符号；\n"
            "2. 如果是手写体或竖排文字，请按正常的阅读顺序排版为整齐段落；\n"
            "3. 只输出转录出来的正文文本，不要包含任何前言、后记、总结或markdown代码块标记。"
        )
        final_prompt = f"{default_prompt}\n提示信息：{prompt_hint}" if prompt_hint else default_prompt

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": final_prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096
            }
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_body = resp.read().decode('utf-8')
            res_json = json.loads(resp_body)
            candidates = res_json.get('candidates', [])
            if candidates and 'content' in candidates[0] and 'parts' in candidates[0]['content']:
                parts = candidates[0]['content']['parts']
                text = "".join(p.get('text', '') for p in parts)
                return text.strip()
            return ""

    def _recognize_via_tesseract(self, image_path: str) -> str:
        """调用本地 Tesseract 引擎识别"""
        if not HAS_PIL or not HAS_PYTESSERACT:
            raise RuntimeError("请先安装 pillow 与 pytesseract: pip install pillow pytesseract")
        img = Image.open(image_path)
        # 尝试中简+中繁+日文多语言
        try:
            text = pytesseract.image_to_string(img, lang='chi_sim+chi_tra+jpn')
        except Exception:
            text = pytesseract.image_to_string(img)
        return text.strip()


# ==============================================================================
# 四、文本清洗与排版规范化 (Text Normalization & Formatting)
# ==============================================================================

class TextCleaner:
    """文本清洗与多格式导出"""

    @staticmethod
    def clean_and_normalize(text: str, to_simplified: bool = True) -> str:
        """规范化清洗：转为规范简体，去除孤立乱码，合并冗余断行"""
        if not text:
            return ""

        # 1. 繁简转换
        if to_simplified and HAS_ZHCONV:
            text = zhconv.convert(text, 'zh-cn')

        # 2. 规范中文标点
        text = text.replace('...', '……')
        text = re.sub(r'—{1,2}', '——', text)

        # 3. 按行清洗并保留合理段落
        lines = [line.strip(' \t\r') for line in text.split('\n')]
        cleaned_lines = []
        for line in lines:
            if not line:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def export_as_python_module(lines: List[str], var_name: str = "EXTRACTED_ILLUSTRATION_TEXT") -> str:
        """导出为可以直接 import 到 convert_all.py 中的 Python 列表代码"""
        escaped_lines = [json.dumps(line, ensure_ascii=False) for line in lines]
        py_code = (
            f"# -*- coding: utf-8 -*-\n"
            f'"""由 extract_image_text.py 自动生成的插图转录文本数据"""\n\n'
            f"{var_name} = [\n    " + ",\n    ".join(escaped_lines) + "\n]\n"
        )
        return py_code


# ==============================================================================
# 五、命令行入口 (CLI Interface)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="通用轻小说插图文本提取与数字化工具 (General Illustration Text Extractor)",
        formatter_class=argparse.RawTextHelpFormatter
    )

    group_input = parser.add_argument_group("输入选项 (至少指定一项)")
    group_input.add_argument("-e", "--epub", help="指定要解包提取插图的 EPUB 文件路径")
    group_input.add_argument("-i", "--image", help="单张待识别插图路径")
    group_input.add_argument("-d", "--dir", help="包含多张插图的目录路径")

    group_opt = parser.add_argument_group("识别与处理选项")
    group_opt.add_argument("--engine", choices=['auto', 'gemini', 'tesseract'], default='auto',
                           help="OCR 引擎选择 (默认: auto，优先 Gemini Vision，回退 Tesseract)")
    group_opt.add_argument("--api-key", help="Gemini API 密钥 (默认从环境变量 GEMINI_API_KEY 读取)")
    group_opt.add_argument("--preprocess", action="store_true", help="是否在 OCR 前进行灰度/对比度/二值化图像增强")
    group_opt.add_argument("--no-simplify", action="store_true", help="不进行繁体转简体")
    group_opt.add_argument("--hint", default="", help="传递给大模型的额外场景提示 (例如: '无职转生第15卷未来老人日记')")

    group_out = parser.add_argument_group("输出选项")
    group_out.add_argument("-o", "--out", help="结果输出文件路径 (.md, .json, .py, .txt)")
    group_out.add_argument("--format", choices=['markdown', 'python', 'json', 'text'], default='markdown',
                           help="输出数据格式 (默认: markdown)")
    group_out.add_argument("--extract-dir", help="EPUB 插图解包保存目录 (默认: scratch/extracted_imgs/)")

    args = parser.parse_args()

    if not args.epub and not args.image and not args.dir:
        parser.print_help()
        print("\n错误：必须指定 --epub, --image 或 --dir 之一作为输入源！", file=sys.stderr)
        sys.exit(1)

    images_to_process: List[str] = []

    # 1. 处理 EPUB 解包
    if args.epub:
        if not os.path.exists(args.epub):
            print(f"错误：指定的 EPUB 文件不存在: {args.epub}", file=sys.stderr)
            sys.exit(1)
        extract_dir = args.extract_dir or os.path.join("scratch", "extracted_imgs", Path(args.epub).stem)
        print(f"[*] 正在从 EPUB 中解包插图: {args.epub} -> {extract_dir}")
        items = EpubIllustrationExtractor.extract_images_from_epub(args.epub, extract_dir)
        print(f"[+] 成功提取 {len(items)} 张高分辨率插图。")
        images_to_process = [it['path'] for it in items]

    # 2. 处理单图
    elif args.image:
        if not os.path.exists(args.image):
            print(f"错误：指定的图片文件不存在: {args.image}", file=sys.stderr)
            sys.exit(1)
        images_to_process = [args.image]

    # 3. 处理图片目录
    elif args.dir:
        if not os.path.isdir(args.dir):
            print(f"错误：指定的目录不存在: {args.dir}", file=sys.stderr)
            sys.exit(1)
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        images_to_process = sorted([
            os.path.join(args.dir, f) for f in os.listdir(args.dir)
            if os.path.splitext(f)[1].lower() in valid_exts
        ])
        print(f"[*] 在目录 {args.dir} 中检索到 {len(images_to_process)} 张图片待处理。")

    if not images_to_process:
        print("未找到需要识别的图像文件，流程结束。")
        sys.exit(0)

    # 4. 初始化 OCR 引擎
    ocr_manager = OcrEngineManager(engine=args.engine, api_key=args.api_key)
    all_results: List[Dict[str, Union[str, int]]] = []

    print("\n[*] 开始执行插图文字提取流程...")
    for idx, img_path in enumerate(images_to_process, start=1):
        fname = os.path.basename(img_path)
        print(f" -> [{idx}/{len(images_to_process)}] 正在处理: {fname} ...", end="", flush=True)

        target_img_path = img_path
        # 若指定预处理增强
        if args.preprocess and HAS_PIL:
            try:
                with Image.open(img_path) as im:
                    enhanced = ImagePreprocessor.enhance_for_ocr(im, contrast_factor=2.2, autocontrast=True)
                    enhanced = ImagePreprocessor.auto_crop(enhanced)
                    temp_dir = os.path.join("scratch", "_temp_enhanced")
                    os.makedirs(temp_dir, exist_ok=True)
                    target_img_path = os.path.join(temp_dir, f"enhanced_{fname}")
                    enhanced.save(target_img_path)
            except Exception as e:
                print(f" (预处理略过: {e})", end="")

        try:
            raw_text = ocr_manager.recognize_image(target_img_path, prompt_hint=args.hint)
            cleaned = TextCleaner.clean_and_normalize(raw_text, to_simplified=not args.no_simplify)
            char_count = len(re.sub(r'\s+', '', cleaned))
            print(f" 成功! 提取到 {char_count} 字。")

            all_results.append({
                'index': idx,
                'image': fname,
                'path': img_path,
                'text': cleaned,
                'char_count': char_count
            })
        except Exception as e:
            print(f" 失败: {e}")
            all_results.append({
                'index': idx,
                'image': fname,
                'path': img_path,
                'text': "",
                'char_count': 0,
                'error': str(e)
            })

    # 5. 格式化输出
    out_format = args.format.lower()
    if args.out:
        out_ext = os.path.splitext(args.out)[1].lower()
        if out_ext == '.py':
            out_format = 'python'
        elif out_ext == '.json':
            out_format = 'json'
        elif out_ext in ('.md', '.markdown'):
            out_format = 'markdown'
        elif out_ext == '.txt':
            out_format = 'text'

    output_content = ""
    if out_format == 'markdown':
        blocks = ["# 插图文字提取结果全集\n"]
        for res in all_results:
            blocks.append(f"## 插图 {res['image']}（{res['char_count']} 字）\n")
            if res['text']:
                blocks.append(res['text'] + "\n")
            else:
                blocks.append("*(未能识别到有效文字或无文本)*\n")
        output_content = "\n".join(blocks)

    elif out_format == 'python':
        all_lines = []
        for res in all_results:
            if res['text']:
                all_lines.extend(res['text'].split('\n'))
        output_content = TextCleaner.export_as_python_module(all_lines)

    elif out_format == 'json':
        output_content = json.dumps(all_results, ensure_ascii=False, indent=2)

    elif out_format == 'text':
        blocks = []
        for res in all_results:
            if res['text']:
                blocks.append(res['text'])
        output_content = "\n\n".join(blocks)

    # 6. 保存或打印
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"\n[+] 成果已成功保存至: {args.out}")
    else:
        print("\n" + "=" * 50)
        print(output_content)
        print("=" * 50)


if __name__ == '__main__':
    main()
