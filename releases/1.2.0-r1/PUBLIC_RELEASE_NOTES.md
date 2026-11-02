# JC Response 1.2.0-r1 — Windows 候选预发布

面向有基础电脑操作能力的 Windows x64 用户。当前未签名，非 JC 官方产品；需要本机 Edge、自己的 JC 账号及支持本地 stdio 的客户端。WorkBuddy 自定义连接有维护者状态验收；本 ZIP 不是 WorkBuddy 市场连接器包。

下载 Assets 中的 JC_response-windows-x64-1.2.0-r1.zip 和外部校验文件，不要把 Source code ZIP 当 Windows 安装包。

- 程序版本 1.2.0；资料修订 r1；契约 response_flow/1.1；固定 CSV 30 列。
- 字节数 122270089。
- ZIP SHA256：91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713。
- 三个产品 EXE SHA256：d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d。
- 本次未重编译，1108 个 bin/ 文件与上一候选保持原样。

从 README 的快速开始进入；详细说明在包内 docs/。本人完成信任、JC 登录和首次范围确认；日常范围内读取不逐批打开许可窗口。安装核对只调用 jctrans_status，不读取业务。

已有旧版不要先卸载、退出登录、删除或回滚数据/预算。多个候选共用 1.2.0，必须比较文件哈希；already_installed 可能不更新说明和 Skill，应按升级白名单刷新。旧开发 Skill 不得与产品 Skill 混用。

单次 1–20 条/1 页；24 小时内测预算为 10 次新读取、100 记录额度、400 HTTP 尝试，并发 1。MCP 不开通、提额或清零，不提供报价提交、飞书写入、调度、推送和 DOM 联系人。预览字段可能交给 AI 云模型处理。

维护者报告通过新装、重复安装、资料升级、配置保留和 WorkBuddy status；见 WINDOWS_VALIDATION.md。当前包真实业务读取/导出及占用失败本轮未测；实际 Skill 加载需用户核对。构建提交未知，不声明可复现构建。

公开 Release 标签定位公开分发资料，不代表私有二进制的源码构建提交。未完成资产上传时，本文件只是发布正文准备稿。
