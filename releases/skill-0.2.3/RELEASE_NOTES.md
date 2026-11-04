# JC回盘助手 Skill 0.2.3｜源同步记录

日期：2026-11-04。源仓基线 `58dfcef8b34a0c153b65e1876efc1bc135dbf7aa`。

## 成品身份与未完成项

已交付的完整上架包：`jc-response-setup-0.2.3.zip`，234614字节，SHA256 `a86a58a26831e60a05247797cde92c78ea1543faf2c8e0145b4786d73ae70e42`。

**当前为草稿PR：PNG尚待补传，Skill ZIP尚未上传GitHub Release。** `skill-v0.2.3` 是建议标签，不表示已创建。WorkBuddy审核状态未在本轮核实。

原图：`skills/jc-response-setup/references/market-icon.png`，512×512，210492字节，SHA256 `ba094f4149d26dd5521bb2052856bee71902fb43f7b4fc11ec87a1c8ed41cfde`。不得用重新生成的近似图替换。

## 本次同步

同步0.2.3的简介、免费/Windows/非官方说明、中英文各3条独立示例、教学资料和产品说明。既有安装脚本、业务规则、运行锁定和升级参考不变。Windows程序仍为已发布的v1.3.0-r2，未重编译、未修改预算或权限。

生成脚本从SKILL.md读版本，保留已有展示元数据和审核历史；打包器纳入产品说明和PNG，检查引用、哈希、数量和资源。旧测试中的个人机器路径及隐式读取正式安装，改为显式提供离线fixture；Windows测试仍保留，缺环境明确跳过。

已交付ZIP中的source-map记录的是制包时状态，`source_repository_updated=false` 不回改成品。后续源同步状态以本文件和PR为准，避免只更新状态就改变已交付哈希。

## 本轮验证

本地含原PNG的Linux副本：13项相关测试中11项通过，2项Windows集成测试跳过。使用新打包器重新生成的ZIP大小及SHA256与上述成品完全一致。验证范围是本轮两个测试文件，不代表全仓Windows测试全部执行。未运行PowerShell、Windows EXE、登录JC或业务读取。

远端在补PNG前：2项依赖PNG的完整验证会明确跳过，打包器直接拒绝缺图。不可将草稿的部分通过当作完整源码交付。

## 补齐原图

在此PR分支，取得本会话已核对的原ZIP后运行：

```text
python scripts/import_reviewed_icon.py --zip <jc-response-setup-0.2.3.zip的路径>
python -m unittest discover -s tests -v
python scripts/pack_setup_skill.py
```

导入只接受固定大小/哈希的ZIP，检查当前文本源并提取唯一缺失的PNG。已有不同图标则停止。不联网、不安装产品、不执行Git命令。核对后将PNG提交到同一PR，并把本文件/README的待补状态改为实际结果。

Git文本归一化为LF，manifest记录原包CRLF文件的恢复方式。压缩环境不同导致整包哈希不一致时停止，不替换既有发布身份。

## Release资产

源码补齐并审阅后，将原ZIP和SHA256SUMS作为独立Skill Release资产分发；不写Git历史，不修改Windows Release。既有标签或资产冲突时停止，不覆盖。实际发布后匿名回下载核对，再更新manifest中的真实URL及发布状态，不编造下载地址。

WorkBuddy使用同一ZIP，后台选择免费并单独上传头像。GitHub发布不代表WorkBuddy审核通过。
