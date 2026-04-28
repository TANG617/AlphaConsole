# AlphaConsole Printer Targets（当前阶段）
## 1. 目标
当前阶段引入 printer target config，用来把 operator-facing 配置与具体 delivery adapter 连接起来。

## 2. 当前支持的 target kind
当前阶段只支持：
- `stdout`
- `file`
- `memory`
- `escpos_socket`
- `escpos_bytes_file`

## 3. 推荐配置结构
```toml
[printing]
default_target = "receipt_printer"

[[printer_targets]]
target_id = "receipt_printer"
kind = "escpos_socket"
printer_profile = "generic_58mm"
render_profile = "receipt32"
host = "192.168.1.50"
port = 9100
timeout_seconds = 5.0
mode = "raster"
font_path = "/path/to/font.ttf"
font_size = 18
line_spacing = 4
cut = true
feed_lines = 4

[[printer_targets]]
target_id = "bytes_debug"
kind = "escpos_bytes_file"
output_dir = "var/escpos"
printer_profile = "generic_58mm"
render_profile = "receipt32"
mode = "raster"
font_path = ""
font_size = 18
line_spacing = 4
cut = true
feed_lines = 4
```

## 4. 字段说明
### 4.1 公共字段
- `target_id`
- `kind`
- `printer_profile`
- `render_profile`
- `mode`
- `font_path`
- `font_size`
- `line_spacing`
- `cut`
- `feed_lines`

### 4.2 `escpos_socket`
必填：
- `host`
- `port`

可选：
- `timeout_seconds`

### 4.3 `escpos_bytes_file`
必填：
- `output_dir`

### 4.4 `file`
必填：
- `output_dir`

## 5. 当前阶段规则
- 当前阶段 `mode` 只允许 `raster`
- blank `font_path` 归一化为 `None`
- 未显式给出 `render_profile` 时，可回退到 `PrinterProfile` 推荐值
- target config 属于 operator/runtime/printing boundary，不属于 domain
- 当前阶段只对单台默认打印机负责，不做多打印机编排

## 6. 当前不做
- USB / CUPS / 蓝牙 target
- printer discovery
- capability auto-detection
- 多 target 路由策略
