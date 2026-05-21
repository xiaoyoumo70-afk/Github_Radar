# github-radar 开发日志

> 2026-05-21 → 2026-05-22

---

## v0.1.0 — 初始发布（5月21日 20:44）

### 背景
幽莫需要一个工具，能自动发现 GitHub 优质仓库，用本地 LLM 深度分析代码结构和创新点，生成结构化知识库，可选输出到 Obsidian Vault。

### 立项
- 本地路径：`/home/drawbridge/.openclaw/workspace/github-radar`
- GitHub 仓库：https://github.com/xiaoyoumo70-afk/Github_Radar
- 认证方式：GitHub CLI (`gh`) OAuth

### 项目架构
```
6 层管道：Discover → Ingest → Analyze → Memory → Web UI / Obsidian
```

| 层 | 目录 | 职责 |
|---|---|---|
| Discover | `github_radar/discover/` | Trending + GitHub Search + 打分排序 |
| Ingest | `github_radar/ingest/` | 元数据抓取 + README + 文件树 |
| Analyze | `github_radar/analyze/` | LLM 快照/结构/综合三步分析 |
| Memory | `github_radar/storage/` | JSON artifacts 存储 |
| Web | `server.mjs` + `public/index.html` | 零依赖 HTTP 服务 + SPA 前端 |
| Obsidian | `github_radar/obsidian/` | Markdown 写入 Vault（可选） |

### 打包：4 种部署形态，Linux + Windows 双兼容
- **Portable（便携包）**：tar.gz/zip，含 node_modules，解压即用
- **Bundled（自包含）**：含 Node.js + Python 运行时，无需系统依赖
- **Docker（容器）**：Dockerfile + docker-compose，完全隔离
- **Electron（桌面）**：AppImage + NSIS，双击运行，内嵌 Python 侧车

### 遇到的问题 & 解决

| 问题 | 解决 |
|------|------|
| Windows 便携包只有 79KB（缺 node_modules） | 修复 `build-windows.sh`，跳过 `.bin` 符号链接 |
| Electron AppImage 文件名含空格 | `productName` 改为 `GitHub-Radar` |
| `.gitignore` 完全缺失 | 新建 46 行规则，排除 dist/build/node_modules 等 |
| GitHub Token 过期 | 改用 `gh auth login` OAuth 认证 |
| `gh release upload` 静默卡死 | 改用 curl 直连 `uploads.github.com`，绕过代理 |

---

## v0.1.1 — 多 API 提供商（5月21日 22:25）

### 需求
原本只支持本地 LLM（`http://localhost:8000/v1`），太单调。需要支持 OpenAI 官方、DeepSeek、任意第三方。

### 实现
```
提供商预设：local / openai / deepseek / custom
```

| 提供商 | 预设地址 | API Key |
|--------|---------|:---:|
| 🏠 本地 | `http://localhost:8000/v1` | ❌ |
| 🤖 OpenAI | `https://api.openai.com/v1` | ✅ |
| 🔍 DeepSeek | `https://api.deepseek.com/v1` | ✅ |
| 🔧 自定义 | 自填（如 `http://ip:port/v1`） | ✅ |

### 改动文件（6 个，+277 行）
- `.env.example` — 新增 `LLM_PROVIDER` / `LLM_API_KEY`
- `config.py` — 提供商预设表 + `effective_base_url` 解析
- `llm_client.py` — `Authorization: Bearer` 注入
- `server.mjs` — `resolveBaseUrl()` + fetch 加 auth header
- `index.html` — 提供商下拉 + 🔗 连接测试按钮 + Key 框动态显示

### 额外修复
- 🐛 便携包 1.7GB → 89MB（`release/` 目录被误打包）
- 🐛 构建脚本补全排除项：dist-electron / dist-sidecar / build / logs / memory / .git

---

## v0.1.2 — 编辑删除 + 模型自动填充（5月21日 23:xx）

### 需求
- 项目卡片上要有删除和编辑按钮
- 设置页连接测试成功后自动填充模型

### 实现
- **✕ 删除**：前端确认弹窗 → `DELETE /api/projects/:name` → 删除 artifacts 目录
- **✎ 编辑**：弹窗 → Markdown 文本框 + 标签输入 → `PUT /api/projects/:name` → 存储 `notes.md` + `tags.json`
- **模型填充**：`testConnection()` 成功后调用 `populateModelDropdown(models)`，单模型自动选中

### 改动文件（2 个，+149 行）
- `server.mjs` — 新增 PUT 端点，GET detail 返回 notes + customTags
- `index.html` — 编辑弹窗 HTML + 删除/编辑按钮 + 模型自动选中

---

## v0.1.3 — AI 分析卡片 + 安全修复（5月22日 00:50）

### 需求
- AI 分析结果在网页上用结构化 HTML 展示，不只是甩一段 markdown
- API Key 不要通过 `/api/settings` 泄露

### 实现

**AI 分析卡片**：详情页改为彩色卡片网格布局

```
💡 一句话总结     ✨ 关键创新     ⚠️ 局限风险
📋 详细摘要       📖 推荐阅读     🏗️ 架构概览
🔬 推荐行动       🔗 相关项目     ❓ 深入问题
📝 我的备注 (Markdown)            ▶ 📄 完整报告 (可折叠)
```

**安全修复**：
- `GET /api/settings` 不再返回 `llm_api_key` / `github_token` 明文
- 改为返回 `llm_api_key_present: true/false` 布尔值
- 前端密码框显示 `•••••••• (已保存)` 占位符
- 保存时只有用户输入了新值才传输 key

### 改动文件（2 个，+163 行）
- `server.mjs` — 脱敏 settings 输出 + 返回 final_synthesis.json
- `index.html` — 重写 renderDetailView() + AI 卡片 CSS + 密码框逻辑

---

## 技术决策记录

| 决策 | 理由 |
|------|------|
| Web 前后端零框架 | 保持打包体积小 + 无供应链风险 |
| JSON artifacts 而非数据库 | 零依赖、可 git 追踪、可直接查看 |
| Obsidian 为可选输出 | 降低使用门槛，核心功能不依赖外部工具 |
| curl 直连上传替代 gh CLI | gh v2.4.0 上传大文件静默卡死 |
| API Key 不通过 API 返回 | 安全第一，F12 看不到 |
| 构建排除 release/ | 避免 1.7GB 异常（含旧版本的二次打包） |

---

## 统计数据

```
Commits:   8
Files:     81
Lines:     11,158
Releases:  4 (v0.1.0 → v0.1.3)
Assets:    6 × ~700MB per release
```

## 待办

- [ ] Windows Bundled 构建（需 Windows 环境）
- [ ] Docker 构建测试（需 Docker daemon）
- [ ] GitHub Actions CI/CD（自动构建 + 发布）
- [ ] Electron 自定义图标
- [ ] Python 3.11+ release 构建
