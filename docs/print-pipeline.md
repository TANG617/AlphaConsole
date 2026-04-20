# AlphaConsole 打印边界（当前阶段）
## 1. 目标
当前阶段的目标不是接入真实打印机，而是在 rendering 与未来真实打印系统之间建立一个清晰、稳定的边界。

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

## 3. 当前阶段只做 dry-run delivery
当前阶段只实现 dry-run adapters，例如：
- 内存 adapter
- 文本文件 adapter

当前阶段明确不做：
- ESC/POS
- 真实打印机硬件接入
- 网络 / USB 设备传输
- 图片输出
- bytes-level printer mapping

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

### 5.3 先 dry-run，再真实设备
当前阶段先把接口和 artifact 定义清楚。  
后续如果进入真实打印机接入，应在这条边界之后扩展，而不是回头改动 domain 或 rendering 的核心语义。
