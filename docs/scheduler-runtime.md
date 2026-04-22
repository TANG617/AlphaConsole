# AlphaConsole Scheduler Runtime（当前阶段）
## 1. 目标
当前阶段引入的是一个本地、同步、轮询式 scheduler runtime。  
它的目标是在保持本地与保守语义的前提下，让系统能够自动出刊并交付到 dry-run 或单台真实 printer target。

## 2. 当前只支持每日固定时点
当前自动化 runtime 对 `PublicationSlot` 的解释固定为：
- enabled slot
- 每天在 `publish_time` 触发一次

`recurrence_rule` 当前阶段不做完整解释。  
当前阶段只允许：
- `None`
- `"daily"`

其他值应在 config compile 阶段明确报错。

## 3. due window 计算
### 3.1 subsequent tick
如果 store 中已有 `last_tick_at`：
- 窗口为 `(last_tick_at, now]`

### 3.2 first tick / cold start
如果 store 中没有 `last_tick_at`：
- 窗口为 `(now - catchup_seconds, now]`

默认：
- `catchup_seconds = 60`

含义：
- 允许处理极短时间内错过的 slot
- 不做大范围历史 backfill
- 不补发很久以前的刊次

## 4. loop 模式
当前阶段的 `runtime loop`：
- 只做本地 polling
- 默认同步循环
- 不做 daemon
- 不做 service manager
- 不做 cron integration
- 可把 due issue 交给默认 target 或 `--target-id` 指定 target

## 5. 失败语义
当前阶段 delivery failure 的语义固定为：
1. 记录 `delivery_attempt`
2. `publication_run` 标记为 `delivery_failed`
3. 异常继续 bubble up
4. 不 retry
5. 不 recovery
6. 不补打

## 6. dedupe 语义
当前阶段 scheduled occurrence 通过 `(slot_id, occurrence_at)` 去重。  
如果某次 scheduled occurrence 已经在 ledger 中出现，则后续 tick 不应再次自动发布。

## 7. 当前阶段不做
- daemon / service manager
- 历史 backfill
- retry / recovery
- 多打印机编排
- printer discovery
