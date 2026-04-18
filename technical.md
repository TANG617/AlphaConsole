# App Technical Route

## 1. 文档定位

本文档用于总结这个 app 的最终技术路线。它回答的问题不是“这个项目想做什么”，而是：

- 系统最终要长成什么技术形态
- 当前已经实现到哪一层
- 后续怎样从本机 MVP 平滑演进到树莓派常驻系统
- 怎样接入 LLM、日历、语音和手机端，而不推翻现有架构

配套文档如下：

- 产品需求：[prd.md](/Users/timli/workspace/AlphaConsole/prd.md)
- 界面与版式设计：[design.md](/Users/timli/workspace/AlphaConsole/design.md)

## 2. 总体结论

这个 app 的最终技术路线应当是：

**一个本地优先、事件驱动、声明式渲染、可多入口接入的个人执行系统。**

它的技术核心不是聊天，也不是普通 Todo，而是以下四层：

1. `Structured Planning Core`
   把用户意图变成结构化事件、提醒和 checklist

2. `Reliable Local Execution`
   在本地持久化、调度、恢复、触发和打印

3. `Unified Receipt UI Engine`
   用同一份 layout/scene 同时驱动 TUI 预览、图片生成和打印

4. `Multi-Channel Ingress`
   支持未来从 TUI、CLI、Web、手机、语音等多个入口进入同一核心

## 3. 最终系统目标

最终系统要满足这四个原则：

- 本地优先：即使 LLM、日历或网络暂时不可用，本地提醒与打印仍能运行
- 结构化优先：LLM 不直接操控系统状态，所有执行前必须落成结构化数据
- 单一真相源：提醒、清单、打印、预览共享同一套本地状态
- 渲染统一：TUI、图片和打印共享同一份声明式 scene

## 4. 当前已落地的技术基线

当前仓库已经实现的是“不依赖 AI 的本地 MVP”，主要包括：

- Python 3 + `uv` 项目管理
- SQLite 本地持久化
- 本地 worker 轮询到期任务
- ESC/POS 网络打印
- Textual TUI
- 统一 scene 驱动的 TUI 预览 / PNG / 打印
- 主题 token 配置文件

当前核心代码：

- CLI 入口：[src/alpha_console/cli.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/cli.py)
- 配置系统：[src/alpha_console/config.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/config.py)
- 数据层：[src/alpha_console/db.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/db.py)
- 统一版式模型：[src/alpha_console/layout.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/layout.py)
- 渲染层：[src/alpha_console/render.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/render.py)
- 打印服务：[src/alpha_console/printer.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/printer.py)
- 业务服务：[src/alpha_console/service.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/service.py)
- TUI：[src/alpha_console/tui.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/tui.py)

## 5. 最终架构分层

推荐的最终架构分成 7 层。

### 5.1 Ingress Layer

负责接收用户输入，不处理复杂业务。

最终支持：

- CLI
- TUI
- 本地 Web UI
- 手机 Web / App
- 语音入口
- 未来可能的 webhook / bot

原则：

- 所有入口只负责采集输入和展示结果
- 不直接写数据库核心状态
- 统一调用 application service

### 5.2 Intent / Planning Layer

负责把自然语言输入转成结构化任务。

最终将包含两种模式：

- `manual mode`
  当前已实现，用户手动提供明确字段
- `llm mode`
  未来接入 LLM，将自然语言转成结构化 draft

这里的关键不是“生成一段文本”，而是输出确定的数据模型，例如：

- `event`
- `checklist`
- `event + checklist`
- `clarification_required`

### 5.3 Validation Layer

这是未来接入 LLM 后最关键的一层。

职责：

- 校验时间格式
- 校验时区
- 校验任务是否早于当前时间
- 校验 checklist 是否为空
- 判断是否需要人工确认
- 防止重复创建事件

原则：

- LLM 输出只能作为 draft
- 本地校验通过后才能变成正式任务

### 5.4 Domain / Application Layer

这是最终系统的核心。

负责：

- 创建 event
- 创建 checklist
- 创建 reminder job
- 查询与更新状态
- 触发打印
- 管理模板
- 管理重打和失败重试

当前主要承载于：

- [src/alpha_console/service.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/service.py)

未来会进一步拆成：

- `entry_service`
- `checklist_service`
- `scheduler_service`
- `calendar_service`
- `planning_service`

### 5.5 Persistence Layer

使用 SQLite 作为本地真相源。

最终本地数据库应保存：

- 事件
- checklist template
- checklist run
- reminder job
- print job
- calendar mapping
- ingestion log
- llm draft / audit log

当前已实现：

- `entries`
- `checklist_items`
- `print_jobs`

当前代码：

- [src/alpha_console/db.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/db.py)

### 5.6 Render / Output Layer

这是项目的特色层。

最终目标：

- 同一份 `ReceiptScene`
- 同一组主题 token
- 多 renderer 输出到不同媒介

当前已实现：

- ASCII CLI preview
- Rich TUI preview
- PNG image
- ESC/POS print

当前代码：

- [src/alpha_console/layout.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/layout.py)
- [src/alpha_console/render.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/render.py)
- [src/alpha_console/printer.py](/Users/timli/workspace/AlphaConsole/src/alpha_console/printer.py)

### 5.7 Runtime / Deployment Layer

负责把这套系统稳定跑起来。

本机阶段：

- `uv run alpha-console ...`
- 手动启动 worker

树莓派阶段：

- systemd service 常驻 worker
- systemd service 常驻 app/TUI/API
- 本地日志
- 自动重启
- 开机恢复

## 6. 关键技术决策

### 6.1 语言选择：Python

选择理由：

- 树莓派友好
- ESC/POS 生态成熟
- 日历/LLM/语音生态都够用
- 快速迭代 TUI、脚本和服务端都方便

### 6.2 项目管理：uv

选择理由：

- 依赖管理轻量
- 本机和树莓派迁移成本低
- CLI 运行方式简单清晰

### 6.3 本地数据库：SQLite

选择理由：

- 单机应用足够可靠
- 易于备份和迁移
- 树莓派部署简单
- 非常适合本项目这种本地优先状态管理

### 6.4 调度策略：本地 worker + DB 轮询

当前实现是 DB 轮询 due job。

最终仍推荐本地 worker 驱动，而不是完全依赖外部定时系统。原因：

- 能与本地状态强一致
- 开机恢复逻辑更直接
- 便于打印、失败重试、补打统一管理

未来可在内部引入更正式的 scheduler，但外部表现仍应保持“本地任务执行器”模型。

### 6.5 打印策略：PNG 作为打印中间格式

这是非常重要的最终路线选择。

不推荐直接依赖打印机原生字符编码去承载全部排版，原因：

- 中文兼容性不稳定
- 不同机型字库和对齐能力差异大
- 难以做统一 UI 风格

因此最终路线应保持：

`Scene -> Bitmap PNG -> ESC/POS image`

这样可以：

- 保证版式一致
- 保证中文可读性
- 保证风格可控

### 6.6 预览策略：统一 scene，多 renderer

最终系统不应该维持三套独立版式：

- 一套 TUI
- 一套图片
- 一套打印

而应该维持：

`single scene source of truth`

当前已经实现这个方向，后续继续强化即可。

## 7. 最终数据模型

最终推荐的数据对象如下。

### 7.1 Event

代表日程事件。

关键字段：

- `id`
- `title`
- `start_at`
- `end_at`
- `timezone`
- `notes`
- `calendar_provider`
- `calendar_event_id`

### 7.2 ChecklistTemplate

代表可复用场景模板。

关键字段：

- `id`
- `name`
- `scenario`
- `items`
- `default_offset_minutes`

### 7.3 ChecklistRun

代表一次实际执行的 checklist。

关键字段：

- `id`
- `template_id`
- `title`
- `items_snapshot`
- `due_at`
- `event_id`
- `status`

### 7.4 ReminderJob

代表一个到时需要执行的本地任务。

关键字段：

- `id`
- `target_type`
- `target_id`
- `due_at`
- `action`
- `status`
- `attempt_count`

### 7.5 PrintJob

代表一次打印或补打动作。

关键字段：

- `id`
- `entry_id`
- `requested_at`
- `completed_at`
- `status`
- `preview_path`
- `error_message`

### 7.6 IngestionDraft

这是未来 LLM 接入后建议新增的对象。

关键字段：

- `id`
- `source_channel`
- `raw_input`
- `parsed_payload`
- `validation_status`
- `needs_confirmation`

## 8. 最终用户数据流

### 8.1 当前无 AI 路线

`用户手动输入 -> Application Service -> SQLite -> Worker -> ReceiptScene -> PNG -> Printer`

### 8.2 未来 AI 路线

`自然语言 -> LLM Draft -> Validation -> Confirmed Structured Record -> SQLite -> Worker -> ReceiptScene -> PNG -> Printer`

### 8.3 未来日历联动路线

`自然语言 / 手动输入 -> 结构化 Event -> Calendar Sync -> ReminderJob -> 到时打印`

### 8.4 未来模板化 checklist 路线

`场景输入 / 事件触发 -> ChecklistTemplate -> ChecklistRun -> ReminderJob -> 打印 checklist`

## 9. 最终 UI 技术路线

UI 路线不是“做一个 Web 页面替代 TUI”，而是建立统一的 UI 描述层。

推荐路线：

### 9.1 当前阶段

- `ReceiptScene`
- `SceneSection`
- `SceneText`
- `ThemeSettings`

### 9.2 下一阶段

增加：

- 组件模板
- variant
- design tokens
- preview reload

### 9.3 远期阶段

让这套 system 更接近现代 GUI 框架：

- 组件树
- 统一测量逻辑
- 实时预览
- 可视化编辑
- 模板系统

也就是说，最终技术路线不是“把打印做成几套字符串模板”，而是“做一个 receipt-oriented GUI framework”。

## 10. 远程访问路线

最终建议采用分阶段策略。

### 10.1 当前到近期

- 本机开发
- CLI + TUI

### 10.2 树莓派阶段

- Tailscale
- SSH
- 可选的本地 Web UI

### 10.3 后续

- 手机 Web
- 局域网或 Tailscale 内访问
- 不优先开放公网写接口

## 11. 树莓派迁移路线

最终部署目标应为树莓派上的两个常驻角色：

### 11.1 Core Worker

负责：

- 轮询 due job
- 打印
- 重试
- 恢复

### 11.2 Control Surface

负责：

- TUI
- CLI
- 后续 Web/API

迁移步骤建议：

1. 保持 Python + uv 不变
2. 复制项目和 `alpha_console.toml`
3. 迁移 SQLite 或重新初始化
4. 配置 systemd
5. 验证打印连通性
6. 验证开机恢复

## 12. LLM 接入路线

LLM 不应成为核心运行时前提，而应作为增强层接入。

推荐路线：

### 12.1 Phase 1

- 手动输入继续保留
- 增加一个 `plan` 接口
- LLM 只生成结构化 draft

### 12.2 Phase 2

- 增加 validation
- 增加确认队列
- 增加失败回退到手动编辑

### 12.3 Phase 3

- 场景化 checklist 自动生成
- 事件和 checklist 联动
- 每日摘要与计划整理

关键原则：

- LLM 不直接执行写库
- LLM 不直接发打印
- LLM 只生成待验证结构

## 13. 日历接入路线

推荐先单一 provider，后抽象接口。

推荐路线：

1. 先定义内部 `CalendarEvent` 抽象
2. 先接一个 provider
3. 保存本地 ID 与 provider event ID 映射
4. 再考虑双向同步

最终需要支持：

- create event
- update event
- list events by day
- local mapping

## 14. 语音与手机入口路线

最终技术路线应保证它们只是新的 ingress，不改核心。

### 14.1 语音

链路：

`Speech -> Text -> Planning -> Validation -> Core`

### 14.2 手机

链路：

`Mobile UI -> API -> Core`

核心要求：

- 不复制业务逻辑
- 不单独维护另一套数据模型
- 不单独维护另一套打印模板

## 15. 可维护性路线

最终系统要长期稳定运行，因此技术路线必须关注可维护性。

推荐长期保持以下约束：

- config file 驱动，而不是散落常量
- scene 驱动，而不是拼接字符串模板
- service layer 驱动，而不是入口脚本直接写库
- DB schema 演进可控
- worker 与 UI 解耦

## 16. 当前与最终的差距

当前已经完成：

- 本地 SQLite
- worker
- 统一 scene
- TUI 预览
- PNG 打印
- 打印机配置落盘

尚未完成但已明确技术方向：

- LLM planning layer
- validation/confirmation queue
- calendar adapter
- checklist template library
- Web/mobile ingress
- voice ingress
- tree-shakable componentized receipt framework

## 17. 推荐的里程碑路线

### M1 本地可靠 MVP

目标：

- 手动录入
- 统一预览
- 稳定打印
- 配置稳定

状态：

- 已完成

### M2 树莓派常驻运行

目标：

- systemd
- 自动启动
- 故障恢复
- 远程维护

### M3 结构化日历系统

目标：

- Event 模型增强
- Calendar provider 接入
- 今日摘要打印

### M4 LLM 编排系统

目标：

- 自然语言转 draft
- validation
- confirmation flow

### M5 多入口系统

目标：

- Web
- 手机
- 语音

### M6 Receipt UI Framework

目标：

- 多主题
- 组件模板
- 可视化编辑
- 更强的 WYSIWYG

## 18. 最终技术路线一句话总结

这个 app 的最终技术路线应当是：

**以 Python + SQLite + local worker 为可靠执行核心，以 ReceiptScene + theme tokens 为统一 UI/打印引擎，以 LLM / 日历 / 语音 / 手机入口作为可插拔增强层，逐步演进为一个运行在树莓派上的本地优先个人执行终端。**
