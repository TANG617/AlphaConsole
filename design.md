# Receipt UI Design

## 1. 文档目的

本文件定义 AlphaConsole 当前的小票界面设计、视觉原则、版式系统与后续演进方向。

这份设计文档的目标不只是描述当前已经实现的样式，还要明确系统未来希望接近的风格：

- 像 Linux / UNIX 终端一样有结构感
- 像赛博朋克设备一样有仪式感
- 但必须保留热敏打印场景下的高可读性
- 尤其要保证中文信息在小票上的阅读效率

## 2. 设计目标

### 2.1 功能目标

- 让提醒、日程、checklist 在纸面上看起来像一张来自“终端设备”的操作票据
- 让 TUI 预览、生成的图片、最终打印结果尽量统一
- 让界面系统具备声明式、组件化、可配置的编辑方式

### 2.2 视觉目标

- 像终端，不像普通票据模板
- 像工业设备面板，不像可爱手账
- 像操作系统输出，不像 marketing poster
- 有 retro-futurist 气质，但不过度牺牲阅读性

## 3. 当前设计方向

当前已经落地的风格方向是：

- 黑白高对比
- 顶部反白 header bar
- monospace ASCII emblem
- 状态面板、内容面板、日志面板三段式结构
- 类终端命名方式，例如 `STATUS BLOCK`、`PAYLOAD`、`LOG STREAM`
- body 内容与 meta 内容分层

当前设计不再依赖密集 CRT 扫描线来制造“复古感”。原因是扫描线在热敏打印场景中会明显影响文字辨识，尤其对中文小字影响更大。

## 4. 理想中的 Retro 风格

### 4.1 参考气质

理想风格不是单纯复刻某一个终端，而是来自以下几类视觉的混合：

- Linux boot / diagnostics screen
- BBS / ANSI art 时代的字符界面
- 工业设备自检与维护面板
- cyberdeck / tactical terminal / field device receipt
- 复古 CRT 终端的秩序感，而不是其显示缺陷本身

### 4.2 应保留的 retro 元素

- ASCII/ANSI 风格的字符徽记
- monospace 元信息和状态码
- 面板式分区
- 带标签的 section header
- 操作日志式 footer
- 设备编号、任务编号、状态字段、时间戳
- 明确的边框与分隔线

### 4.3 应避免的 retro 元素

- 过密扫描线
- 过多噪点、故障纹理、失真效果
- 太细的装饰线条
- 太小的等宽字体用于中文正文
- 大面积纯装饰字符，压缩正文空间

### 4.4 理想视觉关键词

- Terminal Receipt
- Retro Ops Console
- Industrial Diagnostics
- Linux Boot Ticket
- Cyberdeck Checklist
- Monochrome Tactical Slip
- BBS Emblem
- Monospace Panel UI

## 5. 中文可读性原则

这是当前系统最重要的现实约束。

### 5.1 原则

- 中文正文永远优先于“终端味”
- 中文正文不应使用过小的 monospace 字体
- 中文正文应使用 CJK 正文字体，不应强行用 ASCII 字体渲染
- meta 信息可以小，但 checklist / title / notes 不能太小

### 5.2 当前规则

- monospace 字体仅用于：
  - header
  - ASCII emblem
  - panel label
  - meta lines
  - footer log
- 中文正文使用 `font_path`
- 当前 body font size 已提升到主题 token 控制，默认值为较大的可读尺寸

### 5.3 后续建议

- checklist 项目字体应继续优先保证大于等于正文
- notes 多行时应自动放大行距，而不是挤压
- 如果正文项较多，应优先分页或拆票，而不是继续缩小字体

## 6. 统一渲染系统

为了让 TUI 预览、图片生成、最终打印统一，当前已经实现了统一的声明式 layout pipeline。

### 6.1 核心思想

系统不再分别维护：

- 一份 ASCII 预览版式
- 一份图片版式
- 一份打印版式

而是先构建一份统一的 `ReceiptScene`，再用不同 renderer 输出到不同介质。

### 6.2 当前结构

当前统一链路如下：

`EntryRecord -> ReceiptScene -> Rich TUI Preview / ASCII CLI Preview / PNG Image -> Printer`

### 6.3 当前核心文件

- `src/alpha_console/layout.py`
  统一的 scene 定义与 receipt scene builder
- `src/alpha_console/render.py`
  scene 到 ASCII / Rich / PIL image 的 renderer
- `src/alpha_console/printer.py`
  scene 预览生成与打印发送
- `src/alpha_console/tui.py`
  Textual 预览界面，使用 Rich renderer 预览同一份 scene
- `alpha_console.toml`
  主题 token 与打印相关配置

## 7. 当前声明式组件模型

当前系统已经引入了类似 GUI 框架的声明式结构：

- `ReceiptScene`
  代表一整张票据
- `SceneSection`
  代表一个带标签的 panel
- `SceneText`
  代表一个有 role 和 align 的文本节点
- `ThemeSettings`
  代表一组可编辑的设计 token

这使得系统更接近现代 GUI / web UI 的设计思路：

- 内容与渲染分离
- 结构与样式分离
- 多 renderer 共享同一份 UI tree

## 8. 当前主题 token

当前主题 token 存在于 `alpha_console.toml` 的 `[theme]` 段中，包括：

- `page_margin_px`
- `section_gap_px`
- `panel_padding_px`
- `preview_width_chars`
- `header_font_size`
- `title_font_size`
- `subtitle_font_size`
- `emblem_font_size`
- `label_font_size`
- `meta_font_size`
- `meta_line_height`
- `body_font_size`
- `body_line_height`
- `footer_font_size`
- `footer_line_height`

这让界面系统已经具备基础的 design-token 能力。

## 9. 当前统一预览能力

### 9.1 CLI 预览

CLI 使用 scene 的 ASCII renderer，适合快速检查内容层级和换行。

### 9.2 TUI 预览

TUI 已切换为 scene 的 Rich renderer，不再只是纯字符串拼接。

当前 TUI 预览具备：

- 同一份 scene 内容
- 同一组 section label
- 同一组 panel 结构
- 同一份信息顺序
- 与打印内容近似一致的白底黑字预览语义

### 9.3 图片与打印

图片与打印使用同一份 scene，并复用同一套布局规则和主题 token。

打印实际上发送的是 scene 渲染后的 PNG，因此：

- 图片布局与打印内容一致
- 打印结果不再依赖另一套单独版式

## 10. 当前仍不完全统一的部分

虽然已经统一为一份 scene，但仍有几处不是绝对一模一样：

- TUI 预览是 Rich terminal renderable，不是真实 bitmap
- CLI 预览是字符宽度模型，不是像素宽度模型
- 图片与打印使用像素级布局，TUI 使用终端字符布局

这意味着当前系统属于：

`single source of truth + multiple faithful renderers`

而不是：

`single bitmap everywhere`

这已经比此前的多套独立版式前进了一大步，但还不是最终形态。

## 11. 理想中的所见即所得目标

理想目标是把当前 scene 系统继续推进到更强的“receipt GUI framework”：

### 11.1 目标形态

- 一个统一的组件树
- 一个统一的布局引擎
- 多 renderer 共享同一套测量规则
- 主题 token 与组件 props 分离
- 所有平台都基于同一份 layout tree 工作

### 11.2 理想能力

- TUI 中看到的结构和打印出的结构几乎完全一致
- 修改主题 token 后立即影响预览与打印
- 修改 section / line / label 后无需改多处代码
- 未来可以接入 Web 编辑器或 GUI 编辑器

### 11.3 更接近现代 Web GUI 框架的方向

未来可以继续把这套系统朝以下方式发展：

- 组件化模板
  例如 `IdentityPanel`、`StatusPanel`、`ChecklistPanel`
- Token-based theme system
  类似 CSS variables / design tokens
- Declarative layout config
  类似 React/Vue/SwiftUI 的数据驱动 UI
- Live preview
  修改 token 后自动刷新 TUI 与 PNG
- Template variants
  如 `retro-terminal`、`ops-diagnostic`、`quiet-minimal`

## 12. 当前推荐的视觉层级

从强到弱应遵循：

1. 任务标题 / checklist 项目
2. 时间与触发信息
3. section label
4. 状态元信息
5. footer 日志
6. ASCII 装饰

也就是说，ASCII 徽记永远不应抢过主要内容。

## 13. 当前推荐的排版规则

- 票据顶部保留强识别 header bar
- emblem 控制在 2-4 行
- payload 区域占用最大空间
- checklist 项目比 meta 字号更大
- footer 日志只做收尾，不应盖过正文
- 不依赖背景纹理制造风格

## 14. 理想中的变体方向

### 14.1 Linux Diagnostics

更偏系统维护、启动检查、机器日志：

- 更强的 panel 结构
- 更少装饰
- 更像 boot log

### 14.2 Cyberdeck Receipt

更偏设备票据、赛博朋克仪式感：

- 更有性格的 emblem
- 更强的任务编号和状态标签
- 仍然坚持大字号正文

### 14.3 Quiet Ops

更克制、更易长期使用：

- 保留终端语言
- 降低装饰比重
- 适合日常计划与 checklist 高频打印

## 15. 当前实现结果总结

本轮实现已经完成以下关键改变：

- 将 TUI 预览、图片生成、打印输出统一到 `ReceiptScene`
- 将设计 token 提取到 `alpha_console.toml`
- 将中文正文与 monospace 元信息分开处理
- 提升正文与 checklist 字体可读性
- 移除依赖扫描线的伪复古做法
- 让系统具备更接近 GUI framework 的声明式结构

## 16. 下一步建议

如果继续推进，这几个方向最值得优先做：

1. 增加多主题切换
2. 增加 live reload / preview reload
3. 增加组件模板库
4. 增加真正的 bitmap preview widget
5. 增加分页与长内容自动拆票

## 17. 基于网络检索的字体与图案候选

以下候选基于 2026-04-18 的公开资料筛选，并结合当前代码中 `font_path` + `mono_font_path` 的双字体结构整理。

当前系统最适合继续保持：

- 一个负责中文正文可读性的 CJK sans
- 一个负责 `header`、`label`、`meta`、`footer`、ASCII emblem 的 monospace

### 17.1 字体首选

#### A. 中文正文首选：`Source Han Sans SC` 或 `Noto Sans SC`

- 这组字体更适合正文、checklist、notes、subtitle。
- `Noto Sans SC` 在 Google Fonts 中提供 `100-900` 的字重轴，并覆盖 `chinese-simplified` 与 Latin。
- Adobe 对 Source Han 系列的说明强调其为 Pan-CJK 开源项目，并提供区域化字形；同时它与 Google 的 Noto 体系互通。
- 它们的气质更中性、稳定、工业化，适合热敏打印的小票正文，不会像 display 黑体那样过分抢戏。

#### B. 中文正文备选：`IBM Plex Sans SC`

- 如果后续希望正文和 meta 在气质上更统一，可以测试 `IBM Plex Sans SC`。
- IBM 官方包提供 `thin` 到 `bold`，外加 `text` weight，比较适合更偏 diagnostics 的变体。
- 但在没有实际打印 A/B 测试前，不建议直接替换掉 `Source Han Sans SC` / `Noto Sans SC` 作为默认正文方案。

#### C. 元信息首选：`IBM Plex Mono`

- IBM 官方说明其 monospace 版本把每个 glyph 控制在 600-unit 空间内，造型取型于 typewriter era。
- 这比当前的 `Menlo` 更接近“设备控制台 / 工业诊断面板”的气质，同时仍然保留良好的数字和英文可读性。
- 最适合 `header`、`panel label`、`meta`、`footer log`、ASCII emblem。

#### D. 仅用于未来实验：`Source Han Mono`

- Adobe 官方说明其由 `Source Han Sans` 与 `Source Code Pro` 派生，覆盖 7 个字重、5 种语言、2 种样式。
- 它只适合未来少量中文等宽状态行、设备代号或双语标签的实验场景。
- 不建议作为当前正文默认，因为文件体积较大，而且本设计已经明确“中文正文不应强行 monospace”。

### 17.2 当前最推荐的字体配对

- 默认生产方案：`Source Han Sans SC` + `IBM Plex Mono`
- 跨平台轻量 fallback：`Noto Sans SC` + `IBM Plex Mono`
- 未来实验方案：`IBM Plex Sans SC` + `IBM Plex Mono`

如果只做一轮替换，最值得先试的是：

- `font_path` -> `Source Han Sans SC`
- `mono_font_path` -> `IBM Plex Mono`

### 17.3 图案首选

图案不应该回到“整页底纹”路线，而应作为 panel 边缘、角标、状态条、预览底板里的低占比结构元素。

结合 Hero Patterns 与 IBM 2x Grid，最合适的是以下几类：

- `Graph Paper`
  - 最适合 TUI / Web preview 的参考网格，或 PNG 预览里的极浅层底板。
  - 它更像工程制图纸，而不是装饰纹理。
  - 不应用在热敏打印的中文正文下方。
- `Steel Beams`
  - 最适合 section corner、header 两端、status block 外沿。
  - 机械感最强，最贴近 `Industrial Diagnostics` 的语义。
- `Tiny Checkers`
  - 最适合 perforation hint、cut mark、footer 尾条、panel 结束条。
  - 小面积使用时比扫描线更稳，也不会明显破坏正文辨识。
- `Diagonal Stripes` / `Rails`
  - 最适合 `warning`、`queued`、`attention`、`offline` 一类状态标记。
  - 应限制为窄条或侧边提示，不应铺满 panel。
- `Circuit Board`
  - 只适合 `Cyberdeck Receipt` 变体的 header 背板、封面式预览或 emblem 背景。
  - 密度偏高，不应进入默认日常打印模板。

### 17.4 图案落地规则

- 图案只应出现在 header、section cap、footer tail、状态条、角标这些低占比区域。
- 中文正文区、checklist 区、notes 区不允许铺图案底纹。
- 预览端的图案应优先按 IBM 2x Grid 的 8px mini unit 对齐。
- 打印端若引入图案，应优先使用 2mm / 4mm 级别的简化模块，而不是灰度噪点或扫描线。
- 所有图案都应优先选择稀疏、可 1-bit 化、可在热敏打印中稳定成形的几何结构。

### 17.5 当前不推荐的方向

- `Topography`
  - 更像地形纹或海报底纹，太有机，不够 terminal。
- `Floating Cogs`
  - 机械隐喻过于直白，容易落入廉价“科技感”。
- `Bank Note`
  - 太像防伪票券，不像操作票据。
- `Jigsaw`
  - 语义偏玩具和拼图，不适合工业终端语境。

### 17.6 来源

- [Google Fonts: Noto Sans SC](https://fonts.google.com/specimen/Noto+Sans+SC)
- [Adobe Source Han Sans 页面](https://source.typekit.com/source-han-sans/)
- [Adobe Source Han Sans GitHub](https://github.com/adobe-fonts/source-han-sans)
- [IBM Design Language: Typeface](https://www.ibm.com/design/language/typography/typeface/)
- [IBM Plex Sans SC package](https://github.com/IBM/plex/tree/master/packages/plex-sans-sc)
- [Adobe Source Han Mono GitHub](https://github.com/adobe-fonts/source-han-mono)
- [IBM Design Language: 2x Grid](https://www.ibm.com/design/language/2x-grid/)
- [Hero Patterns](https://heropatterns.com/)
- [Hero Patterns: Graph Paper](https://heropatterns.com/svg/graph-paper.zip)
- [Hero Patterns: Steel Beams](https://heropatterns.com/svg/steel-beams.zip)
- [Hero Patterns: Tiny Checkers](https://heropatterns.com/svg/tiny-checkers.zip)
- [Hero Patterns: Diagonal Stripes](https://heropatterns.com/svg/diagonal-stripes.zip)
- [Hero Patterns: Rails](https://heropatterns.com/svg/rails.zip)
- [Hero Patterns: Circuit Board](https://heropatterns.com/svg/circuit-board.zip)

## 18. 结论

AlphaConsole 的小票设计不应该只是“做旧”，而应该是一种高可读性的终端票据语言。

它的理想状态是：

- 结构像终端
- 气质像设备
- 阅读像工业文档
- 编辑像现代 GUI 框架

当前系统已经从“多套分散版式”升级到了“统一 scene + 多 renderer”的阶段，这为后续继续做真正的 WYSIWYG receipt UI framework 打下了基础。
