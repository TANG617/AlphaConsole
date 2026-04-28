# AlphaConsole 打印边界（当前阶段）
## 1. 目标
当前阶段的目标是在 rendering 与 delivery 之间建立一个清晰、稳定的边界，并补入最小 TCP ESC/POS adapter。

## 2. 边界链路
当前阶段的链路定义为：

```text
Issue -> render_issue(profile) -> RenderedReceipt -> PrinterAdapter
```

说明：
- `Issue` 仍然是 domain 层对象
- `render_issue(profile)` 仍然属于 rendering 层
- `RenderedReceipt` 是 rendering -> printing 的边界 artifact
- `PrinterAdapter` 属于 printing / application boundary

## 3. 当前阶段支持的 delivery
当前阶段实现 dry-run adapters，例如：
- 内存 adapter
- 文本文件 adapter

同时提供一个最小 TCP ESC/POS adapter：
- 通过打印机 IP 与 9100 端口发送 raw ESC/POS bytes
- 默认使用 `gb18030` 编码，适配常见中文小票机
- 默认发送初始化、中文模式、文本、走纸、切纸命令

当前阶段明确不做：
- USB / Bluetooth 设备传输
- 图片输出
- bytes-level printer mapping
- 产品级打印队列、重试和恢复

## 4. 当前不定义的语义
以下内容在当前阶段明确不进入：
- 产品级失败恢复
- retry
- 队列
- 补打
- 重印
- 持久化
- 历史查询

如果 adapter 失败，当前阶段允许异常直接向外抛出，不额外发明产品语义。

## 5. 设计原则
### 5.1 Rendering 与 delivery 分离
rendering 负责把 `Issue` 变成稳定文本；printing boundary 负责把已经渲染好的文本交给某个 adapter。

### 5.2 Domain 不承载 printing 状态
不要把 printing 对象、打印状态或交付历史塞进 `Issue`、`Block` 或 `ContentApp`。

### 5.3 先稳定边界，再扩展设备
当前阶段先把接口和 artifact 定义清楚。  
后续如果继续扩展打印机接入，应在这条边界之后扩展，而不是回头改动 domain 或 rendering 的核心语义。
