# 🔭 GitHub Radar

**GitHub → Obsidian 智能研究管道** — 发现 GitHub 优质仓库，用本地 LLM 深度分析，生成结构化知识库。

无需云端 API、无需数据库、不依赖 Obsidian 也可独立使用。

---

## ✨ 核心能力

```
GitHub Trending / 关键词搜索
         │
    ┌────▼────┐     ┌──────────┐     ┌──────────┐
    │ Discover │ ──▶ │  Ingest  │ ──▶ │ Analyze  │
    └─────────┘     └──────────┘     └────┬─────┘
                                          │
                                   ┌──────▼──────┐
                                   │   Memory    │
                                   │ (artifacts) │
                                   └──────┬──────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                     ┌──────────────┐        ┌──────────────┐
                     │   Web UI     │        │   Obsidian   │
                     │ (独立运行)    │        │  (可选输出)   │
                     └──────────────┘        └──────────────┘
```

- 🔍 **智能发现** — 从 GitHub Trending 和你关注的关键词中自动发现优质仓库
- 🧠 **本地分析** — 用你自己部署的 LLM 分析代码结构、创新点、学习路径
- 📊 **结构化输出** — 一键总结、关键创新、推荐行动、标签分类
- 🌐 **Web UI** — 内置 SPA 界面，搜索浏览分析结果
- 📓 **Obsidian 集成** — 可选写入 Obsidian Vault，与你的笔记系统联动

---

## 🚀 快速开始

### 下载即用（推荐）

去 [Releases](https://github.com/xiaoyoumo70-afk/Github_Radar/releases) 下载对应平台的最新版本：

| 平台 | 下载 | 说明 |
|------|------|------|
| 🐧 Linux | `github-radar-*-linux-x64.tar.gz` | 解压即用，需 Node.js 20+ |
| 🐧 Linux | `github-radar-*-linux-x64-bundled.tar.gz` | 自包含，无需安装任何依赖 |
| 🐧 Linux | `GitHub-Radar-*.AppImage` | 桌面应用，双击运行 |
| 🪟 Windows | `github-radar-*-windows-x64.zip` | 解压即用，需 Node.js 20+ |
| ⌨️ Linux CLI | `github-radar-cli` | 纯命令行，PyInstaller 打包 |

### 配置

解压后复制 `.env.example` 为 `.env`：

```bash
# GitHub Token（可选，避免 API 限流）
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# 本地 LLM 地址（OpenAI 兼容 API）
LLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=qwen3.7

# Obsidian Vault 名称（可选，不填也能用）
OBSIDIAN_VAULT=AI-Vault
```

### 启动

```bash
# Linux
./GitHub-Radar.sh          # Web UI → http://localhost:4420
./github-radar-cli.sh daily    # CLI 每日分析

# Windows
scripts\github-radar-windows.bat     # Web UI
```

---

## 🛠️ 从源码构建

```bash
git clone https://github.com/xiaoyoumo70-afk/Github_Radar.git
cd Github_Radar
npm install

# 构建 Linux 便携包
bash packaging/build-linux.sh

# 构建 Linux 自包含包（含 Node + Python 运行时）
bash packaging/build-linux-bundled.sh

# 构建 Linux 桌面应用
bash packaging/build-electron-linux.sh

# 构建 Linux CLI（需要 PyInstaller）
bash packaging/build-python-sidecar-linux.sh
```

Windows 构建请在 PowerShell 中运行对应的 `.ps1` 脚本。

---

## 📂 项目结构

```
github-radar/
├── app/                    # Python CLI 入口（Typer）
│   ├── cli.py              # analyze-repo / search-topic / daily
│   ├── scheduler.py        # 定时调度
│   └── task_runner.py      # 任务执行器
├── github_radar/           # 核心分析引擎
│   ├── discover/           # Trending + 关键词搜索 + 打分
│   ├── ingest/             # 元数据 / README / 文件树抓取
│   ├── analyze/            # LLM 分析（Snapshot / Structure / Synthesis）
│   ├── memory/             # 知识库存储（artifacts/）
│   ├── obsidian/           # Obsidian Vault 写入
│   ├── models/             # Pydantic 数据模型
│   └── storage/            # JSON 文件存储
├── server.mjs              # Web UI 服务器（零依赖，Node.js 内置模块）
├── public/index.html       # SPA 前端
├── desktop/                # Electron 桌面壳
│   ├── main.js             # Electron 主进程
│   └── python_sidecar_entry.py
├── packaging/              # 所有平台的构建脚本
├── scripts/                # 启动脚本 + Docker 辅助
с── docker/                 # Docker 入口
├── .env.example            # 配置模板
├── pyproject.toml          # Python 项目配置
├── package.json            # Node.js 项目配置
└── electron-builder.yml    # Electron 打包配置
```

---

## ⚙️ 依赖

| 组件 | 用途 | 打包时是否包含 |
|------|------|:---:|
| Node.js 20+ | Web UI 服务器 | Bundled 包含 |
| Python 3.11+ | 分析引擎 | Bundled 包含 |
| LLM (OpenAI 兼容) | 代码分析 | ❌ 需自行部署 |
| Obsidian | 笔记输出 | ❌ 可选 |

---

## 🏗️ 技术栈

- **前端**: 原生 SPA（876 行，零框架）
- **后端**: Node.js 内置 HTTP 模块（零 npm 依赖）
- **分析引擎**: Python + Typer + Pydantic + Rich
- **LLM**: OpenAI 兼容 API（Ollama / vLLM / LM Studio 等）
- **打包**: rsync + PyInstaller + electron-builder + Docker

---

## 📄 License

MIT
