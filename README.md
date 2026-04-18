# Local Console MVP

这是一个不依赖 AI 的本地 MVP，用来先跑通这条链路：

- 手动录入日程或 checklist
- 写入本地 SQLite
- 后台 worker 轮询到期任务
- 渲染字符预览和位图小票
- 发送到网络 ESC/POS 打印机

当前默认打印机地址是 `10.0.4.192:9100`，可以通过环境变量覆盖。
当前默认有效打印宽度是 `576px`，对应 72mm 打印宽度在 203DPI 下的常见点数。
项目内已保存打印机配置：`./alpha_console.toml`
界面与排版设计说明见：`./design.md`

## 1. 环境准备

```bash
~/.local/bin/uv sync
```

## 2. 初始化

```bash
~/.local/bin/uv run alpha-console init
~/.local/bin/uv run alpha-console doctor
```

## 3. 创建提醒

创建单条日程：

```bash
~/.local/bin/uv run alpha-console add-event \
  --title "给客户发报价" \
  --due-at "2026-04-18 18:30" \
  --notes "附上最新版 PDF"
```

创建 checklist：

```bash
~/.local/bin/uv run alpha-console add-checklist \
  --title "出门前检查" \
  --due-at "2026-04-18 18:35" \
  --item "钥匙" \
  --item "耳机" \
  --item "水杯" \
  --item "雨伞"
```

创建一个 30 秒后触发的演示任务：

```bash
~/.local/bin/uv run alpha-console demo --delay-seconds 30
```

## 4. 启动 worker

真实打印：

```bash
~/.local/bin/uv run alpha-console worker
```

仅渲染预览，不发往打印机：

```bash
~/.local/bin/uv run alpha-console worker --dry-run
```

## 5. 查看和预览

查看任务：

```bash
~/.local/bin/uv run alpha-console list
```

查看某条任务的字符预览和小票图片：

```bash
~/.local/bin/uv run alpha-console preview 1
```

立即打印某条任务：

```bash
~/.local/bin/uv run alpha-console print-now 1
```

打印一张真实纸宽校准票：

```bash
~/.local/bin/uv run alpha-console calibrate-print
```

## 6. Textual 面板

```bash
~/.local/bin/uv run alpha-console tui
```

面板支持：

- 查看当前任务队列
- 在本地快速新增 event 或 checklist
- 生成字符预览
- 手动立即打印

## 7. 运行数据

默认运行数据位于：

- 数据库：`./var/alpha_console.db`
- 图片预览：`./var/previews/`

可用环境变量：

- `ALPHA_CONSOLE_PRINTER_HOST`
- `ALPHA_CONSOLE_PRINTER_PORT`
- `ALPHA_CONSOLE_PRINTER_WIDTH`
- `ALPHA_CONSOLE_PRINTER_TIMEOUT`
- `ALPHA_CONSOLE_DB_PATH`
- `ALPHA_CONSOLE_DATA_DIR`
- `ALPHA_CONSOLE_FONT_PATH`
- `ALPHA_CONSOLE_MONO_FONT_PATH`

默认会先读取项目根目录的 `alpha_console.toml`，环境变量会覆盖配置文件中的同名项。

当前界面系统已经统一为：

- `ReceiptScene`：单一内容源
- `Rich TUI Preview`：终端预览
- `PNG Image`：图片与打印源
- `ThemeSettings`：可编辑主题 token

校准纸宽时，可以临时覆盖默认宽度，例如：

```bash
ALPHA_CONSOLE_PRINTER_WIDTH=360 ~/.local/bin/uv run alpha-console calibrate-print
```
