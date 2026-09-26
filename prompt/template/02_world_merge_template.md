# 通用模板 02：按时间线聚合分阶段防剧透世界书规约（Stage-Sliced Worldbook Merging Template）

> **使用说明**：将本文档复制到新项目，定义具体作品的时间线阶段表，即可作为 Stage 02 生成分阶段世界书的执行指令。

---

# 任务：按时间线聚合《{{PROJECT_NAME}}》设定草稿，构建分阶段防剧透 JSON 世界书

## 一、配置参数与阶段切片规划

```yaml
项目设定:
  作品名称: "{{PROJECT_NAME}}"
  输入目录: "outputs/world_raw/{volume_id}/*.md"
  输出目录: "world_stages/"
  
阶段切片矩阵:
  - 阶段标识: "shared_world"
    阶段名称: "跨阶段通用底座"
    覆盖范围: "全时期通用"
    收录重点: "不可变的宇宙观、底层力量法则、通用货币与地理框架"
  - 阶段标识: "stage1_{name}"
    阶段名称: "{{STAGE1_NAME}}"
    覆盖范围: "{{STAGE1_RANGE}}"
    剧情特征与防剧透边界: "{{STAGE1_BOUNDARIES}}"
  - 阶段标识: "stage2_{name}"
    阶段名称: "{{STAGE2_NAME}}"
    覆盖范围: "{{STAGE2_RANGE}}"
    剧情特征与防剧透边界: "{{STAGE2_BOUNDARIES}}"
  # 根据需要继续增加 stage3, stage4, stage5 等
```

---

## 二、四大聚合原则

### 1. 实体分阶段拆解（Stage Slicing）
- 坚决杜绝静态单一词条。同一角色、阵营、据点随时间变化的状态，必须独立生成属于各自阶段的条目。
- 保证挂载时采用“1 个通用底座 + 1 个当前阶段”模式，下游绝不串味。

### 2. 50~150 汉字高密度硬约束
- 每个条目的 `content` 核心设定必须严格控制在 **50~150 汉字**以内。
- 删去原著文学修饰、抒情比喻与冗长对话，只保留百科级的事实陈述（机制、来历、弱点、功能、关系）。

### 3. 双条目反转隔离机制（Dual-Entry Anti-Spoiler）
- 对剧情中存在惊天反转或欺骗的设定：
  - **条目一（表面认知）**：`spoiler: false`，记录早期的伪装或常识。
  - **条目二（真实内幕）**：`spoiler: true`，标明 `reveal_arc`（如 `"第X卷反转后"`），并在 `note` 中警示未触发时禁止加载。

### 4. 触发词穷举（Keywords Saturation）
- 必须穷举：官方全称、常用简称、别号、诨名、黑话代称、重要同伴专属称呼。

---

## 三、世界书条目 JSON 标准 Schema

```json
[
  {
    "keywords": ["实体标准名", "别名1", "简称", "专属称呼"],
    "content": "客观事实描述，字数严格在50-150汉字以内。阐述其在当前阶段的核心机制、地位、状态与关键约束。",
    "timeline": "stage1_name",
    "priority": "核心",
    "category": "力量体系",
    "reveal_arc": "",
    "spoiler": false,
    "source_chapters": ["001_01", "002_03"],
    "note": "仅限当前阶段生效，严禁剧透后续反转"
  }
]
```

### 字段说明表

| 字段 | 类型 | 规范与取值 |
|:---|:---:|:---|
| `keywords` | Array[String] | 触发关键词列表，至少 2~5 个以上，穷举所有可能出现的代称。 |
| `content` | String | 设定本体，**严格校验在 50~150 汉字之间**。 |
| `timeline` | String | 所属阶段文件名标识（如 `shared_world`、`stage1_xxx`）。 |
| `priority` | String | `核心`（主线强相关、高频触发）或 `次要`（背景补充、小众细节）。 |
| `category` | String | 分类：`地理`、`组织`、`力量体系`、`种族`、`物品`、`历史`、`社会规则`、`角色`。 |
| `reveal_arc` | String | 反转揭露时机。若无反转留空，若有写明具体卷数/章节。 |
| `spoiler` | Boolean | `false` 表示当期公开认知；`true` 表示涉及核心剧透的深层内幕。 |
| `source_chapters` | Array[String] | 依据来源章节号列表。 |
| `note` | String | 阶段挂载注意事项与防穿帮提示。 |

---

## 四、辅助质检与构建脚本要求

建议编写配套校验工具（如 `tools/build_final_stages.py`）进行自动化拦截：
1. 正则或代码遍历 JSON 数组，校验 `50 <= len(item["content"]) <= 150`。
2. 校验各阶段条目数量（通用底座建议 20~30 条，各阶段专属建议 15~40 条）。
3. 自动化导出与条目 100% 对应的 Markdown 索引总览文档（`world_stages/world_summary.md`）。
