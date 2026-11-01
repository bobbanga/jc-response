# jc-response

JC Response Assistant｜JC 回盘助手 — free WorkBuddy local skill for JC inquiry responses.

公开分发仓，不包含私有 JC 业务内核。Windows x64 本地运行、用户自带 JC 账号，通过 stdio MCP 接入 AI 客户端。本项目不是 JC 官方产品。

## 当前候选

**1.2.0-r1：文档修订候选，Windows 升级验收待完成，尚未发布下载资产。** 程序仍为 1.2.0，契约 response_flow/1.1，未签名。r1 不修改或重编译程序，不宣称修复二进制行为。

- [安装提示词](docs/接入提示词.md) · [安装说明](docs/安装说明.md)
- [已有旧版：升级与回退](docs/升级说明.md)
- [使用说明](docs/使用说明.md) · [安全说明](docs/安全说明.md)
- [产品 Skill](skills/jc-response-preview/SKILL.md)
- [发行清单](releases/1.2.0-r1/manifest.json) · [ZIP 校验和](releases/1.2.0-r1/SHA256SUMS.txt)
- [Cursor 复核与升级任务](docs/Cursor复核与升级.md)
- [修订及验证记录](releases/1.2.0-r1/RELEASE_NOTES.md)

历史候选曾复用 1.2.0 版本号，必须比较文件身份。already_installed 不代表说明、Skill 或全部 DLL 已更新。升级不清理数据、不重置预算、不要求先退出 JC 登录。

本人完成信任、登录和首次范围开通后，按明确数量读取 1–20 条、1 页。已有批次的保存/导出不重新读取 JC。MCP 不开通、提额、清零，不提供报价提交、DOM 联系人、飞书写入、调度和推送。预览字段会交给 AI 客户端，不能承诺全部业务数据绝不上云。

## 维护者验证

```text
python -m unittest discover -s tests -v
python scripts/repack_reviewed.py --source <已审阅原ZIP路径> --output <新ZIP路径>
```

脚本只接受固定原包，不运行 EXE，不访问 JC，不覆盖原包。bin/ 文件逐字节保留。压缩器版本可能影响 ZIP 字节，重打包哈希不一致应先核对环境，不得擅改发布哈希。

二进制不进入 Git。GitHub 自动生成的 Source code ZIP 不是 Windows 安装包。未发布时不猜下载地址，不以 latest 跳转替代固定版本与哈希。
