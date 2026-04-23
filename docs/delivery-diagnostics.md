# AlphaConsole Delivery Diagnostics（当前阶段）
## 1. 目标
当前阶段允许为每次 delivery 记录最小 diagnostics，用于联调、观察和失败定位。

## 2. 当前阶段建议记录
- adapter name
- target id
- printer profile name
- render profile name
- transport
- bytes length
- duration
- succeeded
- error text

## 3. SQLite 中的角色
这些字段进入 SQLite 不是为了历史 UI，而是为了：
- operator 诊断
- calibration 对比
- 真机联调
- 失败定位

## 4. 当前阶段不做
- 自动修复
- retry
- resend
- fallback
- recovery
- 补打
