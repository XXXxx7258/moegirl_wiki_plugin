# 萌娘百科知识补全插件

为 MaiBot / 麦麦提供一个 `moegirl_lookup` Tool，用于在聊天过程中查询萌娘百科词条、补充主词条信息，并附带相关语境条目。

仓库地址：<https://github.com/XXXxx7258/moegirl_wiki_plugin>

## 功能特性

- 基于萌娘百科 Action API 查询词条
- 优先使用 `generator=search`，失败时自动回退 `opensearch`
- 支持常见问句归一化
  - `初音未来是谁`
  - `东方Project是什么`
  - `博丽灵梦是哪个作品的`
- 当主词条足够可信时：
  - 返回主词条**详细结果**
  - 默认附带 2~4 个**相关语境**中等详细结果
- 当主词条不够可信时：
  - 返回多条中等详细候选结果
- 支持本地缓存与可选 Cookie 配置

---

## 目录结构

```text
moegirl_wiki_plugin/
├─ __init__.py
├─ _manifest.json
├─ client.py
├─ models.py
├─ plugin.py
├─ services/
│  └─ query_service.py
├─ README.md
├─ LICENSE
└─ .gitignore
```

---

## 安装方式

将本仓库克隆到 MaiBot 的 `plugins/` 目录下，例如：

```bash
cd /path/to/MaiBot/plugins
git clone https://github.com/XXXxx7258/moegirl_wiki_plugin.git
```

建议最终目录名保持为 `moegirl_wiki_plugin`。

---

## 配置说明

> **不要手动创建 `config.toml`。**
>
> 插件配置会由 MaiBot 根据 `config_schema` 自动生成。

首次加载插件后，会在插件目录下自动生成 `config.toml`，然后你再按需编辑。

### 最小配置

```toml
[plugin]
enabled = true
config_version = "1.0.0"

[network]
timeout_seconds = 10

[auth]
mode = "anonymous"
cookie_string = ""

[search]
prefer_generator_search = true

[cache]
ttl_seconds = 300

[result]
max_candidates = 5

[tool]
prefer_exact_title = true
```

### Cookie 配置（可选）

当前搜索主路径**不依赖 Cookie**，但你仍然可以保留登录态配置，方便后续扩展或站点策略变化时使用：

```toml
[auth]
mode = "cookie"
cookie_string = "完整 Cookie 头"
```

---

## Tool 说明

### Tool 名称

`moegirl_lookup`

### 输入参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `query` | `string` | 要查询的词条、关键词或自然语言问句 |
| `mode` | `string` | `summary` 或 `candidates` |
| `max_candidates` | `int` | 候选数量上限 |

### 输出策略

#### 1. 主词条足够可信

返回：

- 主词条详细结果
  - 标题
  - 完整简介
  - 链接
  - 分类
  - 缩略图
- 相关语境中等详细结果
  - 标题
  - 简短简介
  - 链接

#### 2. 主词条不够可信

返回：

- 多条中等详细候选结果
  - 标题
  - 简短简介
  - 链接

---

## 示例

### 示例 1：主词条 + 相关语境

输入：

```text
初音未来是谁
```

输出形态：

```text
词条：初音未来
简介：……
链接：……
分类：……
缩略图：……

相关语境：
1. 初音未来/现实事件
简介：……
链接：……
2. 初音未来 -歌姬计划-
简介：……
链接：……
```

### 示例 2：候选结果

输入：

```text
某个歧义较大的关键词
```

输出形态：

```text
未找到足够可信的主词条，以下词条可能相关：
1. 词条A
简介：……
链接：……
2. 词条B
简介：……
链接：……
```

---

## 开发与验证

如果你是在 **MaiBot 宿主工程** 中开发或联调本插件，请在 **MaiBot 工程根目录** 运行：

```bash
uv run python -m pytest tests/test_moegirl_tool_plugin.py -q
uv run ruff check plugins/moegirl_wiki_plugin tests/test_moegirl_tool_plugin.py
```

---

## License

MIT License. 详见 [LICENSE](./LICENSE)。
