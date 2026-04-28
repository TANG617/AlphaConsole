# AlphaConsole 文档总览
## 目的
本目录是当前 coding 前的 source of truth。  
当前版本的目标不是定义一个“提醒系统”，而是定义一个**个人纸质内容发行系统**的最小稳定骨架。

## 当前冻结决策
以下内容已经冻结，Codex 不得自行改写：
1. 产品定义是**个人纸质内容发行系统**。
2. 系统主轴是：`PublicationSlot -> Issue -> Block`。
3. 统一抽象是：**App 产出 Block，Issue 消费 Block**。
4. `SceneApp` 是一种 App；`SceneBlock` 是一种 Block。
5. `SceneApp` 和天气、新闻等其他 App 在流程地位上平等。
6. 一个 App 在一次 Issue 中**最多发布一个 Block**。
7. 一张 Issue 由两部分组成：
   - `IssueHeader`
   - 按 FIFO 排列的 `Block[]`
8. 定时发行默认合并。
9. 即时触发默认生成**独立一期**，不参与合并。
10. 打印是**开环**的：
    - 不需要反馈
    - 不回写完成状态
    - 不因为是否打印影响后续生产
11. 过期规则按 **Block** 为单位处理。
12. 错过时机的 Block 不打印，不补打。
13. 当前阶段不考虑打印失败语义。
14. 当前阶段不做重印。
15. 当前阶段不限制单个 Block 或单个 Issue 的长度。
16. 当前阶段不定义固定 identity element；报头中不强制刊名，后续可能补成字符图案。

## 当前未定义，Codex 不得自行补全
以下内容在当前阶段必须保留空位，不得自行设计产品语义：
- 打印失败后的行为
- 重试策略
- 历史记录 UI
- 固定刊名字样 / identity element
- LLM 编辑权限边界细则
- 长度限制与分页规则
- 优先级体系
- 复杂分区与复杂版式规则
- 打印机驱动细节
- 调度器和持久化方案

## 文档优先级
出现冲突时，以下文档优先级从高到低：
1. `docs/prd-v0.2.md`
2. `docs/object-model.md`
3. `docs/core-flows.md`
4. `docs/contracts.md`
5. `docs/template-spec.md`
6. `docs/coding-plan.md`

## 当前工作范围
当前只允许进入以下范围：
- 文档落盘
- 抽象域模型
- `SceneApp`
- `SceneBlock`
- `IssueAssembler`
- `PublicationService`
- TOML config loading
- runtime builder
- CLI（manual dry-run only）
- SQLite runtime state
- local scheduler runtime
- run ledger
- automated dry-run publication
- width-aware rendering
- print pipeline boundary
- TCP ESC/POS adapter（experimental）
- publication runtime（dry-run end-to-end）
- 最小单元测试

## 当前阶段说明
当前阶段已进入 **local automation runtime（SQLite + scheduler + run ledger, dry-run）**。
这一步的目标是在现有 `IssueAssembler`、width-aware rendering、dry-run print boundary、publication runtime 与 manual runtime 之上，建立一个本地、自动化、可恢复重启的 dry-run runtime。
当前 milestone 仍然不是完整 printer hardware milestone，也不是 UI milestone，更不是 cloud/backend milestone。
当前只补入最小 TCP ESC/POS adapter，用于向网口小票机发送文本型 raw ESC/POS bytes。

## 明确不做
当前阶段明确不做：
- USB / Bluetooth printer adapter
- production-grade ESC/POS 队列、重试和恢复
- TUI / Web UI
- LLM integration
- WeatherApp / NewsApp 的真实内容采集
- 历史查询功能
- 打印失败恢复
- print retry / recovery
- print history query
- scheduler daemon / service manager / cron integration
- pagination
- truncation

## 术语使用约定
### 产品术语
- 发行时点：`PublicationSlot`
- 发行物 / 一期：`Issue`
- 报头：`IssueHeader`
- 内容块：`Block`
- 内容应用：`App`
- 场景应用：`SceneApp`
- 场景块：`SceneBlock`

### 代码术语
为了减少歧义，代码中建议：
- 抽象 App 类名使用 `ContentApp`
- 抽象 Block 类名使用 `Block`
- 不要创建一个既代表配置又代表打印结果的单一 `Scene` 类
- 如需表达“场景配置侧”和“打印快照侧”，分别用：
  - `SceneApp`
  - `SceneBlock`
