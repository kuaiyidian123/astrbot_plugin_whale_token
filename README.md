# astrbot_plugin_whale_token · 鲸元券

AstrBot 插件：在聊天中查看虚构货币「鲸元券（WHALE-YUAN TOKEN）」的六档票面图。

票面素材来自视觉设计项目 [DeepSeek-Token-Bank](https://github.com/Huaji124/DeepSeek-Token-Bank)，
本插件把它打包成聊天里可直接发送的图片：**预压缩、无需联网、无第三方依赖**。

![示例：1 亿券正面](resources/front_100000000.jpg)

## 功能

- 按面额返回票面图，六档全覆盖（1 千万 / 2 千万 / 5 千万 / 1 亿 / 2 亿 / 5 亿）
- 支持正面 / 反面 / 正反双面
- 面额支持多种写法：`1亿`、`一亿`、`壹億`、`100000000`、`100,000,000`、`5000万`
- 可发送全系列总表长图
- 默认面额与默认票面可在 AstrBot 后台插件配置页调整，用户无需输入参数

## 安装

方式一：AstrBot 后台「插件市场」搜索安装（若已收录）。

方式二：手动安装 —— 把 `astrbot_plugin_whale_token` 整个目录放进 AstrBot 的 `data/plugins/`，
然后在后台重载插件。本插件无第三方依赖，不需要安装额外 pip 包。

## 指令

| 指令 | 说明 |
| --- | --- |
| `/鲸元券` | 按后台配置的默认面额 / 默认票面发送 |
| `/鲸元券 <面额>` | 发送指定面额的正面，如 `/鲸元券 1亿` |
| `/鲸元券 反面 <面额>` | 发送反面 |
| `/鲸元券 双面 <面额>` | 正反两面一起发 |
| `/鲸元券 列表` | 六档面额一览 |
| `/鲸元券 全系列` | 全系列总表长图 |
| `/鲸元券 随机` | 随机抽一档 |
| `/鲸元券 帮助` | 用法说明 |

指令别名：`/词元券`、`/鲸元`

## 配置

在 AstrBot 后台的插件配置页调整：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| 默认面额 | `random` | 不带参数时使用的面额。可填 `1亿` / `5000万` / `100000000` 等，填 `random` 每次随机 |
| 默认票面 | `front` | 不带参数时发哪一面：`front` / `back` / `both`，也接受 `正面` / `反面` / `双面` |
| 图片后附带票面信息 | 开 | 发送图片后是否再发一条文字说明（主题、券幅、专色等） |
| 允许发送全系列总表 | 开 | 是否允许 `/鲸元券 全系列` |

## 面额一览

| 面额（TOKEN） | 主题 | 券幅（mm） | 专色 |
| --- | --- | --- | --- |
| 10,000,000 | 引航 | 132.0 × 61.6 | #24506B 深青蓝 |
| 20,000,000 | 夜航 | 142.0 × 66.3 | #1F5A52 深海绿 |
| 50,000,000 | 港市 | 148.0 × 69.0 | #4A3A6E 紫罗兰 |
| 100,000,000 | 守望 | 150.0 × 70.0 | #1B2657 藏青 |
| 200,000,000 | 星图 | 158.0 × 73.7 | #8A5A2B 赭金 |
| 500,000,000 | 远洋 | 176.0 × 82.1 | #2E2717 玄金 |

## 目录结构

```
astrbot_plugin_whale_token/
├─ main.py                插件主逻辑
├─ metadata.yaml          插件元信息
├─ _conf_schema.json      后台配置项定义
├─ resources/             13 张预压缩图（6 档 × 正反 + 全系列总表），约 3MB
├─ tests/test_pure_logic.py   纯逻辑测试
└─ tools/build_resources.ps1  重新生成图片的脚本
```

## 重新生成图片

`resources/` 由 `tools/build_resources.ps1` 从 DeepSeek-Token-Bank 仓库的 `dist/png/*.png`
（7560×3528 原图）按各档真实券幅等比缩放生成。脚本只依赖 Windows PowerShell 5 与 .NET
`System.Drawing`，**不需要 Pillow，也不需要联网**。

使用前请先克隆原项目，并保持 `astrbot_plugin_whale_token` 与 `DeepSeek-Token-Bank`
处于同一父目录下（脚本按相对路径取源图），然后运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\build_resources.ps1
```

## 测试

```bash
python tests/test_pure_logic.py
```

测试覆盖面额解析（含中文/大写/带分隔符写法）、指令参数切分、资源文件对应关系与后台配置解析，
不依赖 AstrBot 运行时（缺失时自动注入 stub）。

## 声明

- 「鲸元券」为**虚构设定物**，非真实货币，不具有任何法定清偿效力。
- 票面所用的 DeepSeek 鲸鱼标识是 **DeepSeek 的商标与品牌资产**，其著作权与商标权均不属于本项目；
  本项目与 DeepSeek 官方**没有任何隶属、合作、赞助或背书关系**。
- 票面素材来自 [DeepSeek-Token-Bank](https://github.com/Huaji124/DeepSeek-Token-Bank)，
  该项目的图稿与文档以 **CC BY-NC 4.0（署名-非商业性使用）** 授权。因此本插件**仅限非商业用途**。
