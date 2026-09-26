# 通用模板 00：批量电子书预处理与按章切分清洗规约（EPUB / TXT Preprocessing Template）

> **使用说明**：将本文档复制到新项目，替换大括号内的变量（如 `{{PROJECT_NAME}}`）即可直接作为 Stage 00 的执行指令。

---

# 任务：批量将《{{PROJECT_NAME}}》原始电子书转为标准切分的纯净 Markdown 章节

## 一、配置参数

```yaml
项目设定:
  作品名称: "{{PROJECT_NAME}}"
  作者: "{{AUTHOR_NAME}}"
  输入电子书目录: "inputs/"
  输出章节目录: "outputs/chapters/"
  书籍文件格式: "EPUB (亦可适配 TXT/HTML)"
  预期总卷数/分册数: "{{TOTAL_VOLUMES}}"
```

## 二、输出规格

- **章节目录组织**：`outputs/chapters/{volume_id:02d}/`（如 `outputs/chapters/01/`）
- **章节文件名**：`{chapter_id:02d}_{chapter_title}.md`（如 `01_第一章_「启程」.md`）
- **日志文件**：
  - 各卷清洗日志：`outputs/chapters/{volume_id:02d}/convert_log.md`
  - 全局总览汇总：`outputs/chapters/_summary.md`

---

## 三、清洗与提取准则

1. **绝对顺序以 Spine 为准**：
   - 严禁按文件名字典序排序。必须解析 `content.opf` 的 `<spine>` 阅读流，严格按其声明顺序提取。
2. **三级标题提取策略**：
   - 优选 `toc.ncx` / `nav.xhtml` 中的目录导航文本。
   - 备选抓取正文中首个 `<h1>` 或 `<h2>` 标题。
   - 兜底使用 `chapter_{index:03d}`。
3. **页面智能分类过滤**：
   - **保留**：包含正文叙述段落的文件；实质性后记、番外、特稿。
   - **跳过**：纯插图页（仅含 `<img>`）、纯扉页/空标题页、目录页、版权/出厂信息页。
   - **日志透明**：被跳过的文件必须全数记入 `convert_log.md`，严禁静默丢弃。
4. **HTML 标签清洗标准**：
   - 移除所有 `<script>`, `<style>`, `<img>`, `<iframe>`。
   - `<ruby>` 标签清理：删除 `<rt>` 和 `<rp>` 及其内容，保留核心汉字。
   - 段落 `<p>` 映射为 Markdown 自然段，段落间以单个空行分隔。
   - 段落内和标题内的 `<br/>` 均替换为单个空格，避免单句割裂。
5. **标点与文本保真**：
   - 100% 保留中文/日文原始标点：`「」『』`、`……`、`——`、`？！`、全角空格 `　`。
   - 严禁擅自转为半角或修改字词，严禁插入任何未经原著授权的 AI 解释。

---

## 四、执行指令参考

```bash
# 运行切分工具脚本
python tools/convert_all.py inputs outputs/chapters
```

## 五、验收标准

- [ ] 各卷章节数与原著目录一致（无重大缺失或异常膨胀）。
- [ ] 输出的 `.md` 中无残留 HTML 标签。
- [ ] 对话引号成对完整。
- [ ] 生成完整的 `_summary.md` 质检日志。
