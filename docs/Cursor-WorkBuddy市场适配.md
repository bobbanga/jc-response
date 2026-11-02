# Cursor：发布已审核资产，并制作 WorkBuddy 市场适配

请直接执行。阶段 A 完成 GitHub 二进制资产上传；阶段 B 制作小型市场包。不要再重构业务内核，不重编译或重打包 r1，不把“配置生成”当成“市场流程通过”。

## 0. 仓库与边界

公开仓：https://github.com/bobbanga/jc-response 。先读 AGENTS.md、快速开始、兼容性与排障、升级说明、现有 Skill、发行 manifest、distribution.json、WINDOWS_VALIDATION.md、Release上传.md。

先检查 remote、分支、HEAD、工作区。维护者本机还有未推送站点分支，不要 reset、覆盖或强制切换；从已审阅远端主线建立独立 worktree 和 feat/workbuddy-market-adapter。产品内核仍在私有 bobbanga/jctrans-cli，本轮只读参考，禁止复制到公开仓。

r1 文件身份：JC_response-windows-x64-1.2.0-r1.zip，122270089 字节，SHA256 91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713。程序 1.2.0、契约 response_flow/1.1、未签名；资料修订不是重新编译。

## A. GitHub 资产发布（本轮已授权）

按 docs/Release上传.md 执行：先核对是否已有完全匹配资产，没有才上传原 ZIP 与外部 SHA256。用户已经授权，不再重复问是否可以上传该已审核包；GitHub 正常登录或系统审批仍由本人完成，不能索取或显示 Token。

找不到 ZIP 只问实际路径，不全盘搜索。使用已登录 gh 或正常网页流程，先 draft 校验，再 v1.2.0-r1 prerelease、latest=false；回下载核对大小/哈希，拿真实 browser_download_url，不猜链接。已有不一致资产停止，不用 --clobber，不改已有标签，不提交二进制进 Git。

公开资料的标签不是私有二进制构建提交。发布成功后更新 distribution.json 和 README 的上传状态，保留原 ZIP 内 candidate 元数据和原哈希不动。只提交本轮明确状态文件，不顺带推送其他未审阅工作。

没有上传接口、认证或网络时如实 BLOCKED，不声称文件已经公开。阶段 B 可做离线结构，但没有真实下载 URL 就不能通过新用户分发验收。

## B1. 先核对平台原文

- https://open.workbuddy.cn/docs/connector
- https://open.workbuddy.cn/docs/skill
- https://open.workbuddy.cn/docs/developer-agreement

记录日期和关键章节。采用 MCP + Skill、本地 stdio、一个连接器对应一个 MCP Server。当前平台上传页限制 20 MB，本轮用不超过 20,000,000 字节的保守阈值。

不要把 CLI 方案 macOS/Linux 要求直接当所有本地 MCP 的门槛；也不承诺 Windows-only 必然审核通过。没有官方平台兼容字段时在描述声明，不发明字段。minWorkbuddyVersion 根据实际采用功能的官方版本要求填写，实测版本另列。

官方 MCP 配置可能支持 preAuth:"cli" 认证桥接，这不等于 CLI/MCP 混装一概禁止；它也不是任意下载钩子。本轮默认不用，确需使用先验证认证契约和本人操作边界。不得把 JC 网页登录称为 OAuth。

## B2. 两个包各司其职

大 Windows 包放 GitHub Release 不变。小市场 ZIP 包含 connector-meta.json、mcp.json、自有合法图标、skills/jc-response-preview/SKILL.md，以及确实需要的轻量启动/安装适配。

metadata.type=mcp；英文显示名 JC Response Assistant。source 先核实不冲突，不编造平台生成的连接器 ID。声明 Windows x64、外部运行包、本机 Edge、本人 JC 账号、未签名、非 JC 官方、隐私与预算限制。连接器版本和程序版本分别管理。

禁止打包 122 MB 运行库，禁止随意删除运行依赖凑 20 MB。不能只交付下载广告：必须能在声明前提下启动真实产品能力。图标不冒用 JC 或腾讯官方标识。

## B3. 先用最小实验确定启动路径

在实际 WorkBuddy 本地导入/官方自测中验证 command、args、cwd、包资源定位和变量展开。不假设 %LOCALAPPDATA%、${VAR}、相对路径或虚构 CONNECTOR_DIR 自动可用。

可以评估 Windows 系统级轻量启动器，或官方托管 Node runtime。选型以真实验证为准，不能依赖用户系统 Python/Node、私有包、开发仓库或全局 jctrans。采用 runtime 就填对应官方 runtime/minWorkbuddyVersion。

只定位当前用户正式安装目录中的 jctrans-mcp.exe，不扫描 PATH/全盘，不回退其他凭证。至少核对发布 EXE/契约身份，不能只信 VERSION。没有安装或版本未知时明确诊断并停止，不无限重启下载，不假造工具结果。

stdio 双向透传；stdout 只用于 MCP，日志到 stderr；处理 EOF、退出码、子进程清理。不要打开远程端口，不在初始化/每次调用时偷偷安装、修改配置或清空预算。

若平台没有已证实的包资源路径或缺失组件引导方式，提供最小复现并 BLOCKED，不能先造大型下载框架掩盖这一点。

## B4. 首次安装和旧版升级

用户同意安装/升级后才能获取外部包。来源必须是阶段 A 验证的固定 Release HTTPS 资产及固定大小/SHA256；不使用 latest、镜像或下载后直接执行。

下载到新临时位置，限制大小和重定向，核验全包后安全解压；防路径穿越、链接、重解析点。不得关闭防护、修改全局执行策略或强杀客户端。

复用 --install-user --json；已有用户数据、预算、授权和登录态原位保留。相同版本不代表相同文件；already_installed 不代表资料同步。按升级说明的精确白名单处理资料变化，不手工混配 EXE/DLL，不改 VERSION 骗安装器。

特别注意：市场连接器由平台注册时，不要自动再运行 --configure-workbuddy 创建第二个自定义连接！该命令属于已有自定义接入路线。必须测试现有 jc-response 与市场项的共存和迁移，不能假定同名自动合并。迁移需本人确认，只处理目标项、保留恢复方式，scys-mcp 和其他服务不动。

Trust、JC 登录、首次范围确认都由本人完成。适配器不提供 authorize、提额、reset 工具，不写授权文件，不修改 approvals；日常已经开通的读取不增加新的逐批 GUI/elicitation 要求。

运行文件不一致、程序目录含用户数据、conflict、target_in_use、未知/更高版本时停止。需要修改私有安装器则单独报告，不在市场壳里绕过。

## B5. Skill 和使用规则

复用仓库唯一产品 Skill，市场包只生成随包副本并校验一致性。真实市场工具 namespace 可能与自定义连接名不同，按实际工具清单适配，不能盲写错误路由。

维持 response_flow/1.1、limit 必填 1–20、单页、范围内预授权、预算停止、同批导出、不填猜测字段、不自动下一批、不调用全局 CLI、不宣称全部数据不上云。

产品目录含 Skill 不等于客户端已加载。发现旧 jctrans-response-assistant 先定位冲突，取得确认后备份到扫描根外再停用。不要删开发环境或无关技能。

## B6. 测试和交付

公开仓放适配源文件、包装脚本、合成测试；最终 ZIP 放 Git 外。明确核对以下项目，只有实际观察才能 PASS：

| 编号 | 场景 |
|---|---|
| M01 | ZIP <20,000,000 字节；必需文件/图标/Skill/单 MCP schema 与所有引用正确 |
| M02 | 无开发仓、Python、系统 Node 的 Windows；中文/空格路径、非管理员 |
| M03 | 正式 r1 已安装：真实 stdio initialize、tools/list、status，stdout 无污染 |
| M04 | 未安装、下载失败、哈希不符、未知版本均停止并给出真实引导 |
| M05 | 旧版/资料刷新保留凭证预算；占用失败不强行覆盖 |
| M06 | 市场项与原自定义连接不重复执行业务，其他 MCP 不变 |
| M07 | 新用户本人登录/范围开通，与旧用户已有状态复用分别测试 |
| M08 | 正确 Skill 真正加载，Agent 不走旧 CLI |
| M09 | 隔离模拟读取 5→同批导出，上游新增 0；超限停止 |
| M10 | 实际 WorkBuddy 本地导入或官方自测；不是独立 Python MCP 客户端替代 |

额度耗尽和故障注入只用模拟数据。真实 JC 读取需要用户另行同意；不把模拟当真实，不把状态成功当业务完整。平台解析、自测、提交审核和审核通过四个状态分开。

本轮允许适配分支 push 并创建 draft PR，不合并；提交前逐文件检查。禁止自动提交 WorkBuddy 审核、自动部署站点、修改私有业务内核。二进制不入 Git。

## 回复格式

阶段更新每次最多 3 句话；需要本人操作只说当前一件事。最终正文约 1500 个中文字以内，表格另计：

1. GitHub 发布：tag、真实 Release/资产 URL、大小/SHA256、回下载结果。失败写 BLOCKED，不编链接。
2. Git：基线与新提交、公开分支/PR、私有仓是否变化。
3. 适配路线：运行包定位、未安装/升级、是否使用 preAuth、官方依据和待确认项。
4. 市场 ZIP：路径、字节数、SHA256、文件清单、安全扫描。
5. M01–M10：PASS/FAIL/BLOCKED/NOT_RUN + 实际证据。
6. 结论只能为“可以上传”“先改再上传”“不能上传”，不等同平台审核通过。

最后只给一个最必要的本人动作。不写“全平台支持”“完全安全”“已上架”，不重新讨论 JC 核心架构。
