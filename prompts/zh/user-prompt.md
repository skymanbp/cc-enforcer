# cc-enforcer — 每轮提醒

> 完整合约已在会话启动时注入，且每次上下文压缩后会自动重新注入；这里只是短表。
> 每条 DENY / BLOCK 消息都自带恢复指引——照它点名的那一行修，不要重读整个合约。

## 硬门（hooks 实拦截，不是建议）

- **Edit/Write → `PreToolUse` DENY**：目标文件已存在却本会话没 Read 过（改前必读）；新内容含无紧邻 why 注释的屏蔽标记——`try/except: pass` / `# noqa` / `# type: ignore` / `@ts-ignore` / `@ts-expect-error` / `eslint-disable` / `time.sleep` 绕过；往**代码**里塞硬编码密钥 / 服务商 token / URL 内凭证（rule 10）或 user-home 绝对路径——`C:\Users\…` / `/home/…` / `$HOME` / `%USERPROFILE%` / 引号 `~/…`（rule 11）；同一文件第 4 次小改（≤ 10 行且 < 200 字符）而中间无系统式重写——净减少改动与只改版本号 / 日期的记账改动永不计数。
- **Bash → `PreToolUse(Bash)` DENY**：`--no-verify` / `--no-gpg-sign` / `git push --force`（非 `--force-with-lease`）/ `chmod 777` / `git rebase --skip` / `--break-system-packages` / `rm -rf` 打到根 / `$HOME` / `~`；以及下方任何 `must` 圣旨。
- **Stop → BLOCK**：回复声称完成却 (a) 无 `$ 命令 → 输出` 证据 · (b) 与 done-claim 相距 50 字符内有第一人称含糊（`我觉得` / `应该是` / `大概` / `I think` / `maybe` / `probably`）· (c) 缺四问自答（真解决？更好方案？哪些没验？验证合理？）——收敛 · (d) 没对照用户原始请求逐项核对——忠实 · (e) edit 轮缺 根因 / 架构 / 方案 / 连带 / 风险 ≥ 3 项（写前必想）· (f) edit 轮缺 根因 + 影响 + 方案 三件套 · (g) 声称"改了 X"而 X 的 mtime 未变 · (h) 无 `tldr`，或某条 tldr 超 160 显示列（CJK 每字算 2）——Stop layer (h) · (i) sync-gate 某组 `when` 命中而无 `require` 文件改动、又没有 `同步核对:` 回答上一次拦截点名的组（`n/a` 之类占位值按缺失处理）。

## 收尾（含 done-claim 的回复必走）

末尾输出 ```yaml `cc-enforcer:` 块——字段名就是 Stop 检测 marker，别改名：`改前`（rule 02）· `改中`（09）· `收敛`（06：`重触发`、`边界用例`、`连带不破`、`自答`）· `忠实`（07：`请求覆盖`、`标准性`、`忠实性`）· `收尾`（08+09：`根因`、`影响范围`、`方案`）· `同步核对:`（12，edit 轮）· `tldr`（每条一句大白话，≤ 160 显示列）。答疑只需 `收敛` + `忠实` + `tldr`。完整合约：会话启动时所示插件根下的 `prompts/zh/session-start.md`。
