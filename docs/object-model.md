# AlphaConsole 对象模型
## 1. 建模原则
当前模型必须明确区分两层：
1. **长期配置对象**
   - 长期存在
   - 描述“谁会供稿”
   - 典型对象：`PublicationSlot`、`ContentApp`、`SceneApp`
2. **运行时快照对象**
   - 某次出刊时被创建
   - 描述“这一期实际打印了什么”
   - 典型对象：`Issue`、`IssueHeader`、`Block`、`SceneBlock`

不要创建一个既承担配置语义又承担打印结果语义的混合对象。

## 2. 代码命名约定
### 产品概念 vs 代码类名
- 产品概念：`App`
- 代码类名：`ContentApp`

这样做是为了减少泛化歧义。

### Scene 命名约束
代码中不要创建一个单独的 `Scene` 类同时承担两层语义。  
必须拆成：
- `SceneApp`
- `SceneBlock`

## 3. 一级对象
## 3.1 PublicationSlot
### 中文
发行时点 / 出刊时点

### 英文
`PublicationSlot`

### 类型
长期配置对象

### 作用
定义固定的发行窗口，例如早刊、午刊、晚刊。

### 建议字段
- `slot_id: str`
- `name: str`
- `description: str | None`
- `publish_time: time`
- `recurrence_rule: str | None`
- `is_enabled: bool`
- `created_at: datetime`
- `updated_at: datetime`

---

## 3.2 ContentApp
### 中文
内容应用 / 内容发布者

### 英文
`ContentApp`

### 类型
长期配置对象 / 抽象基类

### 作用
在某个刊次发布一个 Block。

### 核心规则
- 一个 App 在一次 Issue 中最多发布一个 Block
- App 是供稿者，不是纸面实体
- App 自己不等于 Block

### 建议字段
- `app_id: str`
- `app_type: str`
- `name: str`
- `description: str | None`
- `target_publication_slot_id: str | None`
- `prepare_at: time | None`
- `default_trigger_mode: TriggerMode`
- `default_merge_policy: MergePolicy`
- `default_template_type: str`
- `expiration_policy: str | None`
- `is_enabled: bool`
- `created_at: datetime`
- `updated_at: datetime`

---

## 3.3 SceneApp
### 中文
场景应用

### 英文
`SceneApp`

### 类型
`ContentApp` 的具体实现

### 作用
发布一个包含 note 与 checklist 的 SceneBlock。

### 额外字段
- `scene_note: str | None`
- `checklist_items: tuple[str, ...]`
- `scene_description: str | None`
- `recurrence_rule: str | None`

### 说明
支持三种形式：
1. 只有 note
2. 只有 checklist
3. note + checklist 同时存在

---

## 3.4 Issue
### 中文
发行物 / 一期 / 打印单

### 英文
`Issue`

### 类型
运行时快照对象

### 作用
表示某一次真正生成的纸质发行物。

### 组成
- `IssueHeader`
- `Block[]`

### 建议字段
- `issue_id: str`
- `issue_date: date`
- `publication_slot_id: str | None`
- `trigger_mode: TriggerMode`
- `sequence_of_day: int`
- `header: IssueHeader`
- `blocks: tuple[Block, ...]`
- `created_at: datetime`
- `printed_at: datetime | None`

### 当前状态说明
当前阶段不细化复杂状态流。  
如需状态字段，可只保留最小语义：
- `assembled`
- `printed`
- `expired`

---

## 3.5 IssueHeader
### 中文
报头

### 英文
`IssueHeader`

### 类型
运行时快照对象

### 作用
表示一期顶部固定 meta 区域。

### 当前字段
- `issue_date: date`
- `printed_at: datetime`
- `sequence_of_day: int`
- `trigger_mode: TriggerMode`

### 当前不包含
- 固定刊名
- 固定字符图案
- logo
- identity element

---

## 3.6 Block
### 中文
内容块

### 英文
`Block`

### 类型
运行时快照对象 / 抽象基类

### 作用
进入 Issue 的统一排版与记录单元。

### 统一字段
- `block_id: str`
- `block_type: str`
- `title: str`
- `body: str`
- `source_app_id: str`
- `source_app_type: str`
- `publication_slot_id: str | None`
- `trigger_mode: TriggerMode`
- `merge_policy: MergePolicy`
- `expires_at: datetime | None`
- `template_type: str`
- `created_at: datetime`

### 说明
对于结构更丰富的 Block，`body` 可作为通用摘要或 plain-text fallback。  
具体渲染时优先使用具体 Block 自己的结构字段。

---

## 3.7 SceneBlock
### 中文
场景块

### 英文
`SceneBlock`

### 类型
`Block` 的具体实现

### 作用
表示 `SceneApp` 在某次 Issue 中实际发布的打印内容快照。

### 额外字段
- `scene_note: str | None`
- `checklist_items: tuple[str, ...]`

### 说明
- `title` 对应场景名
- `body` 可作为 note + checklist 的 plain-text 汇总
- 实际渲染时优先使用 `scene_note` 和 `checklist_items`

## 4. 记录对象（保留命名，不作为当前实现重点）
## 4.1 BlockHistory
内容块历史

## 4.2 IssueHistory
发行历史

## 4.3 PrintRecord
打印记录

当前阶段只保留命名和空位，不进入详细实现。

## 5. 对象关系
### 5.1 关系概览
- 一个 `PublicationSlot` 会在长期内产生多个 `Issue`
- 一个 `Issue` 包含一个 `IssueHeader`
- 一个 `Issue` 包含多个 `Block`
- 一个 `ContentApp` 在一次 `Issue` 中最多发布一个 `Block`
- 一个 `SceneApp` 在长期内会产生多个 `SceneBlock`

### 5.2 关系文字版
`PublicationSlot` 负责“什么时候出刊”  
`ContentApp` 负责“谁来供稿”  
`Block` 负责“纸上放什么内容”  
`Issue` 负责“这一期最终长什么样”

## 6. 配置字段到快照字段的映射
以下映射必须在代码中清晰体现：
- `ContentApp.target_publication_slot_id` -> `Block.publication_slot_id`
- `ContentApp.default_trigger_mode` -> `Block.trigger_mode`
- `ContentApp.default_merge_policy` -> `Block.merge_policy`
- `ContentApp.default_template_type` -> `Block.template_type`
- `ContentApp.expiration_policy` -> `Block.expires_at`

不要把 App 配置字段和 Block 快照字段混成一个对象。

## 7. 当前禁止的错误建模
以下写法当前都不允许：
1. 用一个 `Scene` 类同时代表配置与打印结果
2. 把 `Issue` 当成一个 App
3. 把 `Block` 当成长期配置对象
4. 把 checklist 提升成当前阶段独立一级对象
5. 把 reminder 重新引入模型
