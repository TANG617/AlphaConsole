# AlphaConsole Hardware Delivery（当前阶段）
## 1. 目标
当前阶段把 dry-run print boundary 推进到第一条真实打印链路，但仍然保持本地、保守、单机优先。

## 2. 当前阶段链路
当前阶段允许的最小链路为：

`Issue -> RenderedReceipt -> RasterizedReceipt -> EscPosPayload -> PrinterAdapter`

其中：
- `PrintService` 负责：
  - `Issue -> RenderedReceipt`
  - `RenderedReceipt -> PrinterAdapter`
- 硬件 adapter 负责：
  - text -> image
  - image -> ESC/POS bytes
  - bytes -> transport

## 3. 当前支持的真实路径
当前阶段至少支持：
- `escpos_socket`

同时保留：
- `stdout`
- `file`
- `memory`
- `escpos_bytes_file`

## 4. diagnostics
当前阶段允许为一次 delivery 记录最小 diagnostics，例如：
- target id
- printer profile
- render profile
- bytes length
- duration
- success / error

这些信息用于：
- operator 联调
- calibration 对比
- 失败定位

这些信息不用于：
- 自动 retry
- resend
- recovery
- 补打

## 5. 失败语义
当前阶段 delivery failure 仍然保持保守：
1. 记录 `delivery_attempt`
2. `publication_run` 标记为 `delivery_failed`
3. 异常 bubble up
4. 不 retry
5. 不 recovery
6. 不补打

## 6. 当前阶段不做
- USB / CUPS / 蓝牙 transport
- printer capability negotiation
- 多打印机路由
- queue / daemon / background service
