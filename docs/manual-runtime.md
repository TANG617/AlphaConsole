# AlphaConsole Manual Runtime（当前阶段）
## 1. 目标
当前阶段提供的是一个 operator-facing 的 local runtime。  
它允许通过 CLI 手动加载配置、预览 issue，并走完整的 dry-run 或 single-printer hardware publication 链路。

## 2. 当前阶段能力边界
当前阶段可以：
- 从 TOML 加载 publication slots 与 scene apps
- preview scheduled issue
- publish scheduled issue
- publish immediate issue
- 通过新增的 automated runtime commands 触发本地自动出刊
- 通过 printer target 执行真实或 dry-run delivery

当前阶段明确不做：
- USB / CUPS / 蓝牙打印
- 历史存储
- 失败恢复
- scheduler daemon / service manager / cron integration

## 3. CLI 命令面
### 3.1 list
列出配置中的 slot 与 app：

```bash
uv run python -m alphaconsole.cli list --config examples/basic.toml
```

### 3.2 preview scheduled
预览某个 slot 的 scheduled issue，但不 delivery：

```bash
uv run python -m alphaconsole.cli preview scheduled --config examples/basic.toml --slot-id noon
```

### 3.3 publish scheduled
走完整 dry-run publication runtime：

```bash
uv run python -m alphaconsole.cli publish scheduled --config examples/basic.toml --slot-id noon
```

### 3.4 publish immediate
针对某个 app 立即发布独立一期：

```bash
uv run python -m alphaconsole.cli publish immediate --config examples/basic.toml --app-id lunch
```

### 3.5 targets list
列出配置中的 printer targets：

```bash
uv run python -m alphaconsole.cli targets list --config examples/basic.toml
```

### 3.6 targets inspect
查看某个 target 的配置摘要：

```bash
uv run python -m alphaconsole.cli targets inspect --config examples/basic.toml --target-id bytes_debug
```

### 3.7 targets ping
对 socket target 做最小 TCP ping：

```bash
uv run python -m alphaconsole.cli targets ping --config examples/printer-network.toml --target-id receipt_printer
```

### 3.8 print test-page
向选定 target 发送一张最小测试页：

```bash
uv run python -m alphaconsole.cli print test-page --config examples/basic.toml --target-id bytes_debug
```

### 3.9 print calibration
向选定 target 发送 calibration page：

```bash
uv run python -m alphaconsole.cli print calibration --config examples/printer-network.toml --target-id receipt_printer
```

### 3.10 deliveries list / latest
查看最近的 delivery attempts：

```bash
uv run python -m alphaconsole.cli deliveries list --state var/state.db
uv run python -m alphaconsole.cli deliveries latest --state var/state.db
```

### 3.11 runtime once / runtime loop with target
自动出刊命令仍然保留，并可通过 `--target-id` 选择打印目标：

```bash
uv run python -m alphaconsole.cli runtime once --config examples/basic.toml --state var/state.db --target-id bytes_debug
uv run python -m alphaconsole.cli runtime loop --config examples/basic.toml --state var/state.db --target-id receipt_printer
```

## 4. 常用参数
当前阶段建议支持：
- `--config`
- `--profile`
- `--adapter`
- `--target-id`
- `--output-dir`
- `--now`
- `--sequence-of-day`

说明：
- `--profile` 可覆盖配置中的默认 profile
- `--adapter` 可覆盖配置中的默认 adapter
- `--target-id` 可覆盖配置中的默认 printer target
- `--output-dir` 主要用于 `file` adapter
- `--now` 与 `--sequence-of-day` 用于测试和可重复运行

## 5. 当前阶段的边界
manual runtime 只是一个同步可调用的 operator flow。  
它已经可以通过 target 进入第一条 printer hardware delivery 链路，但当前阶段仍然不是多打印机或可靠性 runtime。
manual commands 仍然保留，同时 automated runtime commands 是新增的 operator entrypoints。
