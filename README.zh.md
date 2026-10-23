# guideforge

**LLM 说它验收了 ≠ 验收了。**

让 DeepSeek 给每个景点抓 3 张候选封面图、人工 3 选 1。它声称完成了——实际上随手用了搜到的第一张。对质后它承认撒谎。换一个全新对话去审计，审计结论是：它又骗了你，只是方向相反。

这不是某个模型不行，是架构问题：**生成器不能当自己的裁判。** 当"验收"存在于模型自己的话里，它就不存在。

guideforge 是一条旅游攻略生产流水线，每一步都由**代码**验收，而不是由模型的口头汇报验收：

```
LLM 在外面生成                  guideforge 在里面验收
──────────────────             ─────────────────────────
景点清单           ──►   id 唯一、slug 合法、查重            ✔
分档               ──►   schema、每条目唯一归属              ✔
文案               ──►   字段、字数、占位符                  ✔
攻略 HTML          ──►   inline-style 规则、引用受管         ✔
候选图片           ──►   下载、尺寸、比例、去重              ✔
人工挑选（human gate）──►  picked ∈ candidates               ✔
                              全绿 ──► dist/ 发布包
```

## 安装

```bash
pip install guideforge
```

Python 3.9+，依赖仅 `requests`、`Pillow`、`PyYAML`。

## 快速开始

```bash
guide init my-trip
cd my-trip
```

1. **改 `spec.yaml`** —— 档位定义、文案规范、图片标准。这是宪法：工具执行你的规则，不是它自己的。
2. **按 `prompts/*.md` 逐阶段喂给任意 LLM**（Claude / GPT / DeepSeek / GLM 都行——guideforge 不调用任何模型）。每个 prompt 产出一个 JSON artifact，按指示存盘。
3. **过闸门：**

```bash
guide check                        # 阶段 1-4，任何失败 exit 1
guide images --source wikimedia    # 或 --source urls（LLM 给的候选 URL）
guide pick <id> <n>                # 看 sheets/<id>.jpg 后，通过工具写入挑选
guide finalize                     # 全绿 → dist/
```

完整可跑的示例在 [`examples/london/`](examples/london/)。

## 为什么 LLM 在工具外面

两个刻意的设计：

- **guideforge 永远不调用模型。** 你用今天信任的任何模型生成产物，工具只审判落在磁盘上的东西。于是验收是**证据**，不是**证词**；工具也永远不受 API key、费用、框架换代影响。
- **品味留给人。** 哪张图好看、分档是否得体、文案是否动人——这些是 human gate，明确标出。工具不假装能审美，模型也不被要求假装执行过。

## 命令

| 命令 | 作用 |
|---|---|
| `guide init <dir>` | 脚手架：`spec.yaml` + `prompts/` + `.gitignore` |
| `guide check [stages…]` | 机械验收，默认 `attractions tiers descriptions html` |
| `guide images [--source wikimedia\|urls] [--only <id>]` | 抓候选 + 机械校验（最小宽度、比例区间、格式、MD5 + 感知去重）+ 编号对比图；`--only` 单点重抓 |
| `guide pick [<id> <n>]` | 带参：通过工具写入挑选（范围校验）；不带参：校验挑选完整性 |
| `guide finalize` | 总闸门 → `dist/`（guide.html + 定稿图 + checklist.md） |

## 各阶段到底验了什么

| 阶段 | 产物 | 机械校验 |
|---|---|---|
| attractions | `attractions.json` | JSON 合法、id 唯一、slug 格式、重名 |
| coverage | `reference.json` 或 Wikidata | **穷举终止判据**：外部参照 top-N（Wikidata 按知名度排序，或你手工维护的 `reference.json`）必须全部出现在列表中；饱和判据——第二轮独立穷举（`attractions.pass2.json`）新增为零。缺漏/未收敛 → FAIL |
| tiers | `tiers.json` | 档位齐全、每条目恰好在某一档、无未知 id |
| descriptions | `descriptions.json` | 每条目齐全、必填字段、字数区间、禁用/占位符模式（忽略大小写、递归扫描） |
| html | `guide.html` | 无 `<style>`/外链样式/class-id、`<title>` 存在、`<img src>` 只能是外链或受管的 `images/<id>.jpg` |
| images | `images/manifest.json` | 候选文件存在且抓取时通过了下载与校验 |
| picks | `images/manifest.json` | `picked` 已填、是整数、在候选范围内 |

机器**不**验的：事实准确性、审美。这些需要人——本 README 不撒谎。

### 穷举怎么确定结束？

一张列表永远无法自证穷举了一座城——所以 guideforge 把"结束"从愿望变成可判定条件。在 `spec.yaml` 里配置 `coverage.city_qid`（伦敦是 `Q84`），然后：

- **覆盖率**：Wikidata top-N 景点（或你手工维护的 `reference.json`）必须全部出现，缺谁 FAIL 报谁的名字；
- **饱和度**：换个新对话再穷举一轮存成 `attractions.pass2.json`，只要某轮还有新增就 FAIL，第一轮"零新增"出现时报告 `saturated`——穷举结束。

## 与编码 agent 配合（pi / Claude Code / opencode ...）

整套工作流以可安装的 agent skill 发行——把
[`skills/guideforge/SKILL.md`](skills/guideforge/SKILL.md) 复制进你 agent 的技能目录（如 `~/.agents/skills/guideforge/`），以后任何"帮我做 XX 攻略"的任务都会自动触发完整流水线。[AGENTS.md](AGENTS.md) 是同一契约在本仓库内的形态。

guideforge 永远不调用模型——但模型正是流水线里那个预期的**工人**，而你现在多半就是通过一个 agent在读这段话。简版：

- **阶段 1–4 由 agent 执行**：按 `prompts/*.md` 生成产物、落盘、跑 `guide check <stage>`，修到 exit 0；
- **看图是提案**：agent 看九宫格，毙掉主体错误的候选（塔桥 ≠ 伦敦塔；"St Paul's" 四大洲都有），改 `query` 字段、`--only` 重抓，然后用 `guide pick <id> <n>` 记录挑选——必须走工具，让范围校验兜底；
- **机器给所有人打分**。agent 的总结陈词是证词，退出码才是证据；`guide finalize` 重跑全部检查，包括 agent 自己生成的阶段。生成者不能当自己的裁判——这条规则对填流水线的 agent 和对聊天窗口里的模型一视同仁。

在 30 景点、真实抓取的参考跑批中，loop 里的 agent 漏挑了 30 选 2、提错了 4 张主体错误的图——全部被闸门拦下。这就是系统在工作。

## 设计原则

1. 生成与验收是两份工作，永远不要让同一个进程既当运动员又当裁判。
2. 验收必须产出证据（文件、退出码），而不是声明。
3. 宪法（`spec.yaml`）归人所有，工具只负责执行。
4. 小到一个下午能读完：约 800 行 Python，3 个依赖。

## 开发

```bash
pip install -e . pytest ruff
pytest              # 单元 + 离线 e2e（伦敦示例跑在本地图片服务器上）
ruff check guideforge tests

GUIDEFORGE_LIVE=1 pytest -q -m network   # 可选：真实 Wikimedia Commons
```

结构：

```
tests/
├── conftest.py               # 共享的项目构造 fixture
├── unit/                     # 每条校验规则、每种失败模式各一个测试
└── e2e/
    ├── helpers.py            # 确定性 JPEG 生成器 + 本地图片服务器
    ├── test_urls_flow.py     # urls → 抓取 → 校验 → 去重 → 挑选 → 定稿
    ├── test_london_example.py# examples/london 端到端
    └── test_live_wikimedia.py# 真实网络，opt-in，被墙时自动跳过
```

## License

MIT
