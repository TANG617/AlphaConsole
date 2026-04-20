# AlphaConsole 模板与排版规范（当前阶段）
## 1. 目标
当前阶段不实现完整排版引擎。  
本文件只定义最小稳定模板规范，确保域模型与未来打印输出之间的边界清楚。

## 2. 总原则
1. 除报头外，所有内容以 `Block` 为基础单位。
2. `Issue` 由：
   - `IssueHeader`
   - 多个 `Block`
   组成。
3. 当前阶段默认 FIFO 拼接。
4. 当前阶段不实现复杂分区。
5. 当前阶段不实现长度限制。
6. 当前阶段不实现固定刊名字样。
7. 当前阶段模板以**文本安全、ASCII 兼容**为优先。

## 3. IssueHeader 模板
## 3.1 组成字段
当前阶段报头固定包含：
- 日期
- 打印时间
- 当天第几张
- 触发方式

## 3.2 当前不包含
- 固定刊名
- 固定字符图案
- logo
- slogan

## 3.3 推荐文本结构
以下只是最小文本结构，不是最终视觉设计：

```text
================================
DATE: 2026-04-20
PRINTED: 12:00
ISSUE NO: 2
TRIGGER: scheduled
--------------------------------
```

说明：
- 顶部和底部可以使用简单分隔线
- 当前阶段只进入基于 render profile 的文本宽度约束
- 当前阶段不要求真实打印机宽度映射
- 当前阶段只保证信息顺序稳定

## 4. Block 通用规范
每个 Block 必须有：
- 标题
- 主体内容
- 与前后 Block 的分隔

推荐最小结构：

```text
[BLOCK TITLE]
body text...
```

或：

```text
--------------------------------
[BLOCK TITLE]
body text...
```

## 5. SceneBlock 模板
### 5.1 结构
SceneBlock 的固定结构顺序如下：
1. Scene 标题
2. Scene note（如为空则省略）
3. checklist（如为空则省略）

### 5.2 note-only 示例
```text
[LUNCH]
多吃蔬菜，不要喝可乐
```

### 5.3 checklist-only 示例
```text
[DINNER]
[ ] 吃得健康
[ ] 力量训练
[ ] 21:00 结束工作
```

### 5.4 note + checklist 示例
```text
[LUNCH]
多吃蔬菜，不要喝可乐
[ ] 吃得健康
[ ] 力量训练
[ ] 21:00 结束工作
```

### 5.5 清单勾选符号
当前阶段默认使用 ASCII 安全写法：
- `[ ]`

不要在当前阶段强制使用特殊 Unicode 符号。

## 6. Generic Block 预留规范
未来天气、新闻等 App 输出的 Block，可先遵循通用模板：

```text
[AFTERNOON WEATHER]
晴转多云，适合慢跑，建议带轻外套。
```

或：

```text
[TECH NEWS]
今天的科技新闻摘要……
```

当前阶段不要求实现这些 Block，只保留模板规范空位。

## 7. 块分隔规则
当前阶段只要求最小可读性，不要求复杂视觉层级。  
建议使用以下任一方式：
1. 空行分隔
2. 简单横线分隔
3. 横线 + 空行

但必须做到：
- Block 边界清晰
- 报头与正文清晰分开

## 8. 空字段折叠规则
### SceneBlock
- `scene_note` 为空：隐藏 note 区域
- `checklist_items` 为空：隐藏 checklist 区域
- 二者不能同时为空；若同时为空，应由上游 App 决定不发布 Block

### Generic Block
- `title` 不可为空
- `body` 建议不可为空；如为空，应由上游决定不发布

## 9. Width-aware rendering（当前阶段新增）
### 9.1 目标
当前阶段支持“按字符显示宽度”进行纯文本票据排版。  
目标是为后续真实打印做准备，而不是在当前阶段绑定某个具体打印机设备。

### 9.2 当前支持
- 基于字符显示宽度进行文本换行
- 预设 render profile，例如 32 列、42 列
- `IssueHeader`、`SceneBlock`、`Issue` 的固定宽度纯文本输出
- 中英文混排下的基础显示宽度计算

### 9.3 当前不做
- truncation
- pagination
- device-specific printer mapping
- 真实纸宽探测
- ESC/POS 指令映射

### 9.4 SceneBlock 的换行要求
- 长 note 需要自动换行
- 长 checklist item 需要自动换行
- checklist continuation line 需要保持稳定缩进
- 自动换行以字符显示宽度为基础，而不是字节长度或 Python 字符数

## 10. 当前阶段不做的模板能力
- 自动分页
- 长度裁剪
- 栏目优先级
- 多栏布局
- 插图
- logo / masthead
- 不同设备的真实纸宽适配
- 条码 / 二维码
