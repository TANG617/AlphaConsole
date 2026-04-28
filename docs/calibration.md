# AlphaConsole Calibration（当前阶段）
## 1. 目标
当前阶段通过 calibration page 帮助 operator 联调：
- 边距
- 宽度
- 行高
- cut/feed

## 2. calibration page 建议内容
至少包含：
1. 标题
2. target id
3. printer profile 名称
4. render profile 名称
5. 宽度尺 / ruler
6. 左右边界线
7. ASCII 文本示例
8. 中文文本示例
9. checklist 示例
10. cut/feed 说明

## 3. 观察建议
- 如果左右边界不均匀，优先检查 padding / 物理装纸
- 如果内容被截断，优先检查 printer profile 宽度与 render profile 是否匹配
- 如果行距异常，优先调整 `font_size` 与 `line_spacing`
- 如果裁纸位置异常，优先检查 `feed_lines` 与 `cut`

## 4. 当前阶段不做
- 自动校准
- 用户反馈闭环
- 自动纠偏
