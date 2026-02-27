# 1. 前置环境准备
1. linux 环境
2. 确保 uv 已安装
3. 确保 http 与 https 代理已配置(能访问外网)
4. codex cli 已安装到系统中

# 2. 安装 Specify CLI
```
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

安装完后, 就可以使用命令初始化 spec kit 项目了, 但是由于本仓库已经初始化过了, 所以就不需要再初始化了

# 3. 将 codex 的配置目录指向项目的 .codex
```bash
export CODEX_HOME="$PWD/.codex"
```

# 4. 启动 codex
```bash
codex
```

