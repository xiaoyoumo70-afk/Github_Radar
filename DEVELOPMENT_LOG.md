# GitHub Radar 开发日志

> 最后整理：2026-05-17 03:26 GMT+8  
> 项目路径：`/home/drawbridge/.openclaw/workspace/github-radar/`

---

## 1. 项目定位

**GitHub Radar** 是一个本地 GitHub 项目研究系统，目标是把 GitHub 项目发现、分析、结构化总结、Obsidian 笔记输出和桌面/容器化交付串成一条完整流水线。

当前形态已经从纯 Python CLI 演进为：

```text
GitHub Radar
├── Python 分析流水线
├── 本地 Web UI / API server
├── Docker 容器交付
├── Electron 桌面壳
├── PyInstaller Python sidecar
└── Linux / Windows 打包脚本
```

---

## 2. 当前能力总览

### 已完成

- GitHub repo/topic 搜索与候选评分
- GitHub metadata / README / tree / content select 摄入
- Snapshot / Structure / Final Synthesis 三阶段 LLM 分析
- checkpoint / resume / handoff / memory index
- Obsidian repo note 与 daily digest 输出
- 本地 Web UI：项目列表、自然语言搜索、设置页、主题切换、项目详情渲染
- 零依赖 Node API server：`server.mjs`
- LLM 搜索失败完整日志与 AI 失败原因总结
- Docker 容器化运行方案
- Electron 桌面入口
- PyInstaller Linux sidecar smoke build
- Linux/Windows portable 包脚本
- Linux bundled runtime 包脚本
- Windows bundled runtime 构建脚本

### 未完全完成 / 需真实环境验证

- Windows bundled runtime 包需要在真实 Windows PowerShell 构建验证
- Windows Electron installer 需要在真实 Windows 构建验证
- Docker image build 当前 WSL 未启用 Docker Desktop integration，脚本已完成但未本机构建
- Electron 最终 AppImage / Windows Setup 尚未完成最终 release 构建
- 正式 Python sidecar 应使用 Python 3.11+ 构建；当前 Linux sidecar 是 Python 3.10 smoke build

---

## 3. 时间线

## 2026-05-15 — Python 核心流水线

### 目标

建立 GitHub → LLM 分析 → Obsidian 输出的最小闭环。

### Phase 1 — 最小闭环

完成模块：

```text
app/cli.py
app/task_runner.py
github_radar/models/*
github_radar/storage/*
github_radar/ingest/*
github_radar/analyze/*
github_radar/obsidian/writer.py
```

能力：

- `RepoRef` 支持 `owner/repo` 和 GitHub URL 解析
- `RepoPaths` 统一 artifacts 路径
- checkpoint 状态机支持中断恢复
- GitHub metadata / README / tree 拉取
- content select 选择深读文件
- OpenAI-compatible LLM client
- JSON repair
- snapshot / structure / synthesis 三阶段分析
- Obsidian repo note 写入
- CLI 命令：`analyze-repo`, `search-topic`, `resume`

### Phase 2 — 每日自动化

完成模块：

```text
github_radar/discover/trending.py
github_radar/discover/deduplicate.py
github_radar/obsidian/digest_writer.py
app/scheduler.py
```

能力：

- GitHub Trending HTML 抓取
- 已分析项目去重
- daily digest 生成
- `daily` 调度入口

### Phase 3 — Context Rollover

完成模块：

```text
github_radar/memory/handoff.py
github_radar/memory/index.py
```

能力：

- HandoffPacket 上下文续跑契约
- MemoryIndex repo/topic/relation 三层索引

### Phase 4 — 检索与关系图

完成模块：

```text
github_radar/discover/retrieval.py
github_radar/memory/relations.py
```

能力：

- KnowledgeBase 增量同步 artifacts
- RelationGraph 从 synthesis 自动构建关系
- topic cluster 聚类发现

### 验证

```text
21 tests passed
```

覆盖：

- RepoRef 解析
- RepoPaths
- checkpoint 状态机
- 去重
- handoff 序列化
- MemoryIndex CRUD
- RelationGraph 聚类
- KnowledgeBase 空同步

---

## 2026-05-16 — Web UI、本地服务与初始打包

### Web UI

新增：

```text
public/index.html
```

能力：

- 主页面自然语言搜索框
- 设置按钮与设置弹窗
- 左侧项目菜单，可折叠
- 已分析项目列表
- 点击项目展示详情
- Obsidian 风格 Markdown 渲染
- 主题切换：light / dark / system
- 模型、API endpoint、GitHub token、Vault、主题设置

技术选择：

- 单文件 vanilla HTML/CSS/JS SPA
- Markdown 渲染使用 `marked.js` CDN

### API server

新增：

```text
server.mjs
```

设计：

- 使用 Node.js built-in `http/fs/path/url`
- 不依赖 Express
- 原因：本地 `require('express')` 失败，且为了 portable 包减少依赖

API：

```text
GET    /api/projects
GET    /api/projects/:safe_name
DELETE /api/projects/:safe_name
POST   /api/search
GET    /api/settings
PUT    /api/settings
GET    /api/models
```

### LLM 搜索兼容修复

发现：

- `qwen3.6-27b` 返回中可能 `content` 为空，主要内容在 `reasoning_content`
- JSON 可能混在 reasoning text 中

修复：

- 从 `content || reasoning_content` 取 raw
- 用 JSON-like match 从后往前尝试解析
- 避免因思考文本导致搜索失败

### 服务化部署

新增 systemd user service：

```text
~/.config/systemd/user/github-radar-ui.service
```

运行：

```text
PORT=4420
http://172.19.28.70:4420
```

验证：

```text
HTTP 200
projects=3
settings OK
models OK
service enabled + active
```

### 初始 portable 包

新增：

```text
package.json
scripts/github-radar-linux.sh
scripts/github-radar-windows.bat
scripts/github-radar-windows.ps1
scripts/install-linux-service.sh
scripts/github-radar.desktop
scripts/test-api.mjs
packaging/build-linux.sh
packaging/build-windows.sh
packaging/build-windows.ps1
packaging/README.md
```

产物：

```text
dist/github-radar-0.1.0-linux-x64.tar.gz
dist/github-radar-0.1.0-windows-x64.zip
```

说明：

- 这是 portable source/scripts 包
- 不内置 Node/Python runtime
- 不包含 `.env` / `.ui-settings.json` / artifacts / secrets

修复：

- Python 3.10 无 `tomllib`，`build-linux.sh` 改用 `grep/sed` 解析 `pyproject.toml` version
- 本机无 PowerShell，增加 Linux/WSL 兼容的 Windows zip builder：`packaging/build-windows.sh`

验证：

```text
21 passed
HTTP 200
projects 0
no concrete github token in packages
linux files 80, .env included? false
windows files 80, .env included? false
```

---

## 2026-05-16 夜间 — Bundled Runtime 包

### 目标

用户要求：不能只打源码，项目所需环境也要打包。

### Linux bundled runtime

新增：

```text
packaging/build-linux-bundled.sh
```

产物：

```text
dist/github-radar-0.1.0-linux-x64-bundled.tar.gz
```

内容：

```text
runtime/node/bin/node
runtime/node/lib/*
runtime/python/bin/python
runtime/python/lib/pythonX.Y/*
runtime/python/lib/pythonX.Y/site-packages/*
GitHub-Radar.sh
github-radar-cli.sh
README-FIRST.md
```

关键调整：

- 最初尝试 `pip install -e`，失败原因：
  - pip 代理/网络问题
  - 当前 Python 是 3.10.12，但项目声明 `requires-python >=3.11`
- 后改为复制当前 Python runtime、stdlib、必要 site-packages
- CLI 启动方式改为：

```bash
python -c 'from app.cli import main; main()'
```

原因：`app/cli.py` 定义了 `main()`，但没有 `if __name__ == "__main__"` 自动执行。

验证：

```text
Node v22.22.2
Python 3.10.12
github-radar v0.1.0
ui HTTP 200
model qwen3.6-27b
```

### Windows bundled runtime

新增：

```text
packaging/build-windows-bundled.ps1
```

设计：

- Windows 构建时下载 Node.js portable zip
- 下载 Python embeddable zip
- 安装 Python deps 到 embedded `Lib/site-packages`
- 生成：

```text
GitHub-Radar.bat
github-radar-cli.bat
README-FIRST.md
```

待验证：

- 需要真实 Windows PowerShell 环境

---

## 2026-05-16 / 2026-05-17 — Docker 容器化

### 目标

用户希望：新机打开即用，环境独立，不污染系统环境。

### 新增文件

```text
Dockerfile
.dockerignore
docker-compose.yml
docker/entrypoint.sh
packaging/CONTAINER.md
scripts/docker-start.sh
scripts/docker-start-windows.bat
scripts/docker-build-save.sh
scripts/docker-build-save.ps1
```

### 设计

容器内置：

```text
Node.js
Python
Python dependencies
GitHub Radar app code
Web UI/API server
```

宿主机只需要 Docker Desktop / Docker Engine。

数据目录：

```text
host ./data  ->  container /data
```

容器内路径：

```text
/data/.env
/data/.ui-settings.json
/data/artifacts/
/data/vaults/AI-Vault/
```

### server 路径改造

`server.mjs` 新增/使用：

```text
GITHUB_RADAR_DATA_DIR
ARTIFACTS_DIR
OBSIDIAN_VAULT_PATH
```

避免硬编码：

```text
/mnt/c/Users/B1552/Desktop/Drawbridge/AI-Vault
```

### 验证

完成：

```text
node --check server.mjs
21 passed
独立 DATA_DIR 运行验证 OK
```

未完成：

- 当前 WSL 未启用 Docker Desktop integration，`docker` 命令不可用
- Dockerfile / compose / scripts 已完成，实际 image build 待 Docker 环境验证

---

## 2026-05-17 — Electron 桌面应用 Phase 1

### 目标

让 UI 不需要用户手动打开浏览器，以桌面窗口运行。

### 新增文件

```text
desktop/main.js
electron-builder.yml
packaging/ELECTRON.md
packaging/build-electron-dev.sh
packaging/build-electron-linux.sh
packaging/build-electron-windows.ps1
package-lock.json
```

### package.json 新增

```json
{
  "main": "desktop/main.js",
  "scripts": {
    "desktop:dev": "electron .",
    "desktop:pack:linux": "electron-builder --linux AppImage tar.gz",
    "desktop:pack:windows": "electron-builder --win nsis zip"
  },
  "devDependencies": {
    "electron": "^42.1.0",
    "electron-builder": "^26.0.12"
  }
}
```

### server.mjs 改造

新增：

```js
export function startServer(options = {})
```

直接运行仍可用：

```bash
node server.mjs
```

Electron 内嵌启动也可用：

```js
import { startServer } from '../server.mjs';
await startServer({ port, host: '127.0.0.1' });
```

### Electron 行为

启动时：

1. 选择空闲 localhost port
2. 设置用户数据目录
3. 设置 artifacts/vault/env 路径
4. import `server.mjs` 并启动 API server
5. 创建 BrowserWindow
6. 加载本地 UI

用户数据目录：

```text
Linux:   ~/.config/GitHub Radar/
Windows: %APPDATA%/GitHub Radar/
macOS:   ~/Library/Application Support/GitHub Radar/
```

菜单：

```text
GitHub Radar
├── 打开数据目录
├── 显示运行时信息
├── 打开界面
└── 退出
```

### 验证

```text
node --check server.mjs
node --check desktop/main.js
server import + startServer OK
21 passed
npm run test:api -> api-ok
```

---

## 2026-05-17 — Electron Phase 2 / Python Sidecar

### 目标

Electron 桌面版不依赖系统 Python，改为调用 PyInstaller sidecar。

### 新增文件

```text
desktop/python_sidecar_entry.py
packaging/build-python-sidecar-linux.sh
packaging/build-python-sidecar-windows.ps1
```

### sidecar 入口

`desktop/python_sidecar_entry.py`：

```python
from app.cli import main as cli_main
cli_main()
```

并处理：

- dev/frozen import path
- `GITHUB_RADAR_DATA_DIR` 到 `ARTIFACTS_DIR` 的映射

### 构建产物

本机 Linux smoke build：

```text
dist-sidecar/linux/github-radar-cli
```

大小：

```text
46M
```

验证：

```bash
./dist-sidecar/linux/github-radar-cli version
# github-radar v0.1.0
```

注意：

- 当前构建用 Python 3.10.12
- 正式 release 应使用 Python 3.11+，匹配 `pyproject.toml`

### server.mjs 新增 sidecar API

```text
GET  /api/runtime
POST /api/analyze-repo
```

`/api/runtime` 返回：

```json
{
  "data_dir": "...",
  "artifacts_dir": "...",
  "sidecar_path": "...",
  "sidecar_found": true
}
```

`/api/analyze-repo` 调用：

```text
GITHUB_RADAR_SIDECAR_PATH analyze-repo owner/repo
```

### Electron sidecar 识别

开发环境：

```text
dist-sidecar/linux/github-radar-cli
dist-sidecar/win/github-radar-cli.exe
```

打包后：

```text
resources/sidecar/linux/github-radar-cli
resources/sidecar/win/github-radar-cli.exe
```

### 验证

```text
python3 desktop/python_sidecar_entry.py version
npm run sidecar:linux
./dist-sidecar/linux/github-radar-cli version
/api/runtime sidecar_found=true
/api/analyze-repo 参数校验 OK
21 passed
npm run test:api -> api-ok
```

---

## 2026-05-17 — 搜索失败日志与 AI 总结

### 目标

用户要求：搜索失败时报告完整失败日志，并由 AI 总结失败原因。

### server.mjs 新增

日志文件：

```text
GITHUB_RADAR_DATA_DIR/logs/search-errors.log
```

搜索失败时记录：

```text
failure id
time
query
data_dir
artifacts_dir
脱敏 settings
project_count
response_status
error message / stack
LLM raw message
HTTP response text
完整 prompt
```

脱敏策略：

```json
{"github_token_present": true}
```

不写真实 token。

### AI 总结

失败后调用当前 LLM，总结：

- 最可能原因
- 证据
- 修复建议

如果 LLM 本身不可用，则返回本地兜底总结，不吞日志。

### 前端新增

`public/index.html` 搜索失败页显示：

```text
失败 ID
日志路径
错误信息
AI 总结失败原因
完整失败日志
复制完整日志按钮
```

### 验证

模拟坏 endpoint：

```text
llm_base_url=http://127.0.0.1:9/v1
```

结果：

```text
HTTP 500
error=search_failed
failure_id=true
log_path=.../logs/search-errors.log
summary_ok=false
has_log=true
token_leak=false
log-file-ok
```

---

## 4. 当前主要文件清单

### Core Python

```text
app/cli.py
app/task_runner.py
app/scheduler.py
github_radar/models/*
github_radar/storage/*
github_radar/discover/*
github_radar/ingest/*
github_radar/analyze/*
github_radar/memory/*
github_radar/obsidian/*
```

### UI / API

```text
server.mjs
public/index.html
scripts/test-api.mjs
```

### Electron

```text
desktop/main.js
desktop/python_sidecar_entry.py
electron-builder.yml
packaging/ELECTRON.md
```

### Docker

```text
Dockerfile
.dockerignore
docker-compose.yml
docker/entrypoint.sh
packaging/CONTAINER.md
scripts/docker-start.sh
scripts/docker-start-windows.bat
scripts/docker-build-save.sh
scripts/docker-build-save.ps1
```

### Packaging

```text
packaging/build-linux.sh
packaging/build-windows.sh
packaging/build-windows.ps1
packaging/build-linux-bundled.sh
packaging/build-windows-bundled.ps1
packaging/build-python-sidecar-linux.sh
packaging/build-python-sidecar-windows.ps1
packaging/build-electron-dev.sh
packaging/build-electron-linux.sh
packaging/build-electron-windows.ps1
packaging/README.md
```

---

## 5. 关键设计决策

1. **不做全仓读取**  
   使用 metadata → README → tree → selected files → staged analysis，避免大 repo 直接爆上下文。

2. **checkpoint 优先**  
   每个阶段写状态，失败可 resume。

3. **Obsidian 不写插件**  
   优先使用 CLI/文件写入，降低集成复杂度。

4. **Web server 零依赖**  
   `server.mjs` 使用 Node built-ins，不依赖 Express，方便 portable/bundled/container/electron 共用。

5. **用户数据与程序分离**  
   container 使用 `/data`；Electron 使用 `app.getPath('userData')`。

6. **secrets 不打包**  
   `.env`、`.ui-settings.json`、真实 token、artifacts 默认排除。

7. **桌面版采用 Electron + Python sidecar**  
   Electron 负责 UI/窗口/server 生命周期；Python 分析器由 PyInstaller sidecar 提供。

8. **容器版保留**  
   Docker 更适合技术用户、服务器、可复现环境；Electron 更适合普通桌面用户。

9. **失败可诊断**  
   搜索失败不静默 fallback，而是写完整日志 + AI 总结，方便快速定位 API、模型、JSON 输出问题。

---

## 6. 安全审查

| 项目 | 当前结论 |
|---|---|
| Token 泄漏 | 未发现真实 token 打包；搜索失败日志只记录 token 是否存在 |
| Shell 注入 | Python subprocess 使用 list 参数；sidecar spawn 使用参数数组 |
| 路径穿越 | 项目详情删除检查 `..` 与 `/`；RepoPaths 集中管理 |
| 不安全反序列化 | 仅 JSON parse，无 pickle |
| 原子写入 | Python artifacts 使用 tempfile + os.replace |
| 用户数据隔离 | Docker `/data`，Electron userData |
| 包内 secrets | `.env`、`.ui-settings.json` 默认排除 |

---

## 7. 当前验证记录

最近通过：

```text
PYTHONPATH=. python3 -m pytest tests/ -q
# 21 passed

npm run test:api
# projects=3
# model=qwen3.6-27b
# detail=sindresorhus/awesome; markdown=1618
# api-ok

node --check server.mjs
node --check desktop/main.js

./dist-sidecar/linux/github-radar-cli version
# github-radar v0.1.0
```

搜索失败日志验证：

```text
HTTP 500
error search_failed
failure_id true
log_path .../logs/search-errors.log
summary_ok false
has_log true
token_leak false
log-file-ok
```

---

## 8. 待办

### 高优先级

- [ ] 在真实 Docker 环境构建并运行 container image
- [ ] 用 Python 3.11+ 重新构建正式 Linux sidecar
- [ ] 在真实 Windows 环境构建 Windows sidecar
- [ ] 构建 Electron Linux AppImage / tar.gz
- [ ] 构建 Electron Windows NSIS installer / zip
- [ ] Electron 桌面版端到端测试：搜索 → 分析 repo → 写 artifacts → 展示项目详情

### 中优先级

- [ ] UI 增加首次启动配置向导
- [ ] `/api/analyze-repo` 接入前端按钮/表单
- [ ] search failure 日志增加下载按钮
- [ ] 设置页增加 data dir / runtime / sidecar 状态展示
- [ ] 将 `marked.js` vendored 到本地，避免离线 UI 依赖 CDN

### 低优先级

- [ ] 为 Docker/Electron 添加图标
- [ ] 增加自动更新策略调研
- [ ] 给 release 包生成 SHA256 checksum
- [ ] 增加 release checklist

---

## 9. 推荐发布路线

### v0.1 Developer Preview

```text
portable linux/windows zip/tar
Docker source compose
```

适合开发者验证。

### v0.2 Runtime Bundled

```text
linux bundled runtime tar.gz
windows bundled runtime zip
container image tar
```

适合技术用户离线部署。

### v0.3 Desktop Preview

```text
Linux AppImage
Windows Setup.exe
Electron + Python sidecar
```

适合普通用户。

### v1.0

```text
首次启动配置向导
稳定 sidecar
离线 UI assets
完整错误诊断
真实 Windows/Linux 验证
```

---

## 10. 总结

GitHub Radar 已经从最初的 Python 研究流水线，扩展为一个具备 UI、API、容器化、桌面化和失败诊断能力的完整本地应用雏形。

当前最重要的下一步不是继续堆功能，而是完成 **真实环境 release 验证**：

```text
Docker build/run
Python 3.11 sidecar
Electron AppImage
Windows installer
端到端分析任务
```
