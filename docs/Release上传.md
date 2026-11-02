# 上传已审核的 Windows 预发布资产

本轮用户已授权上传 r1。公开仓提交不等于二进制上传；当前状态以 distribution.json 和 GitHub Releases 实际资产为准。不要重编译或重打包，不改变下述文件身份。

- 仓库：bobbanga/jc-response
- 标签：v1.2.0-r1
- 标题：JC Response 1.2.0-r1 — Windows 候选预发布
- ZIP：JC_response-windows-x64-1.2.0-r1.zip
- 字节数：122270089
- SHA256：91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713

## 执行

1. 使用本机已登录的 GitHub CLI 或 GitHub 网页。没有认证时由本人通过正常登录完成，不能索取、输出或复制 Token。先检查同标签 Release 和标签；读取失败不能当成不存在。同名资产相同则复用，不同则停止，不使用 --clobber，不移动已经发布的标签。
2. 核对本地 ZIP 大小、外部 SHA256 和内部清单，生成一份外部 .sha256 文件。二进制不能进入 Git 历史，不能拆块或 Base64 变相提交。
3. 读取实际已审阅的公开提交作为标签目标，记下完整 SHA；标签指向公开分发资料，不是私有二进制构建源码。使用 PUBLIC_RELEASE_NOTES.md，先创建 draft + prerelease 并附加 ZIP 与 .sha256。以下变量由前述检查确定，不盲填：

```powershell
gh release create v1.2.0-r1 $Zip $Checksum --repo bobbanga/jc-response --target $ReviewedCommit --draft --prerelease --latest=false --title 'JC Response 1.2.0-r1 — Windows 候选预发布' --notes-file $Notes
```

4. 将 draft 资产下载到新临时目录，重新检查字节数和哈希。失败保留草稿并报告，不发布半成品，不删除或覆盖已有发布物。
5. 资产验证成功后才公开为 prerelease，不设为稳定版或 latest：

```powershell
gh release edit v1.2.0-r1 --repo bobbanga/jc-response --draft=false --prerelease --latest=false
```

6. 从 GitHub 实际返回取得 release_url 和 browser_download_url。用不带认证的公开下载再次核对文件，下载成功且哈希匹配才称发布完成。
7. 更新外部 distribution.json 为 prerelease_published，写入真实 URL、验证时间和方式；更新 README 的上传状态。不要改 ZIP 或其内置 candidate/NOT_RUN 元数据，用外部发布/验收记录补充。只提交本轮明确文件，不顺带推送本机未审阅的站点分支。

## 网页备用

维护者通过仓库 Releases 创建草稿，选择上述固定标签和已审阅公开提交，勾选预发布，附加两份文件并粘贴发布正文。核对无误后发布，再下载验证。普通用户无需构建或克隆源代码。

当前 upload_pending 表示尚未完成上传，不是可用下载地址。没有真实资产时不能将市场新用户下载流程记为 PASS。

官方命令参考：
- https://cli.github.com/manual/gh_release_create
- https://cli.github.com/manual/gh_release_upload
- https://cli.github.com/manual/gh_release_download
- https://cli.github.com/manual/gh_release_edit
