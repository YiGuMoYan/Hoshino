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

在开始部署之前，建议准备以下 API Key 以获得最佳体验 (可在系统设置中填写)：

<details>
<summary><strong>🔑 推荐配置 (点击展开)</strong></summary>

| 服务         | 用途             | 获取方式                                                                                                                |
| :----------- | :--------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **LLM API**  | 智能识别文件名   | 推荐 **OpenAI** ([获取](https://platform.openai.com/api-keys)) 或 **DeepSeek** ([获取](https://platform.deepseek.com/)) |
| **TMDB API** | 获取海报与元数据 | 注册 [TMDB](https://www.themoviedb.org/) -> [API 设置](https://www.themoviedb.org/settings/api)                         |

</details>

### 2. 环境配置与启动

#### 方式 A：Docker 部署 (推荐)

直接使用 Docker Compose 启动：

```bash
docker-compose up -d
```

> **注意**：默认数据存储在 `./data` 目录。请确保 `docker-compose.yml` 中的卷挂载指向您实际的媒体库和下载目录。

#### 方式 B：源码手动安装

**后端环境**:

```bash
# 推荐使用 Conda 或 venv
conda create -n hoshino python=3.10
conda activate hoshino
pip install -r requirements.txt

# 初始化数据库
python init_db.py
```

**前端环境**:

```bash
cd web
npm install
npm run build
```

**启动服务**:

```bash
# 终端 1: 启动后端 API
python -m app.main

# 终端 2: 启动任务 Worker
python run_worker.py
```

### 3. 系统配置 (Web UI)

启动后访问 `http://localhost:8000` 进入管理界面。

请点击左侧菜单底部的 **"系统设置" (System Settings)** 完成配置：

1.  **大模型配置**：填入您的 API Key 和 Base URL (支持 OpenAI 格式的各种模型)。
2.  **TMDB 配置**：填入 API Key 以启用封面刮削。
3.  **下载器配置**：配置 qBittorrent 的地址和账号密码，实现自动下载。
4.  **应用设置**：指定媒体库整理的目标路径。

---

## 🛠️ 技术栈

| 领域         | 技术                 | 说明                     |
| :----------- | :------------------- | :----------------------- |
| **后端**     | FastAPI              | 高性能异步框架           |
| **数据库**   | SQLite + SQLAlchemy  | 轻量可靠的存储方案       |
| **任务队列** | Huey                 | 简单强大的分布式任务处理 |
| **前端**     | Vue 3 + Vite         | 现代化响应式界面         |
| **UI**       | TailwindCSS + Shadcn | 极简美学设计             |

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
