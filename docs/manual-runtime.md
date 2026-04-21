# AlphaConsole Manual Runtime（当前阶段）
## 1. 目标
当前阶段提供的是一个 operator-facing 的 dry-run runtime。  
它允许通过 CLI 手动加载配置、预览 issue，并走完整的 dry-run publication 链路。

## 2. 当前阶段只做 dry-run
当前阶段可以：
- 从 TOML 加载 publication slots 与 scene apps
- preview scheduled issue
- publish scheduled issue
- publish immediate issue

当前阶段明确不做：
- scheduler
- daemon / cron
- ESC/POS
- 真实打印机硬件接入
- 历史存储
- 失败恢复

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

## 4. 常用参数
当前阶段建议支持：
- `--config`
- `--profile`
- `--adapter`
- `--output-dir`
- `--now`
- `--sequence-of-day`

说明：
- `--profile` 可覆盖配置中的默认 profile
- `--adapter` 可覆盖配置中的默认 adapter
- `--output-dir` 主要用于 `file` adapter
- `--now` 与 `--sequence-of-day` 用于测试和可重复运行

## 5. 当前阶段的边界
manual runtime 只是一个同步可调用的 operator flow。  
它不是 scheduler-facing runtime，也不是 printer hardware runtime，更不是 persistence milestone。
