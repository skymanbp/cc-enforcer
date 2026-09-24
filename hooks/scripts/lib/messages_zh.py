"""中文消息目录 —— `messages_en.py` 的翻译，不是它的替代。

英文骨架是唯一事实源（docs/I18N.md）；本文件按同一套键提供中文文案，由
`messages.py` 在 `CC_ENFORCER_LANG=zh` 时**逐键**覆盖。少写一个键不会让
守卫吐空消息，只会让那一条回落成英文。

翻译时的两条硬约束：

1. **占位符原样保留。** `{file_path}` / `{cap}` / `{snippet}` 之类是
   `str.format` 字段：漏掉一个，守卫就少告诉用户一件事；多写一个，格式化会
   在钩子里、在用户面前抛异常。`i18n_check.py` 逐键比对占位符集合。

2. **提到的标记必须中文侧真的能匹配。** 检测器的模式集本来就中英双收
   （`CONVERGENCE_MARKERS` / `FIDELITY_MARKERS` / `RULE_08_MARKERS` /
   `RULE_09_MARKERS` / `TLDR_MARKERS` / `SYNC_MARKERS` …），所以中文版点
   `自答` / `收敛` / `大白话` / `同步核对` 与英文版点 `self-quiz` /
   `convergence` / `tldr` / `sync-check` 同样属实。**不要**凭好听翻译出一个
   检测器不认的词——那正是 v0.35.1 修过的「文档宣传了一个不存在的检测器」。
"""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---- stop_guard ------------------------------------------------------
    'stop.recovery.a': """你的回复声称完成，却没有任何收敛证据：没有 `$ ` 命令提示行、
没有测试计数（`Ran N tests` / `N passed`）、没有围栏输出块、也没有
`重触发` / `边界用例` / `反向用例` / `verified` / `re-ran` 这类验证陈述。

按 rule 06（rules/06-verify-convergence.md），贴出最初失败的那条命令和它
现在通过的输出，或一次带计数的 `pytest` / `unittest` / `npm test` 运行。
如果你在心里验过、只是没写下来，那就现在写下来 —— 具体的命令和输出。""",
    'stop.tldr.a': '你说做完了但没贴证据——补一段「命令 + 输出」就放行。',
    'stop.fail_note.a': '缺收敛证据',
    'stop.layer_label.a': 'rule 06 —— 无证据',
    'stop.layer_keyword.a': 'rule 06',
    'stop.recovery.b': """你的回复把完成声明和含糊措辞放在了 50 字符以内。
按 rule 01（rules/01-verify-dont-guess.md），有把握的验证不可能与
「我觉得 / 我相信 / 应该是 / 大概 / 可能就」这类词共存于同一句断言旁。

二选一：
  • 删掉含糊词，用具体输出把结果说死，或
  • 删掉完成声明，明说「尚未确认」，让用户自己决定要不要发。

含糊词不是修辞客套 —— 它表示你自己也没底。有底就写清楚；没底就直说。""",
    'stop.tldr.b': '你一边说修好了一边又「应该 / 可能」——删掉含糊词，或明说还没验。',
    'stop.fail_note.b': '完成声明旁有含糊词',
    'stop.layer_label.b': 'rule 01 —— 完成声明旁的含糊词',
    'stop.layer_keyword.b': 'rule 01 + hedge',
    'stop.recovery.c': """你的回复有证据，但没有把 rule 06 的自答摆出来。
通过条件二选一：

  (a) 一个明确标记 —— `rule 06`、`自答`、`收敛`、`重触发`、
      `边界用例`、`反向用例`；或
  (b) 四道自答题里答出 ≥ 2 道：
        1. 真解决了吗？  要具体证据，不是「没报错」
        2. 有更好方案吗？  与备选方案比过
        3. 哪些没验？  明确列出没测到的部分
        4. 验证合理吗？  验的是根因链条，还是只碰到症状？

光是测试通过不等于收敛。现在就把自答写出来。""",
    'stop.tldr.c': '有证据但没答收敛 4 题——把「真解决 / 更好方案 / 哪些没验 / 验证合理」写出来。',
    'stop.fail_note.c': '缺自答 / 缺标记',
    'stop.layer_label.c': 'rule 06 —— 缺自答',
    'stop.layer_keyword.c': 'rule 06 self-quiz',
    'stop.recovery.d': """你改动的那部分通过了 rule 06 的收敛，但回复里没有
呈现 rule 07 的任务忠实 —— 那是另一根轴：「用户要的我是不是**全部**交付了、
是不是按他要求的**标准**交付的？」

通过条件二选一：
  (a) 一个明确标记 —— `rule 07`、`任务忠实`、`请求覆盖`、
      `原始请求`、`无降级`、`无遗漏`、`未超范围`；或
  (b) 三道忠实题里答出 ≥ 2 道：
        1. 覆盖性 —— 把原始请求拆成子项，逐项列出做了哪些、
           没做哪些、为什么
        2. 标准性 —— 用户用过的每个程度词（强制 / 必须 / 完整 /
           严格 / 所有）是落地成了硬动作，还是停在一行软文档？
        3. 忠实性 —— 有没有偷换概念、范围溢出、裁剪要求、藏 TODO？

去重读用户**最初**那条消息，而不是你中途复述的版本。""",
    'stop.tldr.d': '没回看用户原始请求——逐项列「做了哪些 / 有没有降级或遗漏」。',
    'stop.fail_note.d': '缺忠实标记 / 缺自答',
    'stop.layer_label.d': 'rule 07 —— 缺任务忠实',
    'stop.layer_keyword.d': 'rule 07 fidelity',
    'stop.recovery.e': """你这一轮改了文件，但回复里没有呈现 rule 08
（改前必读 / 写前必想）的收尾标记。

通过条件二选一：
  (a) 一个明确标记 —— `rule 08`、`改前必读`、`写前必想`、
      `系统式自答`；或
  (b) 六个 rule 02 关键词里出现 ≥ 3 个：
        架构
        职责
        根源 / 根因
        方案
        连带 / 影响
        风险 / 不变量

如果 rule 08 的功课你在思维链里做了、只是没写进最终回复 —— 现在写出来。
钩子读的是回复，不是隐藏的推理。""",
    'stop.tldr.e': '改了文件但没写「改前必读 / 写前必想」——补「根因 / 架构 / 方案」≥ 3 项。',
    'stop.fail_note.e': '缺 rule 08 标记 / 关键词不足 3 个',
    'stop.layer_label.e': 'rule 08 —— 改前必读 / 写前必想',
    'stop.layer_keyword.e': 'rule 08',
    'stop.recovery.f': """你这一轮改了文件，但回复里没有呈现 rule 09
系统式修改的三件套（根因 + 影响 + 方案）。

通过条件二选一：
  (a) 一个明确标记 —— `rule 09`、`系统式修改`、`打补丁`、
      `反补丁`；或
  (b) 三件套关键词在同一条回复里**全部**出现：
        • 根源 / 根因
        • 连带 / 影响范围
        • 方案

如果这次改动确实是打补丁式的（一处局部屏蔽、没做影响分析、没比过
备选方案），要么重做成系统式的，要么把这个半成品明确告诉用户。""",
    'stop.tldr.f': '改了文件但缺「根因 + 影响 + 方案」三件套——补全再收尾。',
    'stop.fail_note.f': '缺 rule 09 标记 / 三件套不全',
    'stop.layer_label.f': 'rule 09 —— 系统式修改三件套',
    'stop.layer_keyword.f': 'rule 09',
    'stop.recovery.g': """你的回复声称编辑 / 创建 / 修改了文件，但磁盘上的状态与其中
至少一条声明矛盾：

{contradictions}

按 rule 01（验证，不猜测）+ rule 06（收敛验证），关于**你自己做过什么**的
断言必须为真。如果你说「我改了 X.py」而 X.py 的 mtime 仍与本会话你第一次
看到它时一致，那么那次 Edit 要么被另一个钩子拒绝了（往回翻 transcript），
要么落在了别的文件上，要么没有产生净变化。重试那次编辑、改对路径、或撤回
这句声明。

本层只在**矛盾**时触发：没有基线的文件（你从未 Read 过）不核验，改了却忘了
提也不算错。如果你确实通过别的工具改过它，说出来，让用户决定。""",
    'stop.tldr.g': '你说改了某文件但磁盘没变——要么真去改，要么撤回这句声明。',
    'stop.fail_note.g': '文件改动声明与磁盘状态矛盾',
    'stop.layer_label.g': 'rule 01+06 —— 文件声明核验',
    'stop.layer_keyword.g': 'rule 01 + 06 file-claim',
    'stop.recovery.h': """你的回复声称完成，但结尾没有一句大白话总结。

按标准回复 schema，每条含完成声明的回复都必须以一句用户扫一眼就能懂的话
收尾。补上下列之一：

  • schema 的最后一个字段：  tldr: "<一句大白话>"
  • 一行以 `大白话:` / `一句话总结:` / `tldr:` 开头的句子

这句话要用大白话说清：你到底做了什么、结果如何、用户接下来要不要做点
什么。不是把规则检查复述一遍 —— 是给人看的结论。

例子：
  tldr: "改完了 Stop hook 加了 tldr 强制层，203 个测试全绿，可以直接 ship。"
""",
    'stop.tldr.h': '结尾少了一句大白话——加一行 tldr: "..." 就放行。',
    'stop.fail_note.h': '缺 tldr / 大白话',
    'stop.layer_label.h': 'TL;DR —— 缺大白话总结',
    'stop.layer_keyword.h': 'TL;DR 大白话',
    'stop.recovery.i': """本项目的连带组（.claude/cc-enforcer/sync-gate.toml）
里，有一组或多组对本会话的改动未被满足：

{violations}

按 rule 12（rules/12-repo-wide-sync.md），改动一个已登记下游 / 引用兄弟
文件的文件时，必须二选一：

  (1) 在同一会话内，至少编辑一个命中该组 `require` glob 的文件
      （把依赖你这次改动的引用、文档、测试、翻译一起更新），或
  (2) 在回复里用同步标记显式核对 —— 例如写一行：
        同步核对: <require 侧为什么无需变更>

只改 `when` 一侧却不吭声，正是 rule 12 要终结的那种「引用陈旧」偷懒。
现在逐条处理上面列出的组：要么把连带文件改了，要么把「它们为什么已经
是对的」说出来。""",
    'stop.tldr.i': '改了 A 类文件但没动它的连带 B 类——要么一起改，要么写一行「同步核对: 为什么不用改」。',
    'stop.fail_note.i': '连带组未满足',
    'stop.layer_label.i': 'rule 12 —— 全库同步门',
    'stop.layer_keyword.i': 'rule 12 sync-gate',
    'stop.recovery.h_long': """你的回复有 TL;DR，但其中至少有一条太长了，已经不像一句话：

  该条（{length} 列 > 上限 {cap}）：{snippet!r}

每条 tldr 是**一句话** —— 前因、做了什么、结果如何 —— 不超过 {cap} 个显示列。
单位是列不是字符：每个 ASCII 字符算 1 列，每个汉字算 2 列（所以约
{cjk_cap} 个汉字），组合符算 0，上面报的那个数就是列数。有好几件事要报，
就一行一件，每行一句短话、各自不超上限：

  tldr:
    - "修了 X：根因是 A，现在测试全绿。"
    - "顺带把 B 的引用同步了，无行为变化。"

该删的是过程细节，不是结果 —— 过程细节回复正文里已经有了。只超一点点的，
通常是两句话被一个逗号或顿号连成了一条：拆成两条。""",
    'stop.one_shot_footer': '（宽限按层计：这一层在当前恢复序列里不会再拦，但其它仍然不过的层照拦。修 FAIL 行点名的那一项；下一次放行的 Stop 会重置序列。）',
    'stop.headline': 'cc-enforcer · Stop 检查在 Layer {layer} 未通过 [{label}]',
    'stop.table_header': '| 层 | 规则 | 状态 | 说明 |\n|------|------|------|------|',
    'stop.status.pass': '✅ 通过',
    'stop.status.fail': '❌ **未过**',
    'stop.status.pending': '⏸  待评',
    'stop.status.na': '—  不适用',
    'stop.note.non_edit_turn': '（非编辑轮）',
    'stop.note.not_evaluated': '（未求值）',
    'stop.matched_prefix': '命中的完成声明',
    'stop.recovery_header': '[恢复指引 —— {keyword}]',
    'stop.tldr_prefix': '大白话',
    # ---- read_guard ------------------------------------------------------
    'read.deny.unread': """cc-enforcer · rule 04 + 08 违规（改前必读）

工具：{tool_name}
目标：{file_path}

这个文件已经在磁盘上存在，但本会话从未 Read（或 Write）过它。按 rule 04
（rules/04-full-context.md）+ rule 08
（rules/08-read-before-edit-think-before-write.md），编辑之前必须完整读过
目标文件，这样你才知道它周围的架构和下游影响。

继续的方式：对这个文件调用 Read（读**整个**文件，不只是 diff 上下文），
然后重试 {tool_name}。

如果你本会话**确实** Read 过它、闸门却仍然拒绝（Claude Code 偶尔会把 Read
短路到结果缓存而不触发钩子），可以把文件登记为已读 —— **必须拆成两次独立
的 Bash 调用**；任何串联形式（`&&`、`||`、`;`、管道、命令替换）都拿不到
额度，而脚本照样会打印 "register_read: ok"。

  第 1 次 Bash 调用 —— 算出文件当前在磁盘上的 SHA-256：
  python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' PATH

  第 2 次 Bash 调用 —— 登记，前后不许串接任何东西（HEX = 第 1 步打印的摘要）：
  python "${{CLAUDE_PLUGIN_ROOT}}/hooks/scripts/register_read.py" --file PATH --hash HEX

Bash 钩子会重新从磁盘算一遍哈希，一致才登记，所以这个逃生口本身没法用来
绕过「必读」。
""",
    'read.deny.patch': """cc-enforcer · rule 09 违规（补丁式 new_string）

工具：{tool_name}
目标：{file_path}
命中模式：{pattern_label}

片段（你 new_string 里出问题的那一段）：
{snippet}

按 rule 09（rules/09-systematic-modification.md），你要提交的这次修改里
含有一个「补丁标记」—— 它把类型 / lint / 测试 / 错误处理的信号**在没有
说明理由的情况下**静音了。

允许的写法要求同一行或紧邻一行有一条 why 注释，包含下列之一：
`因为`、`原因`、`why`、`正当`、`because`，或一个具体的正当理由
（issue 号 / 规范引用 / 清楚的技术理由）。裸的屏蔽不允许。

可接受的形式举例：

  # noqa: E501  -- 原因：URL 字符串超过 100 字符，拆行反而更难读
  LONG_URL = "https://..."

  // @ts-ignore: 因为第三方库类型不全，见 issue #1234
  const result = legacy.foo();

如果你本意是修掉底层问题（rule 03），那就去修，而不是把信号掐掉。如果这次
屏蔽确实站得住，补上理由注释再重试。如果你确实需要绕过这道闸门，把这次
拒绝呈给用户、让他手工编辑 —— 这套纪律是用来标记偷懒的，不是用来卡住你。
""",
    'read.deny.hardcode': """cc-enforcer · rule 10 违规（非必须硬编码）

工具：{tool_name}
目标：{file_path}
命中模式：{pattern_label}

片段（你写入内容里出问题的那一段）：
{snippet}

按 rule 10（rules/10-no-hardcoding.md），一个设计上属于配置、环境变量、
密钥库或函数参数的值被内联成了字面量。凭证、API key、token、私钥材料，
绝不能进源码。

继续的方式，三选一：

  (1) **把它外置**（首选，rule 03 修根因），例如
        api_key = os.environ["API_KEY"]          # 不是字面量
      真实值只留在未入库的 .env / 密钥库里。

  (2) **如果这确实是占位符 / 示例 / 测试夹具**，就让它看得出来：一个明显的
      占位值（`example`、`changeme`、`your-`、`<...>`、`${{...}}`、`dummy`、
      `redacted`），或在紧邻一行加一条 why 注释说明（可用词：essential /
      必须 / 必需 / example / fixture / placeholder / 占位 / sample / test data）。

  (3) **停下来上报**：如果这次硬编码真的无可避免，告诉用户由他决定 ——
      不要悄悄把一个密钥提交进去。

散文文档（.md / .rst / .txt / .adoc）与锁文件豁免；本检测器针对的是新写的
**代码**。
""",
    'read.deny.pathdep': """cc-enforcer · rule 11 违规（非必须路径依赖）

工具：{tool_name}
目标：{file_path}
命中模式：{pattern_label}

片段（你写入内容里出问题的那一段）：
{snippet}

按 rule 11（rules/11-no-path-dependency.md），一条机器相关的绝对路径 ——
用户主目录、或塞进字符串字面量的 shell 家目录变量 —— 被提交进了代码。
一换机器、换操作系统、进 CI，它当场就断。

继续的方式，三选一：

  (1) **运行时派生**（首选，rule 03 修根因）：
        base = Path(__file__).resolve().parent          # 相对模块
        base = Path(os.environ["CLAUDE_PLUGIN_DATA"])    # 来自配置变量
      用项目根标记、环境变量、tempfile 或传入参数 —— 绝不是一个写死的
      用户目录。

  (2) **如果这条路径确实必需**（一个在每台目标机器上都相同的固定系统位置），
      在紧邻一行加一条 why 注释讲清楚（可用词：essential / 必须 / 必需 /
      因为 / because / example / fixture / sample）。

  (3) **停下来上报**：如果可移植性真的做不到，告诉用户，而不是悄悄把你自己
      这台机器写死进去。

散文文档（.md / .rst / .txt / .adoc）与锁文件豁免；本检测器针对的是新写的
**代码**。
""",
    'read.deny.rolling': """cc-enforcer · rule 09 违规（滚动补丁拦截）

工具：{tool_name}
目标：{file_path}
滚动补丁计数器：本会话对该文件已落地 {current_count} 次小幅编辑；
这一次将是第 #{attempt_count} 次 —— 达到或超过阈值 {threshold}。

按 rule 09（rules/09-systematic-modification.md），对同一文件反复做**小幅**
编辑、中间却没有一次**系统式**重写，就是「滚动补丁」：每次小编辑只孤立地
修掉一个症状，总量信号说明这个文件的整体结构和根因从未被重新面对。

这里用的分类：
  小幅    = max(|old_string|, |new_string|) < {small_chars} 字符
            **且** 最大行数 ≤ {small_lines}
  系统式  = 最大字符数 ≥ {sys_chars} 或 最大行数 ≥ {sys_lines}
            或 该改动跨越了本文件的 ≥ {ratio_pct}%{scale_note}
            （把计数器清 0）
  中等    = 介于两者之间（不计数，也不重置）

任何计数值下都**永不计数**：
  净减少   —— new_string 比 old_string **更短**。滚动补丁是一种累加；
             一次让文件比原来更小的编辑不可能是它。
  记账类   —— 只有版本号 / ISO 日期字面量不同、其余每个字节都相同
             （散文文档里，纯整数也算）。升个版本号不是修 bug。

继续的方式，三选一：

  (1) **系统式重写**：把待办的几处小修合并成**一次** Edit（或 Write），
      让 `new_string` / `content` 达到 ≥ {sys_lines} 行 / ≥ {sys_chars}
      字符{cover_hint}。这会把该文件的计数器清 0。

  (2) **删而不是加**：净减少永不计数，所以把累加物删掉永远放行。绝不要
      给改动「注水」来越过阈值 —— 注水正是这道闸门要抓的东西。

  (3) **停下来上报**：告诉用户「这个文件需要一次系统式重写，请先看我的方案
      再让我继续」，让他决定是放宽约束还是换个思路。

这**不是**补丁标记检查（你的 new_string 里没有屏蔽标记）；这是**累积模式**
检查：太多小修说明的是理解不足，不是屏蔽。
""",
    'read.scale_note': ' —— 这里是 {lines_bar}/{file_lines} 行，或 {chars_bar}/{file_chars} 字符',
    'read.cover_hint': '，或 ≥ {lines_bar} 行 / ≥ {chars_bar} 字符 —— 先够到哪条算哪条',
    'stop.extra.hedge_matched': '命中的含糊词',
    'bash.register.header': 'cc-enforcer · register_read 被拒',
    'bash.register.command_label': '命令',
    'bash.register.needs_absolute': 'register_read 的 --file 必须是绝对路径（收到的是 {got}）。',
    'bash.register.missing_file': 'register_read：文件在磁盘上不存在：{path}',
    'bash.register.bad_hash': 'register_read：--hash 必须是 64 个小写十六进制字符（SHA-256）。收到的是：{got}',
    'bash.register.hash_mismatch': 'register_read：哈希不匹配。\n  --hash：  {claimed}\n  磁盘上：  {actual}\n要么你其实没读过这个文件，要么它在你算完哈希之后变了。重新 Read 拿到最新内容再重试。',
    'bash.register.not_persisted': 'register_read：这次登记没能写进会话状态（另一个进程正握着状态文件）。\n什么都没记下 —— 过一会儿重试，或者干脆再 Read 一次这个文件，那本来就是这个逃生口在绕开的主路径。',
    # ---- bash_guard ------------------------------------------------------
    'bash.deny': 'cc-enforcer · rule {rule} 违规（绕过模式）\n\n命中模式：{name}\n命令：{command}\n\n{explanation}\n',
    'bash.pattern.no_verify.name': '--no-verify（跳过提交钩子）',
    'bash.pattern.no_verify.explanation': '`--no-verify` 标志会跳过 git / commit 钩子。钩子的存在就是为了拦住坏代码；绕过它等于把坏代码发出去。按 rule 03（rules/03-root-cause.md），去修钩子失败的根因，而不是绕开钩子。如果用户明确要求你绕过，请让他手工执行这条命令，而不是由你代劳。',
    'bash.pattern.no_gpg_sign.name': '--no-gpg-sign（跳过提交签名）',
    'bash.pattern.no_gpg_sign.explanation': '跳过 GPG 签名会剥掉提交的可验证性。签名坏了就去修签名配置。按 rule 03（rules/03-root-cause.md），不要为了让一条命令跑通而绕过验证。',
    'bash.pattern.chmod_777.name': 'chmod 777（全局可写）',
    'bash.pattern.chmod_777.explanation': '全局可写权限（777）几乎从不解决底层的访问问题，还引入安全风险。按 rule 03（rules/03-root-cause.md），找出真正需要访问权的那个用户或进程，精确授权给它（例如 `chown` 加上 750 或 640 这类收紧的模式）。',
    'bash.pattern.rebase_skip.name': 'git rebase --skip（悄悄丢弃冲突）',
    'bash.pattern.rebase_skip.explanation': '`git rebase --skip` 不是解决冲突，而是把冲突的那个提交悄悄丢掉。按 rule 03（rules/03-root-cause.md），冲突来自真实的语义分歧 —— 跳过它会丢代码，或者掩盖掉本该暴露的设计问题。三选一：(1) 解决冲突（`git status` 看清冲突在哪，编辑，`git add`，`git rebase --continue`）；(2) 中止并换一种 rebase 策略（`git rebase --abort`）；(3) 如果你百分之百确定那个被跳过的提交不需要，请用户手工执行 --skip。',
    'bash.pattern.break_system_packages.name': 'pip install --break-system-packages（绕过 PEP 668）',
    'bash.pattern.break_system_packages.explanation': '`--break-system-packages` 绕过的是 Python 3.11+ 为防止 pip 改动系统 Python、进而搞坏包管理器安装的软件而加的 PEP 668 保护。按 rule 03（rules/03-root-cause.md），正确做法是装进虚拟环境（`python -m venv .venv && source .venv/bin/activate && pip install …`）、用 pipx 装工具，或走系统包管理器（`apt install python3-X`）。为了让一次安装成功而搞坏系统 Python，是「治症状不治根因」的教科书式反模式。',
    # essential: this message's subject IS the home paths the guard refuses.
    'bash.pattern.rm_rf_root.name': 'rm -rf 打到根 / $HOME / ~',
    # essential: this message's subject IS the home paths the guard refuses.
    'bash.pattern.rm_rf_root.explanation': '对系统根目录、$HOME 或 ~ 做递归强制删除是灾难性的，而且几乎从来不是正确的工具。按 rule 03（rules/03-root-cause.md），如果你要清理构建产物，用项目自己的清理目标（`make clean`、`npm run clean` 等）或删一个更具体的路径；如果你要重置工作区，用 git（`git clean -fdx` 限定在工作树内，或先 stash 再 `git reset --hard HEAD`）。如果用户真的要求一次破坏性的根级 rm，把这次拒绝呈给他、让他手工执行 —— 不可恢复的操作不要代劳。',
    'bash.pattern.force_push.name': 'git push --force 且未用 --force-with-lease',
    'bash.pattern.force_push.explanation': '强推可能不可逆地覆盖同事的工作。按 rule 03（rules/03-root-cause.md）：用 `--force-with-lease`（远端动过就拒推），或先 rebase 再正常 push，或解决分叉的根因。如果你百分之百确定必须强推，请用户手工执行。',
}
