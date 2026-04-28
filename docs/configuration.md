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

[delivery.escpos_tcp]
host = "10.0.4.192"
port = 9100
timeout_seconds = 5
encoding = "gb18030"
cut = true
feed_lines = 3

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
    - `escpos-tcp`
- `file.output_dir`
  - 可选
  - 当 default adapter 为 `file` 时必须存在
- `escpos_tcp.host`
  - 可选
  - 当 default adapter 为 `escpos-tcp` 时必须存在
- `escpos_tcp.port`
  - 默认值：`9100`
- `escpos_tcp.timeout_seconds`
  - 默认值：`5`
- `escpos_tcp.encoding`
  - 默认值：`gb18030`
- `escpos_tcp.cut`
  - 默认值：`true`
- `escpos_tcp.feed_lines`
  - 默认值：`3`

### 4.3 runtime
- `catchup_seconds`
  - 默认值：`60`
- `poll_interval_seconds`
  - 默认值：`30`
- 当前阶段只用于本地 automation runtime
- 当前阶段不扩张为复杂 scheduler config

### 4.4 publication_slots
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

### 4.5 scene_apps
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
- `default_adapter = "escpos-tcp"` 时必须给出 `delivery.escpos_tcp.host`
- `recurrence_rule` 当前阶段不支持复杂解释，slot 只允许 `None` 或 `"daily"`

## 6. 当前明确不支持
- weather/news app 配置
- 历史配置
- queue 配置
- retry 配置
- USB / Bluetooth printer device 配置
- 多 profile fallback
- 多 adapter routing 规则
- 复杂 recurrence engine
- scheduler daemon / cron integration

## 7. 说明
当前阶段配置只是从 config 世界进入 domain/application 世界的最小桥接层。  
它不是最终产品级 schema，也不应该反向污染 domain 对象设计。
