# AlphaConsole Printer Profiles（当前阶段）
## 1. 目标
当前阶段引入 `PrinterProfile`，把设备侧的纸宽、可打印宽度与默认参数从 target config 中抽离出来。

## 2. 当前内建 profile
当前阶段至少提供：
- `generic_58mm`
- `generic_80mm`

## 3. 典型字段
- `profile_id`
- `paper_width_mm`
- `printable_width_dots`
- `horizontal_padding_dots`
- `line_feed_after_print`
- `supports_cut`
- `default_cut`
- `default_font_size`
- `default_line_spacing`
- `recommended_render_profile_name`

## 4. render profile 与 printer profile 的关系
- `PrinterProfile` 负责设备侧宽度与默认参数
- `RenderProfile` 负责文本列宽与换行
- 二者不要混成一个概念

当前阶段规则：
- target 未显式指定 `render_profile` 时，可回退到 `PrinterProfile.recommended_render_profile_name`
- 当前阶段不做 capability auto-detection

## 5. 当前不做
- 动态纸宽探测
- 多打印机 profile negotiation
- 自动 profile fallback
