# 3D 分型总览墙

为了解决“为什么不是 3D”的问题，新增了单页 3D 总览墙：在一个 3D 场景中排列多个分型，可整体旋转/缩放对比。

## 已生成文件
- `docs/examples/type_gallery_3d_valid_2x2x2.html`
  - 已按分型类别分组，不再全量平铺。
  - 分组规则见：`docs/type_grouping.md`

## 生成命令
```bash
uv run python src/generate_type_gallery_3d.py \
  --x-cells 2 --y-cells 2 --layers 2 \
  --filter valid \
  --output-html docs/examples/type_gallery_3d_valid_2x2x2.html \
  --columns 16
```

## 参数
- `--filter valid|invalid|all`：显示有效/无效/全部分型
- `--columns`：在“分型墙”里每行摆放多少个分型
- `--x-cells --y-cells --layers`：离散边界

## 入口脚本
- `src/generate_type_gallery_3d.py`
- `src/visualization/type_gallery_3d.py`
