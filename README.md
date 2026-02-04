<div align="center">
  <img src="image/logo.png" width="120" height="120" alt="Hoshino Logo">
  <h1>Hoshino (星野)</h1>
  <p><strong>Alpha v0.1.0 (Ether Design)</strong></p>
  <p>专为动漫爱好者打造的新一代智能媒体管理中心</p>

  <p>
    <a href="#-核心特性">核心特性</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-发展规划">发展规划</a> •
    <a href="#-配置指南">配置指南</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat-square&logo=vue.js" alt="Vue 3">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
  </p>
</div>

---

Hoshino 是一款专为动漫爱好者设计的智能媒体库整理工具。它结合了传统规则引擎与现代大语言模型 (LLM)，能够精准识别复杂的动漫文件名，并自动将其整理为规范的媒体库结构。

## ✨ 核心特性

<div align="center">
  <table>
    <tr>
      <td align="center" width="33%">
        <h3>🧠 LLM 驱动</h3>
        <p>自研规则引擎 + AI 智能分析<br>精准识别各类复杂命名</p>
      </td>
      <td align="center" width="33%">
        <h3>🎬 自动刮削</h3>
        <p>TMDB 深度集成<br>自动获取本地化元数据与海报</p>
      </td>
      <td align="center" width="33%">
        <h3>⚡ 极速体验</h3>
        <p>Ether Design 设计语言<br>现代化流体交互与深色模式</p>
      </td>
    </tr>
  </table>
</div>

### 🎯 智能识别与整理

- **双引擎驱动**：同时利用规则引擎的速度和 LLM 的理解能力。
  - 支持标准字幕组格式：`[字幕组][作品名][集数][标签]`
  - 理解语义化季度标识（如「完」、「续」、「Kan」、「Zoku」）
  - 智能推断季度和集数范围
- **标准化整理**：按照 `首字母/标题/Season XX/标题 - SXXEXX.ext` 结构自动重命名和移动。

### 📥 全流程下载管理

- **多源支持**：支持磁力链接和种子文件 (.torrent) 上传。
- **自动闭环**：
  - **订阅自动化**：集成 Mikan (蜜柑计划) RSS，自动追番下载。
  - **智能归档**：下载完成后自动触发整理任务，实现"下载即归档"。
- **实时监控**：
  - 在 Web 界面直接管理 qBittorrent 任务。
  - 实时查看下载进度、速度和任务状态。

### 🛡️ 安全可靠

- **任务预览**：执行前预览所有文件名变更，确认无误后再执行。
- **重命名回滚**：支持一键撤销已执行的整理操作。
- **智能去重**：自动检测重复任务，避免覆盖。

## 🛠️ 技术栈

| 领域         | 技术选型            | 说明                       |
| :----------- | :------------------ | :------------------------- |
| **后端**     | FastAPI             | 高性能异步 Python Web 框架 |
| **数据库**   | SQLite + SQLAlchemy | 轻量级持久化存储           |
| **任务队列** | Huey                | 简单强大的分布式任务队列   |
| **前端**     | Vue 3 + Vite        | 现代化渐进式前端框架       |
| **UI 框架**  | TailwindCSS         | 实用优先的 CSS 框架        |
| **API 集成** | qBittorrent, TMDB   | 深度集成的第三方服务       |

## 🚀 快速开始

### 方式一：使用 Docker 部署 (推荐)

如果您安装了 Docker 和 Docker Compose，可以使用以下命令一键启动：

```bash
docker-compose up -d
```

启动后访问 `http://localhost:8000`。

> [!TIP]
> 默认会挂载当前目录下的 `data` 文件夹存储数据库，您可以修改 `docker-compose.yml` 来挂载您的实际媒体库目录。

### 方式二：手动安装

#### 1. 克隆项目

```bash
git clone https://github.com/YiGuMoYan/Hoshino.git
cd Hoshino
```

#### 2. 环境配置

**后端环境**:

```bash
# 推荐使用 Conda 或 venv
conda create -n hoshino python=3.10
conda activate hoshino
pip install -r requirements.txt
```

**前端环境**:

```bash
cd web
npm install
npm run build
```

#### 3. 运行服务

**生产模式**（推荐）：

```bash
# 1. 启动后端 API
python -m app.main

# 2. 启动任务 Worker（新终端）
python run_worker.py
```

访问 `http://localhost:8000`。

## ⚙️ 配置指南

为了获得最佳体验，请在首次启动后进入"系统设置"完成以下配置：

1.  **大模型 (LLM)**：配置 OpenAI 或兼容的 API Key (如阿里云 DashScope, DeepSeek)。这是智能识别的核心。
2.  **TMDB**：配置 TMDB API Key 以获取精美的海报和元数据。
3.  **下载器**：配置 qBittorrent 的 Web UI 地址和账号密码。
4.  **应用设置**：设置媒体库的目标存储路径。

## 🗺️ 发展规划 (Roadmap)

### ✅ 已完成

- [x] **v0.2 下载与整理联动**：qBittorrent 集成、日志系统、种子上传
- [x] **v0.3 订阅自动化**：Mikan RSS 接入、自动追番、定时整理
- [x] **v0.5 体验优化**：深色模式、完整任务闭环、回滚功能

### � 进行中

- [ ] **v1.0 移动端适配**：优化手机和平板访问体验
- [ ] **v1.0 多端通知**：企业微信 / 飞书 / 邮箱推送

### 🌟 未来愿景

- [ ] **合集归档支持**：智能识别并归档整季合集 (Batch)
- [ ] **全版本聚合**：一键检索并补全所有季度和剧场版资源

## 📄 开源协议

本项目采用 [MIT](./LICENSE) 协议开源。

## 🙏 致谢

- [TMDB](https://www.themoviedb.org/) - 提供丰富的元数据
- [qBittorrent](https://www.qbittorrent.org/) - 优秀的开源下载器
- [Mikanani](https://mikanani.me/) - 优质的动漫 RSS 索引

---

<div align="center">
  <p>Designed with ❤️ for Anime Lovers.</p>
  <p><strong>如果觉得好用，请给个 Star ⭐ 支持一下！</strong></p>
</div>
