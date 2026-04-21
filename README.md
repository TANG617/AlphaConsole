# AlphaConsole

AlphaConsole 当前以 `docs/` 下的新文档为准，目标是先落一个**个人纸质内容发行系统**的最小稳定骨架，而不是 reminder / printer MVP。

## 当前状态
- Source of truth 在 [docs/README.md](docs/README.md)
- 当前已实现范围：
  - 抽象域模型
  - `SceneApp`
  - `SceneBlock`
  - `IssueAssembler`
  - width-aware rendering
  - print pipeline boundary（dry-run）
  - publication runtime（dry-run end-to-end）
  - manual runtime（config + CLI, dry-run）
  - 单元测试
- 当前明确不做：
  - 真实 printer adapter
  - ESC/POS
  - 真实打印机硬件接入
  - Scheduler
  - Database / persistence
  - TUI / Web UI
  - LLM integration

## 文档入口
- [产品需求文档](docs/prd-v0.2.md)
- [对象模型](docs/object-model.md)
- [核心流程](docs/core-flows.md)
- [代码契约](docs/contracts.md)
- [配置格式](docs/configuration.md)
- [手动运行](docs/manual-runtime.md)
- [开工计划](docs/coding-plan.md)

## 代码结构
```text
docs/
examples/
src/alphaconsole/
tests/
```

## 验证
```bash
uv run --with pytest pytest
```
