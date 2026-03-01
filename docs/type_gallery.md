# 分型总览图与网页

已支持把多个分型放在同一张图和同一网页中对比，不需要逐张打开。

## 生成命令
```bash
uv run python src/generate_type_gallery.py \
  --x-cells 2 --y-cells 2 --layers 2 \
  --filter valid \
  --output-image docs/examples/type_gallery_valid_2x2x2.png \
  --output-html docs/examples/type_gallery_valid_2x2x2.html \
  --columns 12
```

## 已生成文件
- `docs/examples/type_gallery_valid_2x2x2.png`：一张图包含 201 个有效分型（按编号）
- `docs/examples/type_gallery_valid_2x2x2.html`：分型墙网页，可滚动查看每个分型的 canonical key
- `docs/examples/type_gallery_3d_valid_2x2x2.html`：3D 分型墙（单页多个分型，可旋转）

## 参数说明
- `--filter valid|invalid|all`：筛选有效/无效/全部分型
- `--columns`：大图每行显示的分型数量
- `--x-cells --y-cells --layers`：离散边界

## 入口脚本
- `src/generate_type_gallery.py`
