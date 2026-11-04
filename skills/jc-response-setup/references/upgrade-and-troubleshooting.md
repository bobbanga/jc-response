# 升级与排障

先定位失败的一层，再处理这一层。

| 现象 | 处理 |
|---|---|
| 没有程序目录 | 用户同意后新装。下载地址为空且没有锁定哈希一致的本地包时停止 |
| 版本、契约、`csv_schema`、三个 EXE 和校验清单都匹配 | 复用，不下载、不覆盖 |
| 版本、契约、`csv_schema` 和三个 EXE 都与已审核的 v1.2.0-r1 一致 | 用户同意后调用现有安装器升级。只看到 `1.2.0` 不能升级 |
| 本机 `csv_schema` 不是 `JC_response_business/1.0` | 旧包只能输出技术表 `JC_response/1.1`。`response_flow/1.1` 不能当成中文导出已满足 |
| 同版本但二进制不同 | 按已验证安装器升级，不能只看版本号 |
| 二进制相同，只有说明或 Skill 不同 | 九项资料白名单刷新 |
| 下载地址为空且本地包哈希不符、更高版本、来源不明、目录混杂或配置冲突 | 停止，不降级、不卸载、不删除、不手工替换 EXE |

脚本动作只有 `inspect`、`install`、`refresh-docs`、`configure`。写文件的动作必须带 `-Confirm`。没有确认时只给出变更摘要：目标版本、大小、来源、未签名、目标目录、是否改配置。

产品命令只有两条：

```text
<已验证解压目录>\bin\JC_response.exe --install-user --json
%LOCALAPPDATA%\Programs\JC_response\bin\JC_response.exe --configure-workbuddy --json
```

不通过 PATH 找程序，不进入开发仓库，不读取 `.env`、Token 或业务数据库。

安装成功必须同时看到退出码 0、接受的 JSON status，以及正式目录里的版本、契约和 EXE 哈希。`changed=false` 或单独一个 `already_installed` 都不等于升级完成。`conflict`、`target_in_use`、`target_has_data`、`install_required` 和未知状态都停止。

文件被占用或权限不足时停止。不结束 WorkBuddy，不提权。请用户保存任务并正常停用目标连接；当时不能释放就记下待释放，用户重启后再核验。

范围开通、登录、退出、提额和清零不是安装命令。需要时可以打开已核验的 `JC_response.exe` 无参数界面，由本人操作。业务阶段已经连上 MCP 时，按业务规则从对话发起登录。密码和验证码只在 JC 页面输入。

配置只检查用户级 `%USERPROFILE%\.workbuddy\mcp.json`。目标是正式目录中的 `jctrans-mcp.exe`、stdio、空参数。其他 MCP 和顶层字段必须保留。同名内容不同、另一处还有 `jc-response`、文件损坏或写入期间发生变化，都停止，不用整份备份覆盖。

Cursor 可以代做本机安装，但不能把 Cursor 的配置写成 WorkBuddy 已接入。
