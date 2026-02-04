<div align="center">
  <img src="image/logo.png" width="120" height="120" alt="Hoshino Logo">
  <h1>Hoshino (星野)</h1>
  <p><strong>Alpha v0.1.0 (Ether Design)</strong></p>
  <p>专为动漫爱好者打造的新一代智能媒体管理中心</p>

  <p>
    <a href="#-核心特性">核心特性</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-配置指南">配置指南</a> •
    <a href="#-技术栈">技术栈</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat-square&logo=vue.js" alt="Vue 3">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
  </p>
</div>

---

Hoshino 是一款专为动漫爱好者设计的智能媒体库整理工具。它结合了传统规则引擎与现代大语言模型 (LLM)，能够精准识别复杂的动漫文件名，并自动将其整理为规范的媒体库结构，让您的 Plex/Emby/Jellyfin 媒体库井井有条。

## ✨ 核心特性

<div align="center">
  <table>
    <tr>
      <td align="center" width="33%">
        <h3>🧠 双引擎识别</h3>
        <p>规则引擎 + LLM 大模型<br>精准理解字幕组复杂命名</p>
      </td>
      <td align="center" width="33%">
        <h3>🔄 自动追番</h3>
        <p>Mikan RSS 深度集成<br>自动订阅、下载、整理</p>
      </td>
      <td align="center" width="33%">
        <h3>🎨 现代化 UI</h3>
        <p>Ether Design 设计语言<br>流体交互与深色模式</p>
      </td>
    </tr>
  </table>
</div>

### 场景化功能介绍

- **"把番剧丢进去就行"**：无论文件名是 `[字幕组][新番][01][1080P]` 还是复杂的 `[S1][完][BDRip]`，Hoshino 都能自动识别作品名、季度和集数，并移动到标准目录结构中。
- **"下载即归档"**：深度集成 qBittorrent，下载完成瞬间触发整理，无需人工干预。
- **"不仅是整理"**：内置 TMDB 刮削，自动下载精美海报、背景图、演职人员信息，让您的媒体库赏心悦目。
- **"随时掌控"**：提供功能完整的 Web 管理界面，支持手动修正识别结果、查看下载进度、管理订阅任务。

---

## 🚀 快速开始

### 1. 准备工作 (API Keys)

在开始部署之前，您需要准备以下 API Key 以启用核心功能：

<details open>
<summary><strong>🔑 必填配置 (点击收起)</strong></summary>

| 服务            | 用途             | 获取方式                                                                                                                |
| :-------------- | :--------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **LLM API**     | 智能识别文件名   | 推荐 **OpenAI** ([获取](https://platform.openai.com/api-keys)) 或 **DeepSeek** ([获取](https://platform.deepseek.com/)) |
| **TMDB API**    | 获取海报与元数据 | 注册 [TMDB](https://www.themoviedb.org/) -> [API 设置](https://www.themoviedb.org/settings/api)                         |
| **qBittorrent** | 下载与任务管理   | 需在本地或服务器安装 qBittorrent 并开启 Web UI                                                                          |

</details>

### 2. 获取代码与初始化

```bash
# 1. 克隆项目
git clone https://github.com/YiGuMoYan/Hoshino.git
cd Hoshino

# 2. 准备配置文件
cp .env.example .env
```

### 3. 环境配置 (至关重要)

编辑 `.env` 文件，填入您的配置信息：

```ini
# --- 基础设置 ---
APP_NAME=Hoshino
# 数据库存储路径 (确保目录存在或 Docker 挂载)
SQLITE_URL=sqlite:///./data/hoshino.db

# --- 核心功能 (必须配置) ---
# 推荐使用 DeepSeek (性价比高) 或 OpenAI
OPENAI_API_KEY=sk-xxxxxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# TMDB (元数据刮削)
TMDB_API_KEY=xxxxxx

# --- 下载器设置 ---
QB_HOST=http://localhost:8080
QB_USERNAME=admin
QB_PASSWORD=adminadmin
# 这里的路径是 qBittorrent 下载文件的保存路径
DOWNLOAD_PATH=/path/to/downloads
```

### 4. 启动服务

#### 方式 A：Docker 部署 (推荐)

```bash
# 启动所有服务 (后端 + 数据库 + Worker)
docker-compose up -d
```

访问 `http://localhost:8000` 即可开始使用。

> **注意**：修改 `docker-compose.yml` 中的 volumes 映射，确保 Hoshino 能访问到您的媒体库文件夹。

#### 方式 B：源码运行

**后端准备**:

```bash
# 创建虚拟环境
conda create -n hoshino python=3.10
conda activate hoshino
pip install -r requirements.txt

# 初始化数据库
python init_db.py
```

**前端准备**:

```bash
cd web
npm install
npm run build
cd ..
```

**启动**:

```bash
# 终端 1: 启动 API 服务
python -m app.main

# 终端 2: 启动任务 Worker
python run_worker.py
```

---

## 🛠️ 技术栈

| 领域         | 技术                 | 说明                     |
| :----------- | :------------------- | :----------------------- |
| **后端**     | FastAPI              | 高性能异步框架           |
| **数据库**   | SQLite + SQLAlchemy  | 轻量可靠的存储方案       |
| **任务队列** | Huey                 | 简单强大的分布式任务处理 |
| **前端**     | Vue 3 + Vite         | 现代化响应式界面         |
| **UI**       | TailwindCSS + Shadcn | 极简美学设计             |

## 🗺️ 发展规划

- [x] **v0.5 基础版**：LLM 识别、qBittorrent 联动、基础刮削
- [ ] **v0.8 进阶版**：多用户支持、WebHoook 通知 (企业微信/FCM)
- [ ] **v1.0 正式版**：移动端 App 适配、插件系统

## 📄 开源协议

本项目采用 [MIT](./LICENSE) 协议开源。

## 🙏 致谢

- [TMDB](https://www.themoviedb.org/) - 元数据支持
- [qBittorrent](https://www.qbittorrent.org/) - 下载器支持
- [Mikanani](https://mikanani.me/) - 番剧索引支持

---

<div align="center">
  <p>Designed with ❤️ for Anime Lovers.</p>
</div>
