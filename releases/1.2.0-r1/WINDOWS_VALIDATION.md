# Windows 后续验收补充

整理日期：2026-11-02。原审阅提交：ef4425109977197e816c38a76b713595bf140de2。

证据来源：维护者转交的 Windows Cursor 实测报告及 WorkBuddy 新会话状态摘要。整理者没有独立运行 Windows EXE，未收到全部原始日志。PASS 指维护者报告通过，不表示第三方认证或全部历史版本覆盖。

被测 ZIP：122270089 字节；SHA256 `91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713`。三个产品 EXE SHA256 均为 `d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d`。1108 个 bin/ 文件与上一候选不变。

| 项目 | 状态 | 报告摘要 |
|---|---|---|
| 公开资产测试 | PASS | 9 项 |
| ZIP/CRC/路径/内部校验和 | PASS | 1116 条校验记录 |
| 隔离新安装 | PASS | exit=0，installed，EXE 匹配 |
| 重复安装 | PASS | already_installed，文件不变 |
| 相同程序、不同说明 | PASS | already_installed，说明未重新复制 |
| 九项资料刷新 | PASS | 刷新后目录与 r1 相同 |
| 上一候选包升级场景 | PASS | 用上一候选包模拟，不外推所有旧版 |
| 配置保留、坏 JSON、同名冲突 | PASS | 正常 configured；错误 conflict 且未改文件 |
| 哨兵及本人电脑数据保留 | PASS | 报告称安装、刷新、status 前后未变 |
| 隔离 stdio status | PASS | response_flow/1.1，未登录，无业务记录 |
| 本人电脑实际升级 | PASS | bin/ 已相同，按白名单刷新资料，EXE 未换 |
| 正式 MCP 配置 | PASS | already_configured，正式路径，其他连接保留 |
| WorkBuddy 新会话 status | PASS | response_flow/1.1；active/scoped_preauthorization；present |
| WorkBuddy 实际加载 r1 Skill | NOT_RUN | 发现旧开发 Skill 冲突；status 不证明新 Skill 生效 |
| target_in_use 文件占用失败 | NOT_RUN | 无对应实测 |
| 本次包真实读取与同批导出 | NOT_RUN | 本轮只查安装与状态 |
| WorkBuddy 市场安装 | NOT_RUN | 尚未制作并验收适配包 |

可以上传为候选/预发布资产，不声明稳定版。用户实际执行业务前需处理本机旧 Skill 冲突，这不是 ZIP 带了旧开发 Skill 的证据。

包内与 release-files 中的 NOT_RUN 是制包时记录，保留原字节和哈希；本文件是后续报告，不覆盖历史事实。当前未签名，二进制构建来源提交仍未知。
