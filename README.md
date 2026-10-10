# zxfw-download — 法院电子送达文书下载

从**人民法院在线服务**（zxfw.court.gov.cn）下载法院电子送达文书到本地：

- 传票、起诉状/答辩状、举证通知书、交纳诉讼费用通知书等
- 判决书、裁定书、调解书等裁判文书

本仓库是一个 **Claude Code Skill**：在 Claude Code 里说"帮我下载这条送达短信的文书"即自动执行；也可脱离 Claude Code 直接跑脚本。

## 工作原理

法院送达短信里的链接形如：

```
https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=…&sdbh=…&sdsin=…
```

链接中的 `qdbh` / `sdbh` / `sdsin` 三个参数可直接调接口换回**文书清单和 OSS 预签名下载直链**——**无需登录、无需浏览器**。直链约 1–2 天失效，拿到清单后应立即下载。

## 环境要求

| 依赖 | 说明 |
|---|---|
| Python 3.8+ | 仅用标准库（urllib），无第三方依赖 |

## 安装（Claude Code Skill）

```bash
git clone https://github.com/teamilkman/zxfw-download.git ~/.claude/skills/zxfw-download
```

Windows 路径：`C:\Users\<用户>\.claude\skills\zxfw-download`。也可克隆到项目的 `.claude/skills/` 下，仅对该项目生效。

## 使用

### 方式一：Claude Code 对话（推荐）

安装后把法院送达短信全文直接粘给 Claude，例如：

> 帮我把这条送达短信的文书下载到 D:\案件\送达文书：
> 【人民法院……】…… https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=…&sdbh=…&sdsin=…

Claude 按内置流程执行：解析参数 → 列清单确认 → 下载 → 汇报份数与保存位置。细节见 [SKILL.md](SKILL.md)。

### 方式二：直接跑脚本

```bash
cd ~/.claude/skills/zxfw-download

# 1) 只列清单：确认法院名和文书名
python scripts/download_zxfw.py --list --link "<短信全文或链接>"

# 2) 下载到目标目录
python scripts/download_zxfw.py --link "<短信全文或链接>" --target "<目标目录>"
```

`--link` 接受短信全文或纯链接，脚本用正则自行提取 `qdbh` / `sdbh` / `sdsin`，不需要手工解析。

### 输出

```
<目标目录>/
├── 传票.pdf
├── 举证通知书.pdf
└── 交纳诉讼费用通知书.pdf
```

- 每份文书一个文件，文件名取自送达清单的文书名，自动过滤 Windows 非法字符
- 下载后校验 PDF 文件头（`%PDF`），内容无效会明确报告 FAIL
- 同名同大小的文件自动跳过（可安全重跑）；同名不同内容自动另存 `_2`、`_3`
- 清单里出现「举证通知书」「交纳诉讼费用通知书」等期限文书时，请尽快核对答辩期、举证期、缴费期限

## 说明

- `qdbh` / `sdbh` / `sdsin` 每案每批都不同，必须用当次短信里的链接现取，不要复用旧参数
- 直链有时效，接口偶发瞬时失败：报签名失效或下载失败时先原样重跑一次；仍失败请重新打开原链接确认是否过期
- 仅适用于 zxfw.court.gov.cn（人民法院在线服务全国版），各省法院小程序等其他平台的送达链接不适用
