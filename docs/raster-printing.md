# AlphaConsole Raster Printing（当前阶段）
## 1. 为什么采用 raster-first
当前阶段真实打印链路采用 raster-first：
- receipt text 先渲染成 image
- image 再编码成 ESC/POS raster bytes

原因：
- 当前项目已有中英文混排场景
- raster-first 不依赖具体 code page
- 先把“能稳定打出来”做稳，再考虑 text-mode 优化

## 2. 字体策略
当前阶段允许使用 `Pillow`，但不提交字体二进制文件。

规则：
1. 不 vendoring 字体文件
2. 不提交任何字体到仓库
3. 可通过 config 提供 `font_path`
4. 若未提供 `font_path`：
   - 可尝试使用 Pillow 默认字体
   - 但不保证中文可用

## 3. CI 与测试策略
当前阶段测试只要求：
- ASCII 路径稳定
- 图像尺寸稳定
- ESC/POS bytes 编码稳定
- printer profile 下的固定宽度渲染稳定

当前阶段不强制验证：
- 中文字体覆盖率
- 具体打印机的视觉精度

## 4. 当前阶段不做
- 灰度优化
- 图片缩放策略优化
- logo / QR / barcode
- 自动分页
- 长图裁切
- 字体文件打包
- 复杂 fitting / 缩放策略
