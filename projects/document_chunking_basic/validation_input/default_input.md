# 文档分块示例

这个示例用于验证 Shelf 的 document_chunking 项目实例是否能够把归一化后的 Markdown 文本切成稳定段落块，并按 1 标题 + n 正文的规则闭合成文本块。

## 输入约束

系统先按空行切出段落块，再根据标题规则识别 title/body。段落块必须保持顺序、可回溯位置和唯一的文档归属。

## 组合约束

每个文本块必须从一个标题块开始，随后吸收零个或多个连续正文块。当出现下一个标题块，或当前文档结束时，已有文本块立即闭合输出。

## 输出契约

最终结果必须保留 text_id、ordered_chunk_item_set、paragraph_block_set 和 trace_meta。每个 chunk_item 都要显式携带 title_block_id 与 body_block_id_set。
