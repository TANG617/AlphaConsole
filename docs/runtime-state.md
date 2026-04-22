# AlphaConsole Runtime State（当前阶段）
## 1. 目标
当前阶段使用 SQLite 保存本地 runtime state 与最小 ledger。  
它的目标不是成为完整数据库层，而是为自动化 dry-run runtime 提供可恢复重启的最小状态。

## 2. Config 与 State 的边界
当前阶段固定为：
- `*.toml`：声明式配置
- `state.db`：运行态状态

规则：
1. 不要把 publication slots / scene apps 的定义写进 SQLite
2. 不要把运行态记录写回 TOML
3. SQLite 只保存 runtime state 与 ledger

## 3. 当前阶段建议表
### 3.1 runtime_meta
保存小型 checkpoint，例如：
- `last_tick_at`

### 3.2 daily_sequence_counters
保存每天的 sequence allocator。  
每天从 `1` 开始递增。

### 3.3 publication_runs
保存每次 scheduled automated publication 的最小 ledger 记录。

当前阶段建议状态：
- `assembled`
- `delivered`
- `delivery_failed`

### 3.4 delivery_attempts
保存每次 delivery 尝试。
当前阶段既可能记录 dry-run adapters，也可能记录真实硬件路径：
- `stdout`
- `file`
- `memory`
- `escpos_socket`
- `escpos_bytes_file`

## 4. 技术约束
- 使用 stdlib `sqlite3`
- 时间统一存 ISO 8601 文本
- datetimes 保持当前仓库使用的 naive datetime 风格
- 初始化连接后启用：
  - `PRAGMA foreign_keys = ON;`

## 5. 当前不做
- ORM
- migrations framework
- connection pool
- 历史查询 UI
- retry / recovery
- reprint
- 设备能力探测
