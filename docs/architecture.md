# 架构说明

## 当前唯一主线

仓库已经切换到下面这条主线：

```text
Framework Markdown
  -> Framework IR
    -> Framework Package Registry
      -> Package Entry Classes
        -> Unified Project Config
          -> Package Compile
            -> Runtime Assembly
              -> Canonical Graph
                -> Derived Governance Views
```

这里没有并行旧主链：

- 没有旧模板分发主路径
- 没有旧双轨配置主模型
- 没有旧项目级聚合模块作为编译核心

## 分层

- Framework
  - `framework/*.md`
  - 作者源
- Package
  - `src/framework_packages/modules/*`
  - 每个 framework 文件一个 package，一个入口 class
- Config
  - `projects/<project_id>/project.toml`
  - 分成 `selection / truth / refinement / narrative`
- Code
  - `src/project_runtime/knowledge_base.py`
  - 用 registry 和 config slicing 编译 package
- Evidence
  - `projects/<project_id>/generated/canonical_graph.json`
  - 以及所有 derived views

## 机器真相源

唯一机器真相源：

- `projects/<project_id>/generated/canonical_graph.json`

它稳定记录四层：

- `layers.framework`
- `layers.config`
- `layers.code`
- `layers.evidence`

其它文件如果存在，全部都必须在内容里声明自己 `derived_from canonical_graph.json`。

## 默认项目

当前默认项目：

- [projects/knowledge_base_basic/project.toml](../projects/knowledge_base_basic/project.toml)

默认运行入口：

- [src/main.py](../src/main.py)
- [src/project_runtime/app_factory.py](../src/project_runtime/app_factory.py)
- [src/knowledge_base_runtime/app.py](../src/knowledge_base_runtime/app.py)
