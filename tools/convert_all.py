#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量将 EPUB 小说转为按章切分的 Markdown 工具
按照 prompt/00_tool_create.md 的规范设计与实现
"""

import os
import sys
import re
import argparse
import glob
from typing import List, Dict, Tuple, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Tag

try:
    from tools.vol15_diary_data import VOL15_DIARY_TEXT_PART1, VOL15_DIARY_TEXT_PART2_A, VOL15_DIARY_TEXT_PART2_B
except ImportError:
    from vol15_diary_data import VOL15_DIARY_TEXT_PART1, VOL15_DIARY_TEXT_PART2_A, VOL15_DIARY_TEXT_PART2_B


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符（针对 Windows/Unix）"""
    # 将 Windows 下非法的半角符号替换为全角或安全符号
    replacements = {
        ':': '：',
        '?': '？',
        '*': '＊',
        '"': '”',
        '<': '《',
        '>': '》',
        '|': '｜',
        '/': '／',
        '\\': '＼',
    }
    for char, rep in replacements.items():
        name = name.replace(char, rep)
    # 去除多余控制字符
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    # 去除首尾空格和点
    name = name.strip(' .')
    return name if name else "untitled"


def extract_ncx_map(book: epub.EpubBook) -> Dict[str, str]:
    """从 NCX (toc.ncx) 解析 href -> title 映射字典"""
    ncx_map = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_NAVIGATION:
            try:
                soup = BeautifulSoup(item.get_content(), 'xml')
                for nav in soup.find_all('navPoint'):
                    label = nav.find('navLabel')
                    text_tag = label.find('text') if label else None
                    content_tag = nav.find('content')
                    if text_tag and content_tag and content_tag.get('src'):
                        src = content_tag['src'].split('#')[0]
                        src_clean = os.path.basename(src)
                        title = text_tag.get_text(strip=True)
                        if src_clean and title and src_clean not in ncx_map:
                            ncx_map[src_clean] = title
            except Exception as e:
                pass
    return ncx_map


def extract_fallback_title(soup: BeautifulSoup) -> str:
    """NCX缺失时的标题兜底提取：正文第一个 h1~h6 或标题类样式的 p"""
    # 1. 查找 h1~h6
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # br 转为空格
        for br in h.find_all('br'):
            br.replace_with(' ')
        text = h.get_text(" ", strip=True)
        text = re.sub(r'[ \t\r\n]+', ' ', text).strip(' \t\r\n')
        if text:
            return text

    # 2. 查找具有标题特征 class 的 p 标签（如 pius1, title, chapter-title）
    for p in soup.find_all('p'):
        classes = p.get('class', [])
        if any(c in ['pius1', 'title', 'chapter-title', 'pius2'] for c in classes):
            for br in p.find_all('br'):
                br.replace_with(' ')
            text = p.get_text(" ", strip=True)
            text = re.sub(r'[ \t\r\n]+', ' ', text).strip(' \t\r\n')
            if text:
                return text

    return ""


def clean_paragraph_text(p_tag: Tag) -> str:
    """清理段落内部文本：br 转为空格，处理空白与特殊全角符号"""
    for br in p_tag.find_all('br'):
        br.replace_with(' ')
    text = p_tag.get_text()
    # 替换不可见空格 &nbsp; / \xa0 为普通空格
    text = text.replace('\xa0', ' ')
    # 段首段尾去除普通空格/换行/制表符，但保留日文全角空格 \u3000
    text = text.strip(' \t\r\n')
    return text


def clean_xhtml_body_to_markdown_blocks(html_content: bytes, chapter_title: str = "") -> List[str]:
    """
    将 XHTML 正文清洗为 Markdown 内容段落块列表
    严格遵循六不原则与格式清洗要求
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. 整体删除 script, style
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    # 2. ruby 处理：删除 rt, rp 标签及内容，保留汉字
    for ruby in soup.find_all('ruby'):
        for sub in ruby.find_all(['rt', 'rp']):
            sub.decompose()

    # 3. img 处理：若所在 div class 含 illus 则删掉整个 div；否则只删 img
    for div in soup.find_all('div'):
        classes = div.get('class', [])
        if any('illus' in str(c).lower() for c in classes):
            div.decompose()
    for img in soup.find_all('img'):
        img.decompose()

    # 4. 遍历主体内的标题与段落
    blocks = []
    body = soup.find('body') or soup

    norm_title = re.sub(r'\s+', '', chapter_title)

    for elem in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if getattr(elem, 'decomposed', False):
            continue

        if elem.name.startswith('h'):
            # 标题标签：替换内部 br 为单空格
            for br in elem.find_all('br'):
                br.replace_with(' ')
            t = elem.get_text(" ").replace('\xa0', ' ')
            t = re.sub(r'[ \t\r\n]+', ' ', t).strip(' \t\r\n')
            if not t:
                continue
            # 若与本章标题相同，则不重复生成子标题
            if norm_title and re.sub(r'\s+', '', t) == norm_title:
                continue
            blocks.append(f"## {t}")

        elif elem.name == 'p':
            classes = elem.get('class', [])
            t = clean_paragraph_text(elem)
            if not t:
                # 空段落、纯空白段落整段删除
                continue

            # 若该 p 是用于样式的章节标题（如 class=pius1 且文字与章节标题一致），则不作为段落重复出现
            if classes and any(c in ['pius1', 'pius2', 'title'] for c in classes):
                if norm_title and re.sub(r'\s+', '', t) == norm_title:
                    continue

            blocks.append(t)

    return blocks


def classify_spine_item(
    name: str,
    text: str,
    imgs: List[Tag],
    soup: BeautifulSoup,
    ncx_title: str = ""
) -> Tuple[str, str, bool]:
    """
    根据文件内容对 spine 项目进行智能分类
    返回: (类别, 判别理由, 是否保留为正文)
    """
    stripped_text = text.strip(' \t\r\n')
    text_len = len(stripped_text)
    lower_name = name.lower()

    # 1. 插图页：body 内主要是一个或多个 <img>，几乎没有文本
    if len(imgs) > 0 and (text_len < 15 or (text_len < 50 and any(k in stripped_text for k in ["插画", "彩页", "illus", "cover"]))):
        return "插图页", f"主要包含 {len(imgs)} 张图片，文本仅 {text_len} 字", False

    if text_len == 0 and len(imgs) > 0:
        return "插图页", f"包含 {len(imgs)} 张图片，无正文文本", False

    # 2. 目录页：内容为 <a> 链接列表
    a_tags = soup.find_all('a')
    if len(a_tags) >= 3 and any(k in stripped_text.upper() for k in ["CONTENTS", "目录", "目次"]):
        return "目录页", f"包含 {len(a_tags)} 个目录导航链接", False

    # 3. 版权/元数据页：含 title/copyright/colophon/制作信息等
    meta_keywords = ["制作信息", "转载信息", "版权", "录入：", "扫图：", "译者：", "图源：", "仅供交流", "严禁商用", "staff"]
    if any(k in stripped_text for k in meta_keywords):
        return "版权/元数据", f"内容包含版权/出版元数据特征信息", False

    if ("title" in lower_name or "colophon" in lower_name) and text_len < 100:
        return "版权/元数据", f"书名与出版元数据页（字数 {text_len}）", False

    # 4. 简介页（Summary）
    if "summary" in lower_name or (text_len < 400 and stripped_text.startswith("简介")):
        return "版权/元数据", f"官方图书简介页（字数 {text_len}，非小说正文）", False

    # 5. 扉页：只有章节大标题，无正文段落
    h_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    p_tags = [p for p in soup.find_all('p') if p.get_text(strip=True)]
    if text_len < 40 and len(p_tags) <= 1:
        if any(term in stripped_text for term in ["章", "期", "篇", "卷"]):
            return "扉页", f"仅含部/卷/章大标题，无正文段落（字数 {text_len}）", False

    # 6. 题词/卷首引言（Quotation）
    if "quotation" in lower_name or ("──" in stripped_text and text_len < 150):
        return "扉页/题词", f"卷首题词与引言（字数 {text_len}）", False

    # 7. 后记：有实质文本，含"后记"、"あとがき"等
    if any(k in stripped_text[:200] for k in ["后记", "あとがき", "跋"]) or any(k in ncx_title for k in ["后记", "あとがき", "跋"]):
        return "后记", f"含后记特征词且有实质正文（字数 {text_len}）", True

    # 8. 正文：纯文本段落多，有实质内容
    if text_len >= 100:
        return "正文", f"有实质小说正文段落（字数 {text_len}）", True

    # 9. 判别存疑时：倾向保留（宁可多转，不可误删）
    if text_len > 0:
        return "正文(存疑保留)", f"字数较短({text_len}字)但有文字，遵循倾向保留原则", True

    return "空白/跳过", f"无实质内容（字数 0）", False


def parse_volume_number(filename: str) -> str:
    """从 epub 文件名中提取卷数，返回两位数字字符串如 '01'"""
    # 匹配文件名尾部的数字，如 " 01.epub", " 1.epub", "15.epub"
    match = re.search(r'(\d+)\s*\.epub$', filename, re.IGNORECASE)
    if match:
        return f"{int(match.group(1)):02d}"
    # 备用匹配任何数字
    digits = re.findall(r'\d+', filename)
    if digits:
        return f"{int(digits[-1]):02d}"
    return "01"


def process_single_epub(epub_path: str, output_base_dir: str) -> Dict:
    """
    处理单本 EPUB：
    1. 严格按 spine 顺序解析
    2. 智能分类与过滤
    3. 特殊情况（如跨文件同一章拆分）自动连贯拼接
    4. 输出 Markdown 章节与单卷 convert_log.md
    """
    fname = os.path.basename(epub_path)
    vol_num = parse_volume_number(fname)
    vol_out_dir = os.path.join(output_base_dir, vol_num)
    os.makedirs(vol_out_dir, exist_ok=True)

    book = epub.read_epub(epub_path)
    dc_titles = book.get_metadata('DC', 'title')
    book_title = dc_titles[0][0] if dc_titles else fname

    ncx_map = extract_ncx_map(book)
    spine_items = book.spine

    log_chapters = []
    log_skipped = []
    log_anomalies = []

    # 第一遍扫描：收集所有 spine 项目的基本信息与判别
    parsed_items = []
    for idx, (item_id, _) in enumerate(spine_items):
        item = book.get_item_with_id(item_id)
        if not item:
            log_anomalies.append(f"Spine 项 id={item_id} 在 EPUB 中找不到对应实体文件")
            continue

        raw_content = item.get_content()
        soup = BeautifulSoup(raw_content, 'html.parser')
        text = soup.get_text()
        imgs = soup.find_all('img')
        base_name = os.path.basename(item.get_name())

        ncx_title = ncx_map.get(base_name, "")
        cat, reason, is_content = classify_spine_item(base_name, text, imgs, soup, ncx_title)

        parsed_items.append({
            'idx': idx,
            'id': item_id,
            'base_name': base_name,
            'soup': soup,
            'raw_content': raw_content,
            'text_len': len(text.strip()),
            'ncx_title': ncx_title,
            'category': cat,
            'reason': reason,
            'is_content': is_content,
        })

    # 第二遍：处理章节与跨文件连贯合并（如第15卷由于日记插图导致同章正文被截成多个文件）
    # 策略：如果一个正文文件没有标题（无NCX且无HTML标题），且其所属基础编号与前一个正文一致（例如 Section001 与 Section001-6），
    # 或者紧随其后且属于同章续文，则合并到前一个章节中。
    grouped_chapters = []

    for item_info in parsed_items:
        if not item_info['is_content']:
            log_skipped.append({
                'filename': item_info['base_name'],
                'category': item_info['category'],
                'reason': item_info['reason'],
                'text_len': item_info['text_len']
            })
            continue

        base_name = item_info['base_name']
        ncx_t = item_info['ncx_title']
        fallback_t = extract_fallback_title(item_info['soup'])
        determined_title = ncx_t or fallback_t

        # 检查是否应该合并到上一章：
        # 条件：上一章存在，且当前文件无独立标题（ncx和h均无），且文件名体现同一章节前缀（如 Section001 与 Section001-6，Section002 与 Section002-3）
        should_merge = False
        if grouped_chapters and not determined_title:
            last_chap = grouped_chapters[-1]
            last_base = last_chap['items'][0]['base_name']
            # 提取前缀部分，例如 Section001-6 -> Section001
            curr_prefix = re.split(r'[-_]', os.path.splitext(base_name)[0])[0]
            last_prefix = re.split(r'[-_]', os.path.splitext(last_base)[0])[0]
            if curr_prefix == last_prefix:
                should_merge = True

        if should_merge:
            grouped_chapters[-1]['items'].append(item_info)
            msg = f"文件 {base_name} 判定为上一章（{grouped_chapters[-1]['title']}）的插图后续分段正文，已自动合并为同一章"
            grouped_chapters[-1]['merge_notes'].append(msg)
            log_anomalies.append(msg)
        else:
            if not determined_title:
                determined_title = f"chapter_{len(grouped_chapters) + 1:03d}"
                log_anomalies.append(f"文件 {base_name} 缺失 NCX 与正文标题，使用兜底标题：{determined_title}")
            elif not ncx_t:
                log_anomalies.append(f"文件 {base_name} NCX 缺失标题，降级使用正文标题：{determined_title}")

            grouped_chapters.append({
                'title': determined_title,
                'items': [item_info],
                'merge_notes': []
            })

    # 第三遍：生成 Markdown 文件并写入磁盘
    for chap_idx, chap in enumerate(grouped_chapters, start=1):
        title = chap['title']
        all_blocks = []
        source_files = []
        total_chars = 0

        for it in chap['items']:
            source_files.append(it['base_name'])
            blocks = clean_xhtml_body_to_markdown_blocks(it['raw_content'], chapter_title=title)
            all_blocks.extend(blocks)

            # 特殊处理：第15卷原版插图日记文本还原插入
            if vol_num == '15':
                if it['base_name'] == 'Section001.xhtml':
                    all_blocks.extend(VOL15_DIARY_TEXT_PART1)
                    chap['merge_notes'].append("【插图文字还原】已将日记插图第1~8页（魔石病、潜入米里斯、洛琪希之死、希露菲惨死）还原插入正文")
                elif it['base_name'] == 'Section002.xhtml':
                    all_blocks.extend(VOL15_DIARY_TEXT_PART2_A)
                    chap['merge_notes'].append("【插图文字还原】已将日记插图第9~12页（自动人偶、魔导铠构想）还原插入正文")
                elif it['base_name'] == 'Section002-3.xhtml':
                    all_blocks.extend(VOL15_DIARY_TEXT_PART2_B)
                    chap['merge_notes'].append("【插图文字还原】已将日记插图第13~20页（艾莉丝之死、六面世界真相、时空转移动机）还原插入正文")


        md_body = "\n\n".join(all_blocks)
        full_md = f"# {title}\n\n{md_body}\n" if md_body else f"# {title}\n"
        total_chars = len(re.sub(r'\s+', '', md_body))

        # 文件名：<章节数>_<章节标题>.md
        safe_title = sanitize_filename(title)
        out_filename = f"{chap_idx:02d}_{safe_title}.md"
        out_filepath = os.path.join(vol_out_dir, out_filename)

        with open(out_filepath, 'w', encoding='utf-8') as f:
            f.write(full_md)

        log_chapters.append({
            'num': f"{chap_idx:02d}",
            'filename': out_filename,
            'sources': ", ".join(source_files),
            'title': title,
            'char_count': total_chars,
            'notes': "; ".join(chap['merge_notes'])
        })

    # 生成单本 convert_log.md
    log_path = os.path.join(vol_out_dir, "convert_log.md")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"# 《{book_title}》转换日志\n\n")
        f.write(f"- **来源文件**：`{fname}`\n")
        f.write(f"- **卷数编号**：`{vol_num}`\n")
        f.write(f"- **总 Spine 文件数**：{len(spine_items)}\n")
        f.write(f"- **提取章节总数**：{len(log_chapters)}\n")
        f.write(f"- **跳过文件总数**：{len(log_skipped)}\n\n")

        f.write("## 章节列表\n\n")
        f.write("| 编号 | 输出文件名 | 来源 xhtml | 章节标题 | 正文字数 | 备注 |\n")
        f.write("|---|---|---|---|---|---|\n")
        for c in log_chapters:
            notes = c['notes'] if c['notes'] else "-"
            f.write(f"| {c['num']} | `{c['filename']}` | `{c['sources']}` | {c['title']} | {c['char_count']} | {notes} |\n")
        f.write("\n")

        f.write("## 跳过文件列表\n\n")
        f.write("| 文件名 | 判别类别 | 依据与原因 | 字数 |\n")
        f.write("|---|---|---|---|\n")
        for s in log_skipped:
            f.write(f"| `{s['filename']}` | **{s['category']}** | {s['reason']} | {s['text_len']} |\n")
        f.write("\n")

        f.write("## 异常与合并记录\n\n")
        if log_anomalies:
            for a in log_anomalies:
                f.write(f"- {a}\n")
        else:
            f.write("- 无异常记录\n")
        f.write("\n")

    return {
        'vol': vol_num,
        'title': book_title,
        'file': fname,
        'spine_count': len(spine_items),
        'chapter_count': len(log_chapters),
        'skipped_count': len(log_skipped),
        'anomalies_count': len(log_anomalies),
        'anomalies': log_anomalies
    }


def generate_global_summary(summary_records: List[Dict], output_base_dir: str):
    """生成总日志 _summary.md"""
    summary_path = os.path.join(output_base_dir, "_summary.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# EPUB 批量转换汇总报告 (_summary.md)\n\n")
        f.write(f"共处理书籍总数：**{len(summary_records)}** 本\n\n")
        f.write("## 各卷转换统计对比表\n\n")
        f.write("| 卷数 | 书籍名称 | Spine项数 | 转换章节数 | 跳过项数 | 状态/异常数 |\n")
        f.write("|---|---|---|---|---|---|\n")

        total_chaps = 0
        total_skips = 0

        for r in summary_records:
            total_chaps += r['chapter_count']
            total_skips += r['skipped_count']
            status = f"正常" if r['anomalies_count'] == 0 else f"需关注 ({r['anomalies_count']}条记录)"
            f.write(f"| {r['vol']} | {r['title']} | {r['spine_count']} | {r['chapter_count']} | {r['skipped_count']} | {status} |\n")

        f.write("\n")
        f.write(f"- **总提取章节数**：{total_chaps}\n")
        f.write(f"- **总跳过文件数**：{total_skips}\n\n")

        f.write("## 重点关注与人工复核项\n\n")
        has_issues = False
        for r in summary_records:
            if r['anomalies']:
                has_issues = True
                f.write(f"### 卷 {r['vol']}（{r['title']}）\n")
                for an in r['anomalies']:
                    f.write(f"- {an}\n")
                f.write("\n")

        if not has_issues:
            f.write("- 全卷转换完成，未发现需人工干预的异常项。\n")


def main():
    parser = argparse.ArgumentParser(description="批量将 EPUB 小说转为按章切分的 Markdown")
    parser.add_argument("input_dir", nargs="?", default="inputs/epubs", help="包含 epub 文件的输入目录 (默认: inputs/epubs)")
    parser.add_argument("output_dir", nargs="?", default="outputs/chapters", help="Markdown 章节输出目录 (默认: outputs/chapters)")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    # 路径自适应：如果 inputs/epubs 不存在，自动检测 inputs/eupbs
    if not os.path.exists(input_dir):
        alt_dirs = ["inputs/eupbs", "epubs", "inputs/epub"]
        for alt in alt_dirs:
            if os.path.exists(alt):
                print(f"[提示] 输入目录 `{input_dir}` 不存在，自动切换为找到的现有目录 `{alt}`")
                input_dir = alt
                break

    if not os.path.exists(input_dir):
        print(f"[错误] 未找到有效的输入目录：`{input_dir}`")
        sys.exit(1)

    epub_files = sorted(glob.glob(os.path.join(input_dir, "*.epub")))
    if not epub_files:
        print(f"[错误] 目录 `{input_dir}` 下没有找到任何 .epub 文件！")
        sys.exit(1)

    print(f"==================================================")
    print(f"开始批量转换 EPUB，找到 {len(epub_files)} 本图书")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"==================================================")

    os.makedirs(output_dir, exist_ok=True)
    summary_records = []

    for i, epub_file in enumerate(epub_files, start=1):
        fname = os.path.basename(epub_file)
        print(f"\n[{i}/{len(epub_files)}] 正在处理: {fname} ...")
        try:
            record = process_single_epub(epub_file, output_dir)
            summary_records.append(record)
            print(f"    ✓ 完成! 提取章节: {record['chapter_count']} 章, 跳过: {record['skipped_count']} 项, 异常/合并: {record['anomalies_count']}")
        except Exception as e:
            print(f"    ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n正在生成全书汇总报告 _summary.md ...")
    generate_global_summary(summary_records, output_dir)
    print(f"全部完成! 转换结果与日志已保存在: {output_dir}")


if __name__ == "__main__":
    main()
