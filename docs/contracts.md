# AlphaConsole 代码契约
## 1. 目的
本文件定义当前阶段允许进入代码层的抽象契约。  
它不是最终实现，但 Codex 应以此为代码骨架的唯一参考。

## 2. 总约束
1. 文档语义优先于代码便利性。
2. 当前只允许构建域模型、组刊器、width-aware rendering、dry-run print boundary、publication runtime 与 manual runtime，不要实现外围系统。
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
