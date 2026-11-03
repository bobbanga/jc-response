# JC回盘助手审阅记录

日期：2026-11-03。Skill 版本 0.1.0 candidate。没有 push、merge、发布或提交 WorkBuddy 审核。

## 文档与本机

2026-11-03 核对的官方页面：

- https://open.workbuddy.cn/docs/skill ：技能目录含 `SKILL.md`、`references/`、`scripts/`。必填 frontmatter 为 name、display_name、display_name_en、description、description_zh、description_en、version、author。`allowed-tools` 可选。页面没有给出技能 ZIP 的字节上限。
- https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market ：技能页签里可以市场安装；「添加技能 > 上传技能」写入本地技能包。也提到从 `.agents` 等目录复制的技能保持原文件。
- https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide ：用户级配置是 `~/.workbuddy/mcp.json`。自定义 MCP 不是本 Skill 的安装入口。
- https://open.workbuddy.cn/docs/developer-agreement ：2026-10-22 版 1.0，只确认平台可以审核和拒绝资产。

本机 WorkBuddy 5.9.3 的界面文案同时有「上传技能」和「本地上传技能将在后续版本开放」。本次没有点击该按钮，也没有改用户技能目录。文档与本机文案不一致，不能把其中一方写成已经验证的加载结果。

## 运行包

固定身份在 `skills/jc-response-setup/references/runtime-pin.json`。2026-11-03 重新计算了本机已保存的公开 ZIP，大小和 SHA256 仍是 122270089 与 `91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713`。`origin/main` 上的分发记录当时仍写着未上传；本分支只把这条已发布事实补上，不包含市场连接器启动器。市场适配提交 `8352547331fb4838715a50095dfeeaeb959ecc52` 只作为已见记录，没有并入。

## 自动测试

`python -m unittest discover -s tests`：17 OK。自动测试覆盖危险 ZIP、版本分类、同意前不下载、更高版本停止、配置冲突不覆盖和资料锁停止。另一次非管理员检查把脚本复制到带中文和空格的目录后执行 `inspect`，退出码 0，`downloaded=0`。隔离环境对真实 v1.2.0-r1 的一次安装返回 `install_status=installed`、`install_exit=0`、`install_judged=verified`；再次安装为 `class=match`、`downloaded=0`。合成哨兵仍在，隔离环境没有写出 mcp.json，本机正在使用的程序和配置未变。

模拟业务使用私有测试夹具，不在本仓内：5 条 `simulation=true`、`jc_api=blocked`，导出后上游调用仍是 1，明确续读后变为 2。这不是 WorkBuddy 会话，也不是真实 JC。

## 尚未完成

真实 WorkBuddy 没有加载本 Skill。新会话里的正式 MCP 状态没有在本轮读取。真实 JC 读取没有执行。
