# AlphaConsole 配置格式（当前阶段）
## 1. 目标
当前阶段的目标不是定义最终产品级 schema，而是提供一个简单、稳定、适合人工编辑的 TOML 配置格式。

## 2. 当前阶段技术约束
- 使用 stdlib `tomllib`
- 不引入 YAML 或第三方配置框架
- 当前阶段只覆盖：
  - publication slots
  - scene apps
  - default render profile
  - default dry-run adapter kind
  - runtime defaults
  - printer target config
  - printer profiles / calibration defaults

## 3. 推荐配置结构
```toml
[rendering]
default_profile = "receipt42"

[runtime]
catchup_seconds = 60
poll_interval_seconds = 30

[delivery]
default_adapter = "stdout"

[delivery.file]
output_dir = "var/out"

[printing]
default_target = "stdout_default"

[[printer_targets]]
target_id = "stdout_default"
kind = "stdout"
printer_profile = "generic_58mm"
render_profile = "receipt32"

[[printer_targets]]
target_id = "bytes_debug"
kind = "escpos_bytes_file"
output_dir = "var/escpos"
mode = "raster"
printer_profile = "generic_58mm"
render_profile = "receipt32"
font_path = ""
font_size = 18
line_spacing = 4
cut = true
feed_lines = 4

[[publication_slots]]
slot_id = "morning"
name = "Morning"
publish_time = "07:00"
is_enabled = true

[[publication_slots]]
slot_id = "noon"
name = "Noon"
publish_time = "12:00"
is_enabled = true

[[scene_apps]]
app_id = "lunch"
name = "Lunch"
target_publication_slot_id = "noon"
scene_note = "多吃蔬菜，不要喝可乐"
checklist_items = ["吃得健康", "力量训练", "21:00 结束工作"]
is_enabled = true
```

## 4. 当前支持的配置项
### 4.1 rendering
- `default_profile`
  - 当前阶段建议值：
    - `receipt32`
    - `receipt42`

### 4.2 delivery
- `default_adapter`
  - 当前阶段建议值：
    - `stdout`
    - `file`
    - `memory`
- `file.output_dir`
  - 可选
  - 当 default adapter 为 `file` 时必须存在

### 4.3 printing
- `default_target`
  - 可选
  - 若给出，必须指向一个存在的 `printer_targets.target_id`

### 4.4 printer_targets
每个 target 当前支持：
- `target_id`
- `kind`
  - 当前阶段只允许：
    - `stdout`
    - `file`
    - `memory`
    - `escpos_socket`
  - `escpos_bytes_file`
- `printer_profile`（可选）
  - 当前阶段内建：
    - `generic_58mm`
    - `generic_80mm`
- `render_profile`（可选）
- `mode`（可选）
  - 当前阶段只允许：
    - `raster`
- `font_path`（可选，空字符串按 `None` 处理）
- `font_size`（可选）
- `line_spacing`（可选）
- `cut`（可选）
- `feed_lines`（可选）
- `host` / `port`
  - `escpos_socket` 必填
- `output_dir`
  - `file` 与 `escpos_bytes_file` 必填

### 4.5 runtime
- `catchup_seconds`
  - 默认值：`60`
- `poll_interval_seconds`
  - 默认值：`30`
- 当前阶段只用于本地 automation runtime
- 当前阶段不扩张为复杂 scheduler config

### 4.6 publication_slots
每个 slot 当前支持：
- `slot_id`
- `name`
- `publish_time`
- `is_enabled`
- `description`（可选）
- `recurrence_rule`（可选）
  - 当前阶段只允许：
    - `None`
    - `"daily"`

### 4.7 scene_apps
每个 scene app 当前支持：
- `app_id`
- `name`
- `target_publication_slot_id`
- `scene_note`（可选，空字符串按无 note 处理）
- `checklist_items`（可选）
- `is_enabled`
- `description`（可选）
- `scene_description`（可选）
- `recurrence_rule`（可选，占位）

## 5. 当前阶段校验原则
- 必填字段缺失时，loader 应抛出清晰异常
- `publish_time` 必须是可解析的时间字符串
- 不支持未知 app 类型
- `scene_note` 与 `checklist_items` 不能同时为空
- default profile / adapter 必须落在当前支持范围内
- `default_adapter = "file"` 时必须给出 `delivery.file.output_dir`
- `printing.default_target` 若存在，必须引用已定义 target
- `printer_profile` 若给出，必须是当前支持的内建 profile
- `escpos_socket` 必须给出 `host` 与 `port`
- `file` / `escpos_bytes_file` target 必须给出 `output_dir`
- `mode` 当前只允许 `raster`
- `recurrence_rule` 当前阶段不支持复杂解释，slot 只允许 `None` 或 `"daily"`

## 6. 当前明确不支持
- weather/news app 配置
- 历史配置
- queue 配置
- retry 配置
- 多 profile fallback
- 多 adapter routing 规则
- 复杂 recurrence engine
- scheduler daemon / cron integration
- USB / CUPS / 蓝牙 target
- printer discovery / capability negotiation
- 多打印机路由与多 target 调度

## 7. 说明
当前阶段配置只是从 config 世界进入 domain/application 世界的最小桥接层。  
它不是最终产品级 schema，也不应该反向污染 domain 对象设计。
当前阶段的 printer target 配置也是 operator-facing config，不是最终产品级 device schema。
