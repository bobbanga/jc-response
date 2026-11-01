# 1.2.0-r1 文档修订候选

## 修复

安装提示词去掉安装 Agent 执行范围开通命令的路径，只保留安装和配置两个产品命令。信任、登录和范围开通由本人完成。安装核对只用 jctrans_status。

修正“完全没有开发路径字串”和“保存/导出消耗 JC 读取预算”的不准确表述。Skill 示例不承诺最新排序。增加已有安装升级、同版本不同文件、说明/Skill 刷新和失败回退说明。

VERSION 仍为 1.2.0；r1 是资料修订，不是新编译版本。VERSION 的换行已规范化，字段值未改。新增 RELEASE-METADATA.json 和升级说明，重建内部及外部校验和。

## 已执行验证

核对原 ZIP 身份；重打包后 CRC、路径安全和完整校验和通过。bin/ 下 1108 个文件全部与原包逐字节一致，包括三个产品 EXE 和第三方运行文件。共核验 1116 条内部校验和。公开资产脚本的 9 项单测通过；它们不是产品功能测试。

未新增产品 Python 源码、凭证或业务数据。certifi 的 CA 证书、Playwright/Tcl/Tk/JSON Schema 和运行库保留。静态审阅不等于恶意软件认证。

## 仍需 Windows 复核

本环境未执行 Windows EXE。源码显示 already_installed 可能因版本和 MCP EXE 哈希相同而跳过复制，但本包二进制来源提交未能绑定，不能据源码宣称动态通过。

执行 docs/Cursor复核与升级.md，验证本包在隔离环境和已有安装上的行为。重点是全部运行文件、文档/Skill、真实契约、数据预算保留和非目标 MCP 保留。失败时不能卸载清库或手工替换二进制。

在 Windows 复核通过前，release_status 保持 candidate，download_url 为空。不发布稳定 Release、不覆盖已发布同名资产。具体大小和哈希以本目录 manifest.json 为准。
