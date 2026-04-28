# AlphaConsole 代码契约
## 1. 目的
本文件定义当前阶段允许进入代码层的抽象契约。  
它不是最终实现，但 Codex 应以此为代码骨架的唯一参考。

## 2. 总约束
1. 文档语义优先于代码便利性。
2. 当前只允许构建域模型、组刊器、width-aware rendering、dry-run print boundary、publication runtime、manual runtime 与 local automation runtime，不要实现外围系统。
3. 不要创建一个单独的 `Scene` 类来混合配置与快照语义。
4. 代码中使用 `ContentApp` 代表产品概念中的 App。
5. 一个 `ContentApp` 在一次 `Issue` 中最多返回一个 `Block`。

## 3. 枚举定义
建议最小枚举如下：

```python
from enum import StrEnum


class TriggerMode(StrEnum):
    SCHEDULED = "scheduled"
    IMMEDIATE = "immediate"


class MergePolicy(StrEnum):
    MERGEABLE = "mergeable"
    STANDALONE = "standalone"
```

说明：
- `TriggerMode` 只表达本次实际发行方式
- “外部系统触发但安排到未来刊次”最终仍属于 scheduled
- “外部系统触发并立刻打印”属于 immediate

## 4. 运行时上下文对象
建议定义一个轻量上下文对象，供 App 在发布 Block 时使用。

```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class IssueBuildContext:
    issue_id: str
    issue_date: date
    issued_at: datetime
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    sequence_of_day: int
```

说明：
- 这是运行时对象，不是 PRD 的一级产品对象
- 仅用于一次组刊过程中的参数传递

## 5. PublicationSlot
```python
from dataclasses import dataclass
from datetime import datetime, time


@dataclass(slots=True)
class PublicationSlot:
    slot_id: str
    name: str
    description: str | None
    publish_time: time
    recurrence_rule: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
```

## 6. IssueHeader
```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class IssueHeader:
    issue_date: date
    printed_at: datetime
    sequence_of_day: int
    trigger_mode: TriggerMode
```

## 7. Block 抽象契约
```python
from abc import ABC
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Block(ABC):
    block_id: str
    block_type: str
    title: str
    body: str
    source_app_id: str
    source_app_type: str
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    merge_policy: MergePolicy
    expires_at: datetime | None
    template_type: str
    created_at: datetime

    def is_expired(self, issued_at: datetime) -> bool:
        return self.expires_at is not None and issued_at > self.expires_at
```

约束：
1. Block 是运行时快照对象
2. Block 必须可独立记录
3. Block 必须能被过期判断
4. 当前阶段不要把渲染逻辑塞进 Block

## 8. ContentApp 抽象契约
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time


@dataclass(slots=True)
class ContentApp(ABC):
    app_id: str
    app_type: str
    name: str
    description: str | None
    target_publication_slot_id: str | None
    prepare_at: time | None
    default_trigger_mode: TriggerMode
    default_merge_policy: MergePolicy
    default_template_type: str
    expiration_policy: str | None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    def prepare(self, now: datetime) -> None:
        """当前阶段允许为 no-op。未来用于提前准备内容。"""
        return None

    @abstractmethod
    def publish(self, ctx: "IssueBuildContext") -> Block | None:
        """
        在一次 Issue 中发布一个 Block。
        若当前没有可发布内容，则返回 None。
        """
        raise NotImplementedError
```

约束：
1. ContentApp 是长期配置对象
2. `publish()` 每次只返回一个 Block 或 None
3. 组刊器对同一个 App 每次 Issue 只调用一次 `publish()`
4. 打印是否成功，不得反向改变 App 的后续产品语义

## 9. SceneApp / SceneBlock
```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SceneBlock(Block):
    scene_note: str | None
    checklist_items: tuple[str, ...]


@dataclass(slots=True)
class SceneApp(ContentApp):
    scene_note: str | None
    checklist_items: tuple[str, ...]
    recurrence_rule: str | None

    def publish(self, ctx: "IssueBuildContext") -> SceneBlock | None:
        raise NotImplementedError
```

约束：
1. SceneApp 必须支持：
   - 只有 note
   - 只有 checklist
   - note + checklist
2. SceneBlock.title 对应场景名
3. SceneBlock.body 作为 plain-text fallback
4. 实际渲染优先使用：
   - `scene_note`
   - `checklist_items`

## 10. App 配置到 Block 快照的映射规则
Codex 必须在代码结构中保留以下映射关系：
- `ContentApp.target_publication_slot_id` -> `Block.publication_slot_id`
- `ContentApp.default_trigger_mode` -> `Block.trigger_mode`
- `ContentApp.default_merge_policy` -> `Block.merge_policy`
- `ContentApp.default_template_type` -> `Block.template_type`
- `ContentApp.expiration_policy` -> `Block.expires_at`（通过规则解析得到）

不要把这些字段做成“既是配置又是结果”的同一个字段源。

## 11. 可选内部对象：PreparedPayload
当前产品语义允许 App 提前准备内容。  
为避免未来实现时扭曲模型，允许在代码中加入一个内部对象，但它不是当前 PRD 的主对象。

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PreparedPayload:
    source_app_id: str
    prepared_at: datetime
    payload: dict[str, Any]
```

说明：
- 这是实现辅助对象，不是当前产品一级对象
- 当前阶段可不实现
- 当前阶段不要持久化它

## 12. Issue
```python
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Issue:
    issue_id: str
    issue_date: date
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    sequence_of_day: int
    header: IssueHeader
    blocks: tuple[Block, ...]
    created_at: datetime
    printed_at: datetime | None = None
```

约束：
1. Issue 是一次实际发行物
2. Issue 只包含：
   - 一个 Header
   - 多个 Block
3. 当前阶段不实现复杂状态机

## 13. IssueAssembler 契约
建议创建服务对象 `IssueAssembler`。

```python
from collections.abc import Sequence
from datetime import datetime


class IssueAssembler:
    def assemble_scheduled_issue(
        self,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        raise NotImplementedError

    def assemble_immediate_issue(
        self,
        app: ContentApp,
        now: datetime,
        sequence_of_day: int,
    ) -> Issue:
        raise NotImplementedError
```

行为要求

`assemble_scheduled_issue`
1. 创建 Issue
2. 创建 IssueHeader
3. 仅收集归属于该 slot 的 App
4. 对每个 App 调用一次 `publish()`
5. 丢弃 `None`
6. 丢弃已过期 Block
7. 保留未过期 Block
8. 按 FIFO 组装
9. 返回 Issue

`assemble_immediate_issue`
1. 创建独立一期
2. `publication_slot_id` 可为空
3. `trigger_mode` 必须是 `immediate`
4. 不参与合并
5. 对传入 App 调用一次 `publish()`
6. 若无 Block，可返回空 Issue，或显式抛出受控异常  
   当前阶段建议使用受控异常或空 Issue 二选一，但 Codex 不得自行发明业务补偿

## 14. 当前阶段禁止的实现
当前代码阶段禁止以下行为：
- 在 `publish()` 里做真实打印
- 在 `publish()` 里做持久化
- 在 `publish()` 里依赖用户反馈
- 在 `IssueAssembler` 中实现重试逻辑
- 在 `IssueAssembler` 中实现打印失败逻辑
- 在 `IssueAssembler` 中实现复杂优先级
- 在 `SceneApp` 中偷偷引入 reminder 概念

## 15. 推荐的最小测试断言
当前阶段至少需要覆盖：
1. 一个 SceneApp 可以发布 SceneBlock
2. note-only Scene 可以正常发布
3. checklist-only Scene 可以正常发布
4. 定时组刊可以合并多个 Block
5. 过期 Block 会被剔除
6. 即时触发会生成独立一期

## 16. Printer / Device Boundary
当前阶段允许进入 printer/device boundary，但这些对象不属于 domain。

### 16.1 PrinterTargetConfig
- 作用：
  - 表示一个 operator-facing 的打印目标配置
- 当前阶段支持的 kind：
  - `stdout`
  - `file`
  - `memory`
  - `escpos_socket`
  - `escpos_bytes_file`
- 约束：
  - 它属于 config/runtime/printing boundary
  - 不要把它塞进 `Issue`、`Block` 或 `ContentApp`

### 16.2 HardwarePrintOptions
- 作用：
  - 表示硬件打印阶段的附加选项
- 当前阶段建议包含：
  - `mode`
  - `font_path`
  - `font_size`
  - `line_spacing`
  - `cut`
- 约束：
  - 当前阶段 `mode` 只允许 `raster`
  - blank `font_path` 可归一化为 `None`

### 16.3 RasterizedReceipt
- 作用：
  - 表示 `RenderedReceipt` 已经被光栅化后的中间结果
- 约束：
  - 它不属于 domain
  - 当前阶段只要求单色 receipt image
  - 不做分页、裁切、二维码或图片优化

### 16.4 EscPosPayload
- 作用：
  - 表示已经编码完成、可发送到 ESC/POS 兼容目标的 bytes
- 约束：
  - 当前阶段只要求最小 raster payload
  - 不做 capability negotiation
  - 不做 text-mode code page 打印

### 16.5 EscPosSocketPrinterAdapter
- 作用：
  - 通过 TCP socket 把 ESC/POS bytes 发送到单台真实打印机
- 约束：
  - 当前阶段只支持 `host` + `port`
  - 使用 socket 发送 bytes
  - 异常直接 bubble up
  - 不做 retry / recovery

### 16.6 EscPosBytesFileAdapter
- 作用：
  - 把 ESC/POS bytes 写到 `.bin` 文件，作为 raw bytes debug adapter
- 约束：
  - 自动创建目录
  - 同名文件直接覆盖
  - 不定义 reprint 语义

### 16.7 当前阶段的打印链路
当前阶段允许的最小真实打印链路为：

`Issue -> RenderedReceipt -> RasterizedReceipt -> EscPosPayload -> PrinterAdapter`

约束：
- `PrintService` 仍然只负责：
  - `Issue -> RenderedReceipt`
  - `RenderedReceipt -> PrinterAdapter`
- 真实硬件 adapter 可以在 `deliver(receipt)` 内部完成：
  - text -> image
  - image -> ESC/POS bytes
  - bytes -> transport
- 不把硬件字节流与设备配置回写到 domain

## 17. Printer Profile / Diagnostics Boundary
当前阶段允许把打印机推进到 profile-aware、calibratable、diagnosable，但这些对象仍然不属于 domain。

### 17.1 PrinterProfile
- 作用：
  - 描述设备侧的纸宽、可打印宽度与默认参数
- 当前阶段建议字段：
  - `profile_id`
  - `paper_width_mm`
  - `printable_width_dots`
  - `horizontal_padding_dots`
  - `line_feed_after_print`
  - `supports_cut`
  - `default_cut`
  - `default_font_size`
  - `default_line_spacing`
  - `recommended_render_profile_name`

### 17.2 PrinterCapability
- 作用：
  - 表示当前 target 的最小能力摘要
- 当前阶段只要求最小静态能力，不做真实探测

### 17.3 DeliveryDiagnostics
- 作用：
  - 表示一次 delivery 的最小诊断信息
- 当前阶段建议包含：
  - `adapter_name`
  - `target_id`
  - `printer_profile_name`
  - `render_profile_name`
  - `transport`
  - `bytes_length`
  - `duration_ms`
  - `succeeded`
  - `error_text`

### 17.4 TargetHealthResult
- 作用：
  - 表示 operator 主动执行 `targets ping` 的结果
- 约束：
  - 当前阶段只对 `escpos_socket` target 有意义
  - 不做自动恢复

### 17.5 PrinterTargetInspection
- 作用：
  - 表示 `targets inspect` 的结构化输出摘要
- 约束：
  - 用于 operator 观察，不是 domain 状态

### 17.6 PrintResult
- 作用：
  - 将 `RenderedReceipt` 与 `DeliveryDiagnostics` 打包成一次打印结果
- 约束：
  - 不引入新的产品级状态机
  - 不引入 retry / recovery
7. 一个 App 在一次 Issue 中只发布一个 Block

## 16. Printing / application boundary
当前阶段允许建立 rendering 与未来真实打印机之间的边界对象。  
这些对象属于 printing / application boundary，而不是 domain。

说明：
- 允许在这一层传递“已经渲染好的票据文本”
- 不允许把 printing 对象混入 `Issue` / `Block` / `ContentApp`
- 不允许在当前阶段引入产品级失败恢复、历史记录或打印状态机

## 17. RenderedReceipt
建议定义 `RenderedReceipt`：

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class RenderedReceipt:
    issue_id: str
    publication_slot_id: str | None
    trigger_mode: TriggerMode
    profile_name: str
    text: str
    rendered_at: datetime
```

约束：
1. `RenderedReceipt` 是 rendering -> printing 的边界 artifact
2. 它不是 domain 对象
3. 它只表示“已经渲染好的票据文本”
4. 当前阶段不要在这里引入打印状态机

## 18. PrinterAdapter
建议定义 `PrinterAdapter`：

```python
from abc import ABC, abstractmethod


class PrinterAdapter(ABC):
    name: str

    @abstractmethod
    def deliver(self, receipt: RenderedReceipt) -> None:
        raise NotImplementedError
```

约束：
1. adapter 只接收已经渲染好的 `RenderedReceipt`
2. adapter 不负责渲染
3. adapter 不负责 domain 组刊
4. adapter 不负责历史记录
5. 当前阶段不要引入 retry / fallback / product semantics
6. adapter 异常允许直接向外抛出

## 19. PrintService
建议定义 `PrintService`：

```python
class PrintService:
    def render_issue_to_receipt(
        self,
        issue: Issue,
        profile: RenderProfile = RECEIPT_42,
    ) -> RenderedReceipt:
        raise NotImplementedError

    def print_issue(
        self,
        issue: Issue,
        adapter: PrinterAdapter,
        profile: RenderProfile = RECEIPT_42,
    ) -> RenderedReceipt:
        raise NotImplementedError
```

约束：
1. `render_issue_to_receipt()` 内部调用现有 `render_issue()`
2. `print_issue()` 先 render，再把 artifact 交给 adapter
3. `PrintService` 不修改 `Issue`
4. `PrintService` 不记录历史
5. `PrintService` 不实现失败恢复
6. adapter 异常直接 bubble up

## 20. Application boundary / publication runtime
当前阶段允许建立一个应用层 publication runtime，用于把组刊、渲染与 dry-run delivery 串联成同步调用入口。
这些对象属于 application boundary，而不是 domain。

说明：
- 允许在这一层组织 `IssueAssembler` 与 `PrintService`
- 不允许把 application 对象混入 `Issue` / `Block` / `ContentApp`
- 不允许在当前阶段引入持久化、历史、调度、重试或产品级失败恢复

## 21. PublicationResult
建议定义 `PublicationResult`：

```python
from dataclasses import dataclass


@dataclass(slots=True)
class PublicationResult:
    issue: Issue
    receipt: RenderedReceipt
    adapter_name: str
```

约束：
1. `PublicationResult` 是 application boundary 对象，不是 domain 对象
2. 它只表示一次 publication 调用的返回结果
3. 当前阶段不要在这里引入状态机
4. 当前阶段不要在这里引入持久化语义
5. `receipt` 必须就是本次实际 deliver 给 adapter 的那个对象实例

## 22. PublicationService
建议定义 `PublicationService`：

```python
class PublicationService:
    def publish_scheduled(
        self,
        slot: PublicationSlot,
        apps: Sequence[ContentApp],
        adapter: PrinterAdapter,
        now: datetime,
        sequence_of_day: int,
        profile: RenderProfile = RECEIPT_42,
    ) -> PublicationResult:
        raise NotImplementedError

    def publish_immediate(
        self,
        app: ContentApp,
        adapter: PrinterAdapter,
        now: datetime,
        sequence_of_day: int,
        profile: RenderProfile = RECEIPT_42,
    ) -> PublicationResult:
        raise NotImplementedError
```

约束：
1. `PublicationService` 属于 application boundary，而不是 domain
2. `PublicationService` 负责串联 `IssueAssembler` 与 `PrintService`
3. `PublicationService` 不负责持久化、历史、调度或失败恢复
4. `publish_scheduled()` 与 `publish_immediate()` 都必须直接 bubble up adapter 异常
5. `PublicationService` 不修改 `Issue.printed_at`

## 23. Config / runtime boundary
当前阶段允许建立一个 config/runtime boundary，用于把静态 TOML 配置编译为 manual runtime 所需对象。
这些对象属于 application / composition / operator boundary，而不是 domain。

说明：
- 允许在这一层加载 TOML、做最小校验并编译成 runtime 可用对象
- 不允许把 config dataclass 直接当作 `PublicationSlot`、`SceneApp` 或其他 domain 对象
- 不允许在当前阶段引入持久化、队列、设备发现或复杂 DI framework

## 24. RuntimeConfig
建议定义 `RuntimeConfig`：

```python
@dataclass(slots=True)
class RuntimeConfig:
    ...
```

约束：
1. `RuntimeConfig` 是 config 层对象，不是 domain 对象
2. 当前阶段使用 stdlib `tomllib` 从 TOML 文件加载
3. 当前阶段只覆盖：
   - publication slots
   - scene apps
   - default render profile
   - default dry-run adapter kind
4. 当前阶段不要把它扩张成最终产品级 schema

## 25. ConfiguredSceneApp
当前阶段允许在 config 层定义轻量 `ConfiguredSceneApp`，再由 compiler 转成 domain `SceneApp`。

约束：
1. `ConfiguredSceneApp` 只表达配置文件中的 scene app
2. 它不是 domain `SceneApp`
3. compiler 负责从 config 世界进入 domain / application 世界

## 26. RuntimeBundle
建议定义 `RuntimeBundle`：

```python
@dataclass(slots=True)
class RuntimeBundle:
    publication_service: PublicationService
    slots_by_id: dict[str, PublicationSlot]
    apps_by_id: dict[str, ContentApp]
    default_profile: RenderProfile
    default_adapter_kind: str
```

约束：
1. `RuntimeBundle` 是 composition root 的产物，不是 domain 对象
2. 它负责暴露 manual runtime 所需的最小可运行对象
3. 当前阶段不要把它扩张成 service locator

## 27. AdapterFactory
当前阶段允许存在一个最小 `AdapterFactory`，用于创建 dry-run adapters。

约束：
1. `AdapterFactory` 属于 runtime / composition boundary
2. 当前阶段只需要支持：
   - `stdout`
   - `file`
   - `memory`
3. 不允许把 adapter factory 放进 domain
4. 不允许在当前阶段引入真实设备发现或 capability negotiation

## 28. CLI 最小命令面
当前阶段允许提供一个 operator-facing CLI。

建议最小命令面：
1. `list`
2. `preview scheduled`
3. `publish scheduled`
4. `publish immediate`

约束：
1. CLI 使用 stdlib `argparse`
2. CLI 只做 manual dry-run 操作，不做 scheduler / daemon
3. CLI 不负责扩张产品语义
4. CLI 可以覆盖 profile / adapter / now / sequence_of_day 等运行参数

## 29. State / runtime boundary
当前阶段允许建立一个本地 state/runtime boundary，用于把声明式配置之外的运行态状态保存在 SQLite 中，并驱动自动化 tick。
这些对象属于 runtime / application / state boundary，而不是 domain。

说明：
- 允许在这一层保存 publication runs、delivery attempts、checkpoint 与 daily sequence allocator
- 不允许把 runtime state 对象混入 `Issue` / `Block` / `ContentApp`
- 不允许把 declaration config 写回 SQLite，也不允许把 runtime state 写回 TOML

## 30. PublicationRunRecord
建议定义 `PublicationRunRecord`：

```python
@dataclass(slots=True)
class PublicationRunRecord:
    issue_id: str
    slot_id: str | None
    occurrence_at: datetime | None
    trigger_mode: str
    sequence_of_day: int
    profile_name: str
    adapter_name: str
    status: str
    created_at: datetime
    delivered_at: datetime | None
```

约束：
1. `PublicationRunRecord` 是 runtime ledger 对象，不是 domain 对象
2. 当前阶段只要求最小状态：
   - `assembled`
   - `delivered`
   - `delivery_failed`
3. 当前阶段不要扩张为复杂状态机

## 31. DeliveryAttemptRecord
建议定义 `DeliveryAttemptRecord`：

```python
@dataclass(slots=True)
class DeliveryAttemptRecord:
    attempt_id: str
    issue_id: str
    adapter_name: str
    attempted_at: datetime
    succeeded: bool
    error_text: str | None
```

约束：
1. `DeliveryAttemptRecord` 是 delivery ledger 对象，不是 domain 对象
2. 当前阶段每次 delivery 尝试最多记录一条 attempt
3. 当前阶段不引入 retry / recovery 语义

## 32. RuntimeCheckpoint
当前阶段允许定义一个最小 `RuntimeCheckpoint`，用于表达 runtime checkpoint，例如 `last_tick_at`。

约束：
1. 它属于 runtime state boundary
2. 当前阶段只需要最小 checkpoint 能力
3. 不要扩张为复杂 scheduler state machine

## 33. ScheduledOccurrence
建议定义 `ScheduledOccurrence`：

```python
@dataclass(slots=True, frozen=True)
class ScheduledOccurrence:
    slot_id: str
    occurrence_at: datetime
```

约束：
1. `ScheduledOccurrence` 是 scheduler/runtime 对象，不是 domain 对象
2. 当前阶段只表达“某个 slot 在某个时点的一次 occurrence”
3. 当前阶段只支持每日固定时点，不做复杂 recurrence engine

## 34. RuntimeTickResult
建议定义 `RuntimeTickResult`：

```python
@dataclass(slots=True)
class RuntimeTickResult:
    ticked_at: datetime
    window_start: datetime
    window_end: datetime
    due_occurrences: tuple[ScheduledOccurrence, ...]
    published_issue_ids: tuple[str, ...]
    skipped_existing_occurrences: tuple[ScheduledOccurrence, ...]
```

约束：
1. `RuntimeTickResult` 是 application/runtime boundary 对象
2. 它只表达一次 scheduler tick 的结果
3. 当前阶段不要在这里引入重试、恢复或复杂 metrics

## 35. SQLiteStateStore
建议定义 `SQLiteStateStore`：

```python
class SQLiteStateStore:
    def init_schema(self) -> None:
        raise NotImplementedError
```

约束：
1. `SQLiteStateStore` 属于 runtime state boundary，而不是 domain
2. 使用 stdlib `sqlite3`
3. SQLite 中时间统一存 ISO 8601 文本
4. 当前阶段不引入 ORM、migrations framework 或 connection pool

## 36. AutomationRuntimeService
建议定义 `AutomationRuntimeService`：

```python
class AutomationRuntimeService:
    def run_once(...) -> RuntimeTickResult:
        raise NotImplementedError

    def run_loop(...) -> None:
        raise NotImplementedError
```

约束：
1. `AutomationRuntimeService` 属于 application/runtime boundary，而不是 domain
2. 它负责串联：
   - scheduler due policy
   - issue assembly
   - receipt rendering
   - dry-run delivery
   - SQLite ledger
3. 它不负责 UI、daemon 管理、重试或复杂 backfill

## 37. Local automation CLI 命令面
当前阶段允许扩展 CLI，为本地自动化 runtime 提供最小 operator entrypoints：
1. `runtime once`
2. `runtime loop`
3. `runs list`
4. `runs latest`

约束：
1. CLI 继续使用 stdlib `argparse`
2. `runtime loop` 只做本地 polling，不做 daemon / service manager
3. CLI 可以覆盖 `state`、`profile`、`adapter`、`output_dir`、`catchup_seconds`、`poll_interval` 等运行参数
