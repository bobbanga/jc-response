# JC Response｜JC 回盘助手

把自己 JC 账号的一批回盘带进 AI 对话，按需要查看、整理和导出。**免费本地工具，非 JC 官方产品。** 本仓公开使用说明、Skill 和分发适配；业务内核不在此仓开源。

## 下载与当前状态

面向能下载 ZIP、解压和核对文件的 Windows 用户。程序版本 **1.2.0**，包修订 **r1**，契约 **response_flow/1.1**，当前是**未签名候选包，不是稳定版承诺**。

**[查看 Releases 和 Windows 资产](https://github.com/bobbanga/jc-response/releases)**。请选择 Assets 中的 `JC_response-windows-x64-1.2.0-r1.zip`，不要下载 GitHub 自动生成的 Source code ZIP 来安装。

> 截至本次文档更新，Release 二进制上传尚未完成。没有看到该资产时就是尚未提供下载，不要猜下载地址或使用第三方镜像。维护者按[上传流程](docs/Release上传.md)发布并回下载校验后，更新[分发状态](releases/1.2.0-r1/distribution.json)。

| 文件身份 | 固定值 |
|---|---|
| 文件名 | `JC_response-windows-x64-1.2.0-r1.zip` |
| 字节数 | `122270089` |
| ZIP SHA256 | `91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713` |
| 三个产品 EXE SHA256 | `d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d` |

r1 没有重编译，1108 个 bin/ 文件保持不变。已有维护者报告的新装、重复安装、资料刷新和 WorkBuddy 状态验证；本版的完整真实读取/导出、文件占用失败测试仍未在该报告中完成。详见[验收补充](releases/1.2.0-r1/WINDOWS_VALIDATION.md)。

## 第一次使用

1. 确认电脑是 **Windows x64**，有本机 Edge、可用的 WorkBuddy 桌面端和你自己的 JC 账号；当前无 macOS/Linux 安装包，也不支持网页客户端直接远程连接。
2. 下载上面指定的 Windows 资产，校验并解压。按[快速开始](docs/快速开始.md)安装；也可把[接入提示词](docs/接入提示词.md)与解压路径交给本机 AI。**普通使用不需要安装 Python、Nuitka 或克隆私有仓。**
3. 本人完成需要的客户端信任、JC 登录和一次范围确认。先查状态，再按自己需要读取一批。不要把密码、Cookie 或 Token 发到聊天。

```text
只调用 jc-response 的 jctrans_status，核对契约、授权状态和登录状态；不要读取回盘。
```

状态正常、配套 Skill 确认生效后，再用一个小任务开始：

```text
使用 JC Response 读取一批 5 条回盘，不保存，不继续下一批。
```

```text
把刚才这批导出为 CSV，只使用同一批数据，不重新读取。
```

这些是用法示例，不是宣称当前用户账号已读到数据。返回不足、权限失效或预算耗尽时如实停止。

## 已经装过旧版

**不要先卸载、删除数据或退出 JC 登录。** 多个旧候选曾共用 1.2.0 版本号，必须比对文件哈希。安装器的 `already_installed` 可能只说明程序判断无需复制，**不表示说明和 Skill 已刷新**。

请按[升级与回退](docs/升级说明.md)或交给 [Cursor 复核与升级](docs/Cursor复核与升级.md)。保留凭证、授权、预算和已保存数据；同二进制仅资料变化时用精确白名单刷新。旧的 `jctrans-response-assistant` Skill 可能指向开发 CLI，需先备份并定向停用，不能混用。

## 能做什么、不能做什么

单次明确读取 **1–20 条、1 页**，在同一批上查看已有详情、保存和导出固定 30 列 CSV。首次开通后日常范围内读取不再逐批打开许可窗口；客户端自己的审批仍由客户端决定。

滚动 24 小时内测上限为 **10 次新读取、100 记录额度、400 次上游 HTTP 尝试**，并发读取为 1。这是产品策略，不是 JC 官方额度；退出重登不清零。同批保存/导出不增加 JC 读取，但会写本地文件。

不提供报价提交、应盘、消息发送、DOM 联系人、危险品自动处理、飞书写入、调度或推送；MCP 不能开通权限、提额或清零。预览字段会进入 AI 客户端，可能由云模型处理；不承诺“所有数据绝不上云”。

## 文档与反馈

[快速开始](docs/快速开始.md) · [兼容性与排障](docs/兼容性与排障.md) · [使用说明](docs/使用说明.md) · [安全说明](docs/安全说明.md) · [产品 Skill](skills/jc-response-preview/SKILL.md)

问题反馈使用 [GitHub Issues](https://github.com/bobbanga/jc-response/issues)。只提供版本、文件哈希、失败步骤和脱敏错误；不要附账号凭据、完整配置、数据库或业务 CSV。

WorkBuddy 市场包尚在适配，**不能把本 Windows 大包直接上传到 20 MB 的连接器入口**。维护者任务：[Cursor 市场分发适配](docs/Cursor-WorkBuddy市场适配.md)。

维护者验证：`python -m unittest discover -s tests -v`。普通用户不用运行测试或重打包。二进制只做 Release Assets，不进入 Git 历史。
