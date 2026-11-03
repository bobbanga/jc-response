# JC回盘助手审阅记录

日期：2026-11-03。当前候选 Skill 0.2.0，尚不可提审。没有 push、merge、发布或提交 WorkBuddy 审核。

2026-11-03 再次核对 https://open.workbuddy.cn/docs/skill 。必填 frontmatter 仍是 name、display_name、display_name_en、description、description_zh、description_en、version、author。`allowed-tools` 可选。引用方式仍是 `@references/xxx.md`。页面没有给出技能 ZIP 的字节上限。

1.3.0 候选运行包已在本地编译，默认导出 `JC_response_business/1.0`。它尚未公开上传，下载地址为空。已发布的 v1.2.0-r1 仍是技术表 `JC_response/1.1`。文件级中文表核对不能代替逐条对照 JC 页面。

## 文档与本机

2026-11-03 核对的官方页面：

- https://open.workbuddy.cn/docs/skill ：技能目录含 `SKILL.md`、`references/`、`scripts/`。必填 frontmatter 为 name、display_name、display_name_en、description、description_zh、description_en、version、author。`allowed-tools` 可选。页面没有给出技能 ZIP 的字节上限。
- https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market ：技能页签里可以市场安装；「添加技能 > 上传技能」写入本地技能包。也提到从 `.agents` 等目录复制的技能保持原文件。
- https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide ：用户级配置是 `~/.workbuddy/mcp.json`。自定义 MCP 不是本 Skill 的安装入口。
- https://open.workbuddy.cn/docs/developer-agreement ：2026-10-22 版 1.0，只确认平台可以审核和拒绝资产。

本机 WorkBuddy 5.9.3 的界面文案同时有「上传技能」和「本地上传技能将在后续版本开放」。本次没有点击该按钮，也没有改用户技能目录。文档与本机文案不一致，不能把其中一方写成已经验证的加载结果。

## 运行包

固定身份在 `skills/jc-response-setup/references/runtime-pin.json`。当前锁定尚未发布的 1.3.0 候选：`JC_response-windows-x64-1.3.0.zip`，122397333 字节，SHA256 `3c4dc966c07d82722d4fbde9ed8542a55375ec16d3a85cdd26abbfe80598dc3e`，三个 EXE `5a65927202043b605c48019ae552b110612c68600b745fb33af14764de4e9ff3`，`csv_schema` 为 `JC_response_business/1.0`，下载地址为空。已发布的 v1.2.0-r1 仍是 122270089 字节、SHA256 `91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713`，只输出技术表。市场适配提交 `8352547331fb4838715a50095dfeeaeb959ecc52` 只作为已见记录，没有并入。

## 自动测试

`python -m unittest discover -s tests`：17 OK。自动测试覆盖危险 ZIP、版本分类、同意前不下载、更高版本停止、配置冲突不覆盖和资料锁停止。另一次非管理员检查把脚本复制到带中文和空格的目录后执行 `inspect`，退出码 0，`downloaded=0`。隔离环境对真实 v1.2.0-r1 的一次安装返回 `install_status=installed`、`install_exit=0`、`install_judged=verified`；再次安装为 `class=match`、`downloaded=0`。合成哨兵仍在，隔离环境没有写出 mcp.json，本机正在使用的程序和配置未变。

模拟业务使用私有测试夹具，不在本仓内：5 条 `simulation=true`、`jc_api=blocked`，导出后上游调用仍是 1，明确续读后变为 2。这不是 WorkBuddy 会话，也不是真实 JC。

## 尚未完成

真实 WorkBuddy 没有加载本 Skill。新会话里的正式 MCP 状态没有在本轮读取。真实 JC 读取没有执行。

2026-11-03 补充：登录、读取和同批导出的技术链路证据保留。已安装的 v1.2.0-r1 仍是 `JC_response/1.1` 技术表。新编译的 1.3.0 候选包可以导出中文业务表，但还没有公开下载地址，不能提审。
