# JC回盘助手｜JC Response Assistant

用自然对话读取、核对自己 JC 账号的回盘，将同一批导出为 **30 列中文 CSV**。免费分享，提供安装接入、上手教学和回盘整理。**非 JC / JCTrans 官方产品。** 本仓公开 Skill、安装编排、使用说明和分发校验；私有业务内核不在此仓开源。

## 当前版本与获取

| 交付物 | 当前版本 | 位置 |
|---|---|---|
| JC回盘助手 Skill | **0.2.3**，标识 `jc-response-setup` | [公开源文件](skills/jc-response-setup/)；[发行记录](releases/skill-0.2.3/RELEASE_NOTES.md) |
| Windows x64 运行程序 | **1.3.0，资料修订 r2**，未签名预发布 | [GitHub Release v1.3.0-r2](https://github.com/bobbanga/jc-response/releases/tag/v1.3.0-r2) |

**本次源同步为草稿PR：原PNG图标尚待补传，Skill成品ZIP尚未上传Release。** 补齐前，仓库打包命令会拒绝缺失资源，不生成不完整替代包。已有完整上架ZIP的身份如下，不要猜GitHub下载地址。

- Skill文件：`jc-response-setup-0.2.3.zip`，**234614 字节**。
- Skill SHA256：`a86a58a26831e60a05247797cde92c78ea1543faf2c8e0145b4786d73ae70e42`。
- Windows运行包：`JC_response-windows-x64-1.3.0-r2.zip`，**122402084 字节**。
- 运行包SHA256：`747a62e46af7177cb6364461f7edc776a0797652e3e423570109b3da7c47f9c9`。

GitHub自动生成的 **Source code ZIP不是Windows安装包**；Windows大包也不是WorkBuddy技能上传包。Skill和程序分别版本化，配套契约为 `response_flow/1.1`，默认中文导出为 `JC_response_business/1.0`。本次展示同步没有修改或重编译运行程序。

旧版 [v1.2.0-r1](https://github.com/bobbanga/jc-response/releases/tag/v1.2.0-r1) 保留，它只输出技术表 `JC_response/1.1`。不能仅凭 `response_flow/1.1` 推断已支持中文导出。

## 第一次使用

需要 **Windows x64、本机Edge、WorkBuddy桌面端的本地执行能力和自己的JC账号**。普通使用不需要Python、Nuitka或私有源码。未验证的macOS、Linux、其他AI客户端和云端环境不作兼容承诺。

按当前平台实际支持的方式加载Skill，再选择一个独立任务：

```text
我是第一次用，帮我接入JC回盘助手，并教我怎么提问。
```

```text
读取一批5条回盘，整理成清单，不保存、不继续。
```

```text
读取一批5条回盘及详情，导出同一批的30列中文CSV，完成后停止。
```

助手先复用已核对的安装；需要下载、安装或改配置时说明范围并取得同意。本人完成实际出现的客户端信任、JC页面登录和首次范围确认。接入核验只查状态，不自动读取。不要把密码、Cookie或Token发到聊天。

第一条是接入和教学；第二条仅取列表；第三条明确读取详情并导出同一批。已有批次后仍可说“导出刚才这批，不重新读取”。缺失或隐藏字段保持为空，不猜报价、港口或联系方式。

## 已经装过旧版

**不要先卸载、删除数据、退出登录或回滚预算。** 同版本号不一定同文件；`already_installed` 不保证说明和Skill已刷新。脚本只对身份可核实的已审核旧版本升级，更高版本、未知来源、占用或配置冲突会停止。

保护凭证、授权、预算、快照和历史文件；保留 `scys-mcp` 和其他连接。日常业务不回退全局 `jctrans` 或开发仓库。旧开发Skill冲突需先定位，经本人同意处理；产品目录含Skill文件不等于客户端已加载。

当前说明见 [产品条件](skills/jc-response-setup/references/product-notes.md)、[升级与排障](skills/jc-response-setup/references/upgrade-and-troubleshooting.md)、[教学示例](skills/jc-response-setup/references/prompt-examples.md)。旧版 `docs/` 和 `releases/1.2.0-r1/` 保留其历史记录，不当作本版新增验收。

## 能力、费用和隐私

单批数量明确，**1–20条、1页**。滚动24小时内测预算为 **10次新读取、100记录额度、400次上游HTTP尝试**，并发读取1。这是产品策略，不是JC官方额度；重登不清零。同批查看、保存和导出不增加JC读取，但保存和导出会写本地文件。

不自动续读、不提交报价或应盘、不发消息、不作危险品接载或商业承诺、不采集DOM联系人、不写飞书、不调度推送；MCP不能开通、提额或清零。业务规则见 [权威业务Skill](skills/jc-response-preview/SKILL.md)。

本助手免费分享；JC服务、AI客户端或模型可能另有费用。WorkBuddy后台价格须发布者亲自选“免费”，ZIP不会修改表单。业务字段可能由客户端云模型处理，不承诺全部数据绝不上云。程序未签名，不要求关闭系统防护。

## 维护与反馈

反馈到 [Issues](https://github.com/bobbanga/jc-response/issues)，提供版本、哈希、失败步骤和脱敏错误，不附凭据、完整配置、数据库或真实CSV。

[0.2.3发行记录](releases/skill-0.2.3/RELEASE_NOTES.md)区分已完成同步、待补齐资源和验证范围。成品ZIP只作为Release资产，不提交Git历史；公开PNG可入仓。平台审核与仓库发布是不同状态。

维护者命令：

```text
python -m unittest discover -s tests -v
python scripts/sync_setup_references.py
python scripts/pack_setup_skill.py
```

版本从SKILL.md读取，示例各不超过3条，图标和产品说明不可漏包。打包拒绝覆盖已有文件并核对已审核ZIP身份。Windows安装测试需要显式隔离测试条件，缺条件会注明跳过；静态通过不等于本轮已经执行Windows或JC业务。
