
# 🎓 北邮校园智能助手 (BUPT AI Assistant)

基于 **RAG (Retrieval-Augmented Generation)** 技术的校园知识问答系统，为北京邮电大学师生提供准确、快速的校园信息查询服务。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ 功能特点

| 功能 | 说明 |
|------|------|
| 📚 **智能检索** | 基于 TF-IDF 向量检索，从校园文档中精准定位相关信息 |
| 🤖 **AI 问答** | 接入 MiMo 大模型，生成准确、自然的回答 |
| ⚡ **快速响应** | 本地 Embedding，毫秒级知识检索速度 |
| 📄 **来源溯源** | 每个回答都标注信息来源，确保可信度 |
| 🎨 **精美界面** | 深色主题 UI，支持历史对话管理 |
| 📁 **文件上传** | 支持上传 PDF/TXT 文件扩展知识库 |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/SMZXzbc/bupt-assistant.git
cd bupt-assistant
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 MiMo API Key：

```env
MIMO_API_KEY=tp-your-api-key-here
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
```

> 🔑 **获取 API Key**: [MiMo 开放平台](https://platform.xiaomimimo.com)

### 4. 启动服务

```bash
streamlit run app.py
```

浏览器访问 http://localhost:8501

---

## 📖 使用指南

### 首次使用

1. 打开网页后，点击左侧 **「加载/重新加载知识库」**
2. 等待知识库加载完成（显示"已加载 XX 块"）
3. 在底部输入框提问，或点击快捷问题按钮

### 示例问题

- 📖 "图书馆开放时间是什么？"
- 🎓 "如何办理学生证？"
- 💳 "校园卡怎么充值？"
- 🍽️ "食堂在哪里？"
- 📋 "如何选课？"
- 📝 "毕业论文要求是什么？"

---

## 📊 数据来源

| 来源 | 内容 | 文件 |
|------|------|------|
| 北邮图书馆官网 | 开放时间、借阅规则、电子资源 | `data/01_bupt_library_*.txt` |
| 北邮教务处 | 培养方案、选课通知 | `data/04_bupt_jwc_*.txt` |
| 北邮官网 | 学校概况、联系方式 | `data/06_bupt_main_*.txt` |
| 北邮信息门户 | 学生服务、校园生活 | `data/09_bupt_portal.txt` |
| 校园生活信息 | 食堂、宿舍、交通 | `data/10_bupt_campus_*.txt` |

> 📅 **数据更新日期**: 2026-05-16

---

## 🏗️ 项目架构

```
bupt-assistant/
├── 📁 data/                    # 校园知识库数据（17个文件）
├── 📁 src/                     # 核心源代码
│   ├── embedding.py            # TF-IDF 本地 Embedding
│   ├── retriever.py            # 向量检索模块
│   ├── generator.py            # MiMo API 问答生成
│   ├── loader.py               # 文档加载
│   └── splitter.py             # 文本切分
├── 📄 app.py                   # Streamlit 前端应用
├── 📄 scraper.py               # 数据爬取脚本
├── 📄 requirements.txt         # Python 依赖
├── 📄 .env.example             # 环境变量模板
└── 📄 README.md                # 项目说明
```

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.10+** | 后端开发语言 |
| **Streamlit** | 前端 Web 界面 |
| **LangChain** | RAG 框架 |
| **ChromaDB** | 向量数据库 |
| **scikit-learn** | TF-IDF 向量计算 |
| **MiMo API** | 大语言模型（LLM） |
| **BeautifulSoup** | 网页数据爬取 |

---


> 💡 **提示**: 本项目仅供学习交流使用，数据来源于北邮官网公开信息。
```

