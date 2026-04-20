# AlphaConsole 开工计划（当前阶段）
## 1. 目标
本计划用于指导第一批代码落盘。  
目标不是直接做完整产品，而是先做不会歪的最小骨架。

## 2. 工作顺序
### Phase 0：落文档
必须先完成：
- `docs/README.md`
- `docs/prd-v0.2.md`
- `docs/object-model.md`
- `docs/core-flows.md`
- `docs/contracts.md`
- `docs/template-spec.md`
- `docs/coding-plan.md`

文档落盘后再开始写代码。

---

### Phase 1：域模型骨架
创建以下文件：

```text
src/alphaconsole/
  __init__.py
  domain/
    __init__.py
    enums.py
    context.py
    publication_slot.py
    issue_header.py
    issue.py
    block.py
    app.py
    scene.py
```

Phase 1 目标
1. 定义最小枚举：
   - `TriggerMode`
   - `MergePolicy`
2. 定义：
   - `IssueBuildContext`
   - `PublicationSlot`
   - `IssueHeader`
   - `Issue`
   - `Block`
   - `ContentApp`
   - `SceneBlock`
   - `SceneApp`
3. 保证类型关系清晰
4. 不实现外围系统

Phase 1 禁止事项
- 不要加打印机代码
- 不要加 scheduler
- 不要加 persistence
- 不要加 LLM
- 不要加 UI

---

### Phase 2：组刊器
创建以下文件：

```text
src/alphaconsole/services/
  __init__.py
  issue_assembler.py
```

Phase 2 目标

实现 `IssueAssembler` 的最小可运行逻辑：
- `assemble_scheduled_issue`
- `assemble_immediate_issue`

组刊器必须做到
1. 为定时刊次创建 Issue
2. 生成 IssueHeader
3. 从候选 App 收集 Block
4. 一个 App 一次最多调用一次 `publish()`
5. 丢弃 `None`
6. 丢弃过期 Block
7. 以 FIFO 排列保留的 Block
8. 生成最终 Issue

当前阶段允许的简化
- FIFO 可以先按 `created_at` 实现
- 如需稳定性，可加插入顺序作为 tie-breaker
- immediate 先支持单 App -> 单独一期

---

### Phase 3：最小测试
创建以下文件：

```text
tests/
  __init__.py
  test_issue_assembler.py
  test_scene_block.py
```

必须覆盖的测试
1. SceneApp 能发布 SceneBlock
2. note-only Scene 可发布
3. checklist-only Scene 可发布
4. note + checklist Scene 可发布
5. 定时刊次能合并多个 Block
6. 过期 Block 会被剔除
7. 即时触发会生成独立一期
8. 同一个 App 在一次 Issue 中只发布一个 Block

## 3. 推荐目录职责
### `domain/enums.py`
定义最小枚举，不要放业务逻辑。

### `domain/context.py`
定义 `IssueBuildContext`。

### `domain/publication_slot.py`
定义 `PublicationSlot`。

### `domain/issue_header.py`
定义 `IssueHeader`。

### `domain/issue.py`
定义 `Issue`。

### `domain/block.py`
定义 `Block` 抽象与通用行为，如 `is_expired()`。

### `domain/app.py`
定义 `ContentApp` 抽象。

### `domain/scene.py`
定义 `SceneApp` 与 `SceneBlock`。

### `services/issue_assembler.py`
定义组刊逻辑，不做打印。

## 4. Stop 条件
Codex 在当前阶段做到以下程度后必须停止，等待下一轮指令：
1. 文档全部落盘
2. 域模型骨架可 import
3. `IssueAssembler` 最小逻辑可运行
4. 测试通过
5. 没有越界实现外围系统

## 5. 明确不越界的功能
当前阶段不要继续做：
- Printer service
- Scheduler
- DB schema
- API
- TUI
- Web UI
- WeatherApp
- NewsApp
- History query
- Reprint
- Retry / failure recovery

## 6. 推荐的阶段性完成标准
到当前阶段结束时，仓库应能回答这几个问题：
1. `SceneApp` 和 `SceneBlock` 是否被清晰区分？
2. App 和 Block 是否被清晰区分？
3. `Issue` 是否明确只是 Header + Blocks？
4. 定时发行是否能组出一期？
5. 即时触发是否能组出独立一期？
6. 过期 Block 是否会被剔除？

如果以上答案都是“是”，当前阶段就算完成。

---

## 给 Codex 的补充实现说明
下面这段可以作为你给 Codex 的额外执行提示，一起贴过去：

```md
请按以下要求执行：
1. 先创建 docs/ 下全部文件，内容以 handoff 为准。
2. 再根据 docs/contracts.md 与 docs/coding-plan.md 创建 Python 骨架。
3. Python 版本默认按 3.11+ 组织，优先使用 `dataclass(slots=True)`、`StrEnum`、类型标注。
4. 当前阶段只创建：
   - `ContentApp` 抽象
   - `Block` 抽象
   - `PublicationSlot`
   - `IssueHeader`
   - `Issue`
   - `SceneApp`
   - `SceneBlock`
   - `IssueAssembler`
5. 添加最小测试，保证：
   - note-only / checklist-only / mixed scene 都能工作
   - scheduled merge 正常
   - immediate standalone 正常
   - expired block 被剔除
6. 不要实现：
   - printer
   - scheduler
   - persistence
   - llm
   - ui
7. 所有未定义产品语义必须保留 TODO，不要自行发挥。
8. 完成后停在 Phase 2/3，不继续扩展。
```
