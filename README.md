# 🎮 AI 视频广告生成工具（基于 Google Veo v3 + Gemini）

这是一个通过调用 **Google Veo v3** 模型和 **Gemini API**，支持广告模板的 **AI 视频广告生成工具**。用户可以输入产品关键词或品牌信息，系统将智能生成视频文案，并最终生成广告影片。

---

## 🧬 功能特色

* 🎥 使用 **Google Veo v3** 模型生成真实感视频广告
* 🧹 支持**多种广告模板**（产品介绍、品牌宣传、节日促销等）
* 🧟️ 接入 **Gemini Pro API** 进行文案、镜头脚本生成
* ✍️ 用户可视化编辑生成内容
* 🌐 前后端分离架构，支持**多服务器部署**

---

## ⚙️ 技术栈

| 模块    | 技术                                  |
| ----- | ----------------------------------- |
| 前端    | React + Vite + Tailwind CSS         |
| 后端    | Python + Streamlit + Gemini API     |
| AI 模型 | Google Veo v3 (通过 Gemini 生成 prompt) |
| 部署    | Docker 分容器独立部署                      |

---

## 📁 项目结构

```
.
├── frontend/                  # React 前端
├── video-ads-generation/     # Python 后端
├── README.md
└── .gitignore
```

---

## 🚀 快速开始

### ✅ 前端（开发模式）

```bash
cd frontend
npm install
npm run dev
```

默认地址：[http://localhost:3000](http://localhost:3000)

---

### ✅ 后端（开发模式）

```bash
cd video-ads-generation
pip install -r requirements.txt
streamlit run streamlit_app.py
```

默认地址：[http://localhost:8501](http://localhost:8501)

---

## 🔐 配置 Gemini API

你需要在 `video-ads-generation/` 目录下创建 `.env` 文件，内容如下：

```
GEMINI_API_KEY=你的个人 Gemini API Key
```

Gemini API Key 可在 [Google AI Studio](https://makersuite.google.com/app/apikey) 申请。

---

## 🐳 Docker 部署

### 前端

```bash
cd frontend
docker build -t video-ads-frontend .
docker run -d -p 3000:80 video-ads-frontend
```

### 后端

```bash
cd video-ads-generation
docker build -t video-ads-backend .
docker run -d -p 8501:8501 video-ads-backend
```

---

## 📌 注意事项

* 前后端如果部署在不同服务器，前端需要通过 `.env` 设置后端 API 地址
* Google Veo API 需要个人账户授权，必须自行配置

---

## 📜 License

MIT License © 2025
