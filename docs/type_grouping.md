# 分型分类规则

3D 分型墙不再直接平铺全部分型，而是按“结构族 + 每层占用单元数向量”分组。

示例（2 层）：
- `shelf + (4,4)`：SHELF 结构，第 0/1 层都占 4 格
- `frame + (0,4)`：FRAME 结构，第 0 层空，第 1 层占 4 格

排序规则：
1. 先按 family（默认 `shelf` 在前）
2. 再按 active layers（非空层数）降序
3. 再按 total cells（总占用单元）降序
4. 再按向量字典序

页面中每个组都有：
- 组框（group frame）
- 组标题（`Gxx family=... cells/layer=(...) active=... count=...`）
- 组内分型编号（`#idx`）

生成命令：
```bash
uv run python src/generate_type_gallery_3d.py \
  --x-cells 2 --y-cells 2 --layers 2 \
  --filter valid \
  --output-html docs/examples/type_gallery_3d_valid_2x2x2.html \
  --columns 12
```
