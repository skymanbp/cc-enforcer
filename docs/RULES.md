# Rule Catalog（规则目录）

> 索引版本。每条规则的**完整正文**位于 [`../rules/`](../rules/)（英文骨架）与
> [`../rules/zh/`](../rules/zh/)（中文翻译）；本文档只做摘要、severity、执行方式
> 与关联组件指引。英文索引是 [`../rules/00-index.md`](../rules/00-index.md)。
>
> 修改任意一条规则时，请按 [`ARCHITECTURE.md`](./ARCHITECTURE.md) §8 的连带表
> 同步检查所有相关文件。

## 语言

- **English（骨架 / source of truth）** — [`../rules/`](../rules/) 根层。钩子注入
  默认英文（`prompts/` 根层）；其它任何层的规则语义都以英文骨架为准。命令 /
  skill 的**正文**用中文书写，但它们引用的规则**定义**以英文骨架为准。
- **中文翻译** — [`../rules/zh/`](../rules/zh/)，逐文件、逐标题跟随英文骨架；
  出现 drift 以英文为准（CI 硬门 [`i18n_check.py`](../hooks/scripts/i18n_check.py)，
  见 [`I18N.md`](./I18N.md)）。运行时 `CC_ENFORCER_LANG=zh` 切换注入语言；新语言放
  `rules/<code>/` + `prompts/<code>/`，缺失文件自动回退英文。

## 规则一览

编号格式 `<两位数>-<kebab-case>.md`；编号一旦发布不再回收；当前区间 `01–12`，
全部为 **must**（`should` / `info` 两级预留，暂无规则使用）。

| ID | 标题 | 适用场景 | 物理执行 |
|---:|------|----------|----------|
| 01 | [验证而非猜测](../rules/01-verify-dont-guess.md) | 任何关于文件、API、版本、文献、报错的断言 | Stop layer (b)（完成声明旁的第一人称含糊词）、layer (g)（"我改了 X"与磁盘 mtime 矛盾） |
| 02 | [系统式而非反应式](../rules/02-systematic-not-reactive.md) | 修 bug、改架构、重构、加功能前的七问 | 文本层纪律；Stop layer (e) 用其关键词间接评分 |
| 03 | [修根因，不修症状](../rules/03-root-cause.md) | 异常处理、测试 / CI 失败、竞态、钩子失败；上游溯源阶梯 | `PreToolUse(Bash)` DENY（绕过模式与破坏性命令） |
| 04 | [完整阅读，拒绝关键词依赖](../rules/04-full-context.md) | 编辑前、跨文件影响分析 | `PreToolUse(Edit\|Write)` DENY（本会话未 Read 的已存在文件） |
| 05 | [引用必须可追溯](../rules/05-cite-sources.md) | 任何对外陈述（PR、回复、报告） | 文本层纪律；`verifier` 子代理事后核验 |
| 06 | [验证收敛](../rules/06-verify-convergence.md) | 任何修复 / 更新完成后的收敛验证 | Stop layer (a)（无证据）、layer (c)（缺四问自答） |
| 07 | [任务忠实](../rules/07-task-fidelity.md) | 声称完成前对照原始请求逐项核对 | Stop layer (d) |
| 08 | [改前必读，写前必想](../rules/08-read-before-edit-think-before-write.md) | 任何 `Edit` / `Write` 前的前置纪律 | `PreToolUse(Edit\|Write)` DENY（未读即改）+ Stop layer (e) |
| 09 | [系统式修改，禁止打补丁](../rules/09-systematic-modification.md) | 修改内容的姿势：屏蔽标记、滚动补丁、统一修复 | `PreToolUse(Edit\|Write)` DENY（无 why 的屏蔽标记；同文件第 4 次小改）+ Stop layer (f) |
| 10 | [禁止非必须硬编码](../rules/10-no-hardcoding.md) | 把本应是配置 / 环境的密钥凭证内联成代码字面量 | `PreToolUse(Edit\|Write)` DENY（仅代码目标；散文文档与锁文件豁免） |
| 11 | [禁止非必须路径依赖](../rules/11-no-path-dependency.md) | 把机器特定的 user-home 绝对路径写死进代码 | `PreToolUse(Edit\|Write)` DENY（同上） |
| 12 | [全库同步](../rules/12-repo-wide-sync.md) | 修改收尾的全库引用清扫；按需全库陈旧扫描 | Stop layer (i)（项目级 `.claude/cc-enforcer/sync-gate.toml`，按项目选择启用）+ `repo-refresh` skill |

Stop 各层的判定顺序、标记集合与宽限语义见 [`ARCHITECTURE.md`](./ARCHITECTURE.md) §2.5。

## 规则之间的关系

- **01 / 04 / 05** 是**输入端**约束：agent 如何获取与陈述事实。
- **02** 是**思考过程**约束：如何把事实组织成方案。
- **08** 把 04 + 02 折叠成 `Edit` / `Write` 之前的最低必答清单，并由 PreToolUse +
  Stop layer (e) 物理强制。
- **03** 是**输出端（改什么）**约束：是否触达根因——沿因果链上溯到机制 /
  设计决策 / 缺失不变量为止，停在中途必须显式说明。
- **09** 是**输出端（怎么改）**约束：修改内容不得打补丁；确诊的根因定义一个"类"，
  全库同类实例一次修完。**10 / 11** 是同一写入时内容检测家族里的**内容值**
  约束（09 拦姿势，10 / 11 拦塞进去的值），三者共用 why 注释逃生舱把"非必须"
  落地为可验证判定；10 / 11 没有 Stop 层，避免对已被拦截的写入双重追责。
- **06** 是**输出端（改完之后 · 技术面）**约束：根因是否真的解决到收敛。
- **07** 是**输出端（改完之后 · 契约面）**约束：用户要求的是否**全部**按**原标准**
  交付。06 解决"症状-根因"轴，07 解决"请求-交付"轴。
- **12** 是**输出端（仓库引用图轴）**约束：06 收敛被改的部分，07 覆盖用户要的部分，
  12 让仓库其余部分跟着走——文档 / 下游 / 测试 / 翻译连带更新或显式核对。

## 各组件如何引用这些规则

| 组件 | 引用方式 |
|------|---------|
| [`prompts/session-start.md`](../prompts/session-start.md) | 权威合约：12 条规则各一行、物理强制层表、YAML 回复 schema；会话启动与每次压缩后注入 |
| [`prompts/user-prompt.md`](../prompts/user-prompt.md) | 每轮短提醒：全部硬门、Stop 九层、schema 字段名 |
| [`commands/checklist.md`](../commands/checklist.md) | 八节可勾选清单（A 改前 / B 改后 / C 收敛 / D 忠实 / E 改前必读·写前必想 / F 系统式修改 / G TL;DR / H 全库同步）；规则 10 / 11 是纯内容层 DENY，无可自证项 |
| [`agents/verifier.md`](../agents/verifier.md) | 规则 05 + 01 的事后核验；只读 |
| [`skills/systematic-debug/SKILL.md`](../skills/systematic-debug/SKILL.md) | 规则 02 + 03 + 06 + 08 + 09 |
| [`skills/repo-refresh/SKILL.md`](../skills/repo-refresh/SKILL.md) | 规则 12 主动半区：全库陈旧 / 过时 / 冗余 / 错误 / 漂移扫描 |
| [`hooks/scripts/read_guard.py`](../hooks/scripts/read_guard.py) | 规则 04 + 08（改前必读）、09（屏蔽标记 + 滚动补丁频率）、10 + 11（内容值检测）、12（`edited_files` 记录） |
| [`hooks/scripts/bash_guard.py`](../hooks/scripts/bash_guard.py) | 规则 03（绕过模式拦截）+ 圣旨 + `register_read` 逃生口 |
| [`hooks/scripts/stop_guard.py`](../hooks/scripts/stop_guard.py) | 九层：(a)(c) 06 · (b) 01 · (d) 07 · (e) 08 · (f) 09 · (g) 01+06 · (h) TL;DR 收尾约定 · (i) 12 |
| [`hooks/scripts/lib/`](../hooks/scripts/lib/) | 判定模型（`srclex` / `mdctx` / `shellcmd` / `editscale`）、状态、配置读取、消息目录、语言解析——一处定义、多处消费，见 ARCHITECTURE §2.6 |

## 添加新规则

1. 在 [`../rules/`](../rules/) 下创建 `13-xxx.md`，带 YAML frontmatter（`id` /
   `title` / `severity`，参考任意现有规则）；在 [`../rules/zh/`](../rules/zh/) 下
   创建同名翻译，标题层级一致。
2. 按 [`ARCHITECTURE.md`](./ARCHITECTURE.md) §8 的 `rules/<nn>-*.md` 行同步：
   两份索引（`rules/00-index.md` + zh）、两层注入提示词（en + zh）、本文档的
   规则表、`commands/checklist.md`、`tests/test_inject_context.py`；视情况增加
   物理强制层（`hooks/scripts/` + `tests/`）。
3. 在 [`../CHANGELOG.md`](../CHANGELOG.md) 的 `[Unreleased]` 段记录。
