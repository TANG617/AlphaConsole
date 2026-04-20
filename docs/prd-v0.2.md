# AlphaConsole 产品需求文档 v0.2
## 1. 文档信息
- 文档名称：AlphaConsole 产品需求文档
- 文档版本：v0.2
- 文档状态：工作草案
- 当前目标：为第一批代码骨架提供稳定产品语义

## 2. 一句话定义
AlphaConsole 是一个以固定刊次与即时独立一期为核心的**个人纸质内容发行系统**。  
系统在约定的发行时点生成一期纸质发行物，由统一报头与多个内容块组成，并通过打印机将内容送达日常生活场景。

## 3. 核心问题
用户需要一种重新融入现代生活的打印媒介，它不是传统的“文档打印机”，而是一个会在合适时刻把内容变成纸的发行系统。  
用户希望通过纸质输出获得：
- 更强的存在感
- 更低的忽略概率
- 更好的环境融入感
- 更强的场景执行感

## 4. 产品目标
当前阶段的目标是先建立稳定的发行骨架，而不是实现所有内容 app。

### 当前目标
1. 定义固定发行时点。
2. 在发行时点生成一期 `Issue`。
3. 让不同 App 在出刊时各自发布一个 `Block`。
4. 将多个 Block 默认合并到同一期中。
5. 通过 `SceneApp` 覆盖最基础的 note + checklist 场景。
6. 支持即时触发时生成独立一期。
7. 明确开环语义：打印不反向影响后续生产。
8. 记录必要历史，但历史展示不是当前重点。

## 5. 非目标
以下内容不属于当前阶段：
- Calendar
- 数字闭环任务管理
- 用户反馈回传
- 重印
- 打印失败后的产品语义
- 打印长度限制
- 复杂优先级体系
- 复杂版式引擎
- Printer 驱动实现
- LLM 编辑策略的细化落地
- Scheduler / persistence / UI

## 6. 核心原则
### 6.1 Printer-first
打印机是主交互媒介，不是附属输出设备。

### 6.2 Open-loop
打印完成后，当前交互回合结束。  
系统不依赖用户反馈，不记录“纸上是否完成”。

### 6.3 App publishes Block
统一抽象是：**App 产出 Block，Issue 消费 Block**。

### 6.4 One app, one block, one issue
一个 App 在一次 Issue 中最多发布一个 Block。

### 6.5 Block-level expiration
过期判断以 Block 为单位，不以整个 Issue 为单位。

### 6.6 Scheduled merge by default
定时发行默认合并成同一期。

### 6.7 Immediate standalone issue
即时触发默认生成独立一期，不参与默认合并。

### 6.8 Scene is not pipeline-special
`SceneApp` 是一种 App，`SceneBlock` 是一种 Block。  
它在流程上与未来的 WeatherApp、NewsApp 平等，只是字段更丰富。

## 7. 核心概念
### 7.1 PublicationSlot
固定发行时点，例如：
- 07:00 早刊
- 12:00 午刊
- 19:00 晚刊

### 7.2 Issue
某个时点实际打印的一张长条纸。

### 7.3 IssueHeader
每一期固定头部区域，当前包含：
- 日期
- 打印时间
- 当天第几张
- 触发方式

### 7.4 Block
进入 Issue 的基础内容单元。  
除报头外，所有打印内容都应被视为 Block。

### 7.5 App
Block 的生产者。  
App 是长期存在的配置对象或发布者。

### 7.6 SceneApp
一种 App。  
其内容包括：
- 场景标题
- 场景描述 / note
- checklist 条目
- 发行相关 meta

### 7.7 SceneBlock
SceneApp 在某一次 Issue 中产出的 Block 快照。

## 8. MVP 范围
### 包含
1. `PublicationSlot`
2. `Issue`
3. `IssueHeader`
4. `ContentApp` 抽象
5. `Block` 抽象
6. `SceneApp`
7. `SceneBlock`
8. `IssueAssembler`
9. FIFO 拼接
10. Block 级过期删除
11. 即时独立一期
12. 基础历史对象命名与空位

### 暂不包含
1. 真实打印
2. 真实调度
3. 真实存储
4. 真实 LLM
5. 历史展示
6. 失败恢复
7. 高级版式规则
8. 真实天气/新闻 app

## 9. 场景说明
### 9.1 定时刊次
系统在约定时间触发某一期。  
例如中午 12:00 出一期午刊。  
凡是归属该刊次、到时未过期、允许合并的 Block，都会被拼入这一期。

### 9.2 App 提前准备内容
App 可以在更早时间开始准备内容。  
例如“科技新闻”在 08:00 开始收集，但归属 12:00 午刊。  
若到 12:00 仍未准备好，则该 Block 过期，不进入午刊。

### 9.3 SceneApp
例如“午餐”这个 SceneApp：
- note：多吃蔬菜，不要喝可乐
- checklist：
  - 吃得健康
  - 力量训练
  - 9 点结束工作
到刊次触发时，这个 SceneApp 会发布一个 `SceneBlock`。

### 9.4 即时触发
外部系统触发某次立即打印时，应生成一个独立一期。  
独立一期不与当前默认刊次合并。

## 10. 成功标准
当前阶段的成功标准不是“整个产品完成”，而是：
1. 文档语义不自相矛盾。
2. 代码中能清晰区分：
   - App 配置侧
   - Block 快照侧
   - Issue 组刊侧
3. 可以用 `SceneApp` 成功生成 `SceneBlock`。
4. 可以将多个 Block 按 FIFO 拼入一个 `Issue`。
5. 可以正确剔除过期 Block。
6. 可以生成即时独立一期。
7. 没有引入 Calendar / Reminder / Todo 的旧模型。

## 11. 当前明确不实现
- reminder 概念
- checklist 独立对象模型
- event / calendar 模型
- reprint
- print failure semantics
- issue length limit
- block length limit
- 复杂模板系统
- block 优先级体系

## 12. 待后续补充
- LLM 编辑边界
- 个性化 prompt 语义
- 非 Scene 类 App 的具体产品定义
- 历史查看视图
- 打印失败后的语义
- 固定刊名 / identity element
