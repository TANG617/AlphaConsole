# AlphaConsole Publication Runtime（当前阶段）
## 1. 目标
当前阶段的目标是在 application 层提供一个同步可调用的 publication runtime，并允许 delivery 边界接入 dry-run 或最小 TCP ESC/POS adapter。

## 2. 运行链路
当前阶段的链路定义为：

```text
SceneApp / ContentApp -> IssueAssembler -> Issue -> PrintService -> RenderedReceipt -> PrinterAdapter
```

说明：
- `IssueAssembler` 负责组刊
- `PrintService` 负责渲染与 delivery
- `PublicationService` 负责把两者串起来

## 3. 正式入口
当前阶段提供两条入口：
- scheduled publication
- immediate publication

两条入口都属于同步调用的 application-level orchestration，不引入后台 runtime。

## 4. 当前阶段支持的 delivery
当前阶段支持：
- 可以组刊
- 可以渲染 receipt
- 可以把 receipt 交给 dry-run adapter
- 可以把 receipt 交给最小 TCP ESC/POS adapter

当前阶段明确不做：
- scheduler
- daemon
- 队列
- USB / Bluetooth printer adapter
- production-grade ESC/POS 队列、重试和恢复

## 5. 当前不定义的语义
以下内容在当前阶段明确不进入：
- 失败恢复
- retry
- 重印
- 历史存储
- 历史查询
- 持久化

如果 adapter 失败，当前阶段允许异常直接向外抛出，不额外发明产品级补偿逻辑。
