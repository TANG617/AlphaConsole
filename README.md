# AlphaConsole

AlphaConsole 当前以 `docs/` 下的新文档为准，目标是先落一个**个人纸质内容发行系统**的最小稳定骨架，而不是 reminder / printer MVP。

## 当前状态
- Source of truth 在 [docs/README.md](/Users/timli/workspace/AlphaConsole/docs/README.md)
- 当前已实现范围：
  - 抽象域模型
  - `SceneApp`
  - `SceneBlock`
  - `IssueAssembler`
  - 最小单元测试
- 当前明确不做：
  - Printer adapter
  - Scheduler
  - Database / persistence
  - TUI / Web UI
  - LLM integration

## 文档入口
- [产品需求文档](/Users/timli/workspace/AlphaConsole/docs/prd-v0.2.md)
- [对象模型](/Users/timli/workspace/AlphaConsole/docs/object-model.md)
- [核心流程](/Users/timli/workspace/AlphaConsole/docs/core-flows.md)
- [代码契约](/Users/timli/workspace/AlphaConsole/docs/contracts.md)
- [开工计划](/Users/timli/workspace/AlphaConsole/docs/coding-plan.md)

## 代码结构
```text
docs/
src/alphaconsole/
tests/
```

## 验证
```bash
uv run --with pytest pytest tests/test_scene_block.py tests/test_issue_assembler.py
```
