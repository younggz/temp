# 🤖 基于 NLP 意图识别的智能博客系统

## 📌 系统简介

本系统在传统 Django 博客系统基础上，引入 NLP 意图识别算法，使用户可以通过自然语言完成博客操作（如查询文章、获取最新内容等），实现从"菜单点击式交互"到"自然语言交互"的升级。

---

## 🏗️ 系统架构

```
用户（网页输入）
        ↓
前端页面（输入框）
        ↓
Django后端（views）
        ↓
意图识别模块（NLP算法）
        ↓
Agent调度模块
        ↓
Skills功能模块
        ↓
数据库（博客数据）
        ↓
返回结果（页面展示）
```

---

## 📁 项目结构

```
django_blog/
│
├── blog/                  # ⭐博客核心模块
│   ├── models.py          # 数据模型（文章）
│   ├── views.py           # 博客页面逻辑
│   ├── urls.py            # URL路由
│   └── admin.py           # 后台管理
│
├── nlp/                   # ⭐智能模块（核心创新）
│   ├── intent_recognition.py   # 意图识别算法
│   ├── agent.py                # Agent调度逻辑
│   └── skills.py               # 功能技能模块
│
├── templates/             # 前端页面模板
│   ├── base.html           # 基础模板
│   ├── index.html          # 首页
│   ├── post_list.html      # 文章列表
│   └── post_detail.html    # 文章详情
│
├── staticfiles/           # 静态文件
├── django_blog/           # Django配置
│   ├── settings.py        # 系统配置
│   ├── urls.py            # 主URL配置
│   └── wsgi.py
│
├── manage.py              # Django管理脚本
├── create_initial_data.py # 初始数据脚本
└── README.md              # 项目说明文档
```

---

## 🚀 快速启动

### 1. 安装依赖

```bash
pip install django python-docx
```

### 2. 数据库初始化

```bash
# 创建迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 创建示例数据
python create_initial_data.py
```

### 3. 启动服务

```bash
python manage.py runserver
```

访问：http://127.0.0.1:8000

---

## 📚 系统功能

### ✔ 传统博客功能

- ✅ 文章列表展示
- ✅ 文章详情查看
- ✅ 关键词搜索
- ✅ 按时间排序
- ✅ 后台管理（Django Admin）

### ✔ 智能功能（核心创新）

- ✅ 自然语言输入
- ✅ 意图识别算法
- ✅ Agent 自动调度
- ✅ Skills 功能执行
- ✅ 智能对话交互

---

## 🧠 NLP 智能模块详解

### 1️⃣ 意图识别模块（intent_recognition.py）

**功能**：判断用户输入的自然语言意图

**支持的意图**：
- `查询文章`：如"帮我找Python文章"
- `获取最新文章`：如"最新文章"
- `搜索文章`：如"搜索文章"
- `打招呼`：如"你好"

**算法优化**：
- **Baseline**：关键词匹配
- **优化方法**：SequenceMatcher 相似度匹配
- **优势**：提升语义理解能力，支持多样表达

### 2️⃣ Agent 调度模块（agent.py）

**功能**：根据意图，决定调用哪个功能

**流程**：
1. 接收用户输入
2. 调用意图识别算法
3. 根据意图选择对应的 Skill
4. 执行功能并返回结果

### 3️⃣ Skills 功能模块（skills.py）

**功能技能**：
- `query_article()`：根据关键词查询文章
- `get_latest_articles()`：获取最新文章
- `search_articles()`：搜索文章引导
- `say_hello()`：打招呼
- `unknown_intent()`：未知意图回复

---

## 💡 使用示例

### 自然语言交互

在页面底部的聊天框中输入：

1. **"你好"** → 系统回复欢迎语
2. **"帮我找Python文章"** → 系统搜索并返回Python相关文章
3. **"最新文章"** → 系统展示最近发布的文章
4. **"查找Django"** → 系统搜索Django相关内容的文章

### 传统操作

- 访问首页查看最新文章
- 点击"文章列表"查看所有文章
- 使用搜索框搜索文章
- 访问 `/admin/` 进行后台管理

---

## 🎯 系统特点

### ⭐ 特点1：算法落地
本系统不仅实现了意图识别算法，还将其嵌入实际 Web 系统中，实现从理论到应用的完整闭环。

### ⭐ 特点2：结构清晰
系统采用 Agent + Skills 架构，实现了解耦设计，具有良好的扩展性。

### ⭐ 特点3：交互升级
将传统点击式博客操作升级为自然语言交互，提高用户体验。

---

## 📊 技术栈

- **后端框架**：Django 6.0
- **数据库**：SQLite3
- **NLP算法**：SequenceMatcher 相似度匹配
- **前端**：HTML5 + CSS3 + JavaScript
- **架构模式**：Agent + Skills

---

## 🔧 扩展建议

### 算法优化
1. 引入 Sentence-BERT 句向量
2. 使用深度学习模型（如 BERT）
3. 增加更多意图类型
4. 支持多轮对话

### 功能扩展
1. 用户注册登录
2. 文章评论功能
3. 文章分类标签
4. 更多自然语言操作

---

## 📝 答辩要点

1. **系统定位**：不是"博客系统 + AI"，而是"用自然语言操作博客"的系统
2. **核心创新**：意图识别算法 + Agent 调度架构
3. **技术实现**：Baseline（关键词匹配）→ 优化（相似度算法）
4. **工程价值**：从理论到应用的完整闭环

---

## 👨‍💻 开发者信息

- 系统类型：智能博客系统
- 开发框架：Django
- 核心技术：NLP 意图识别、Agent 架构
- 适用场景：Web 开发、NLP 应用、课程设计

---

## 📞 常见问题

**Q: 如何添加更多示例文章？**  
A: 修改 `create_initial_data.py` 文件，添加更多文章数据后重新运行。

**Q: 如何训练更准确的意图识别模型？**  
A: 可以在 `intent_recognition.py` 中增加更多意图模板，或引入机器学习模型。

**Q: 如何部署到生产环境？**  
A: 建议使用 Gunicorn + Nginx 部署，数据库可迁移到 PostgreSQL。

---

**祝使用愉快！🎉**



















![image-20260422094200144](C:\Users\youngz\AppData\Roaming\Typora\typora-user-images\image-20260422094200144.png)

![image-20260422094243643](C:\Users\youngz\AppData\Roaming\Typora\typora-user-images\image-20260422094243643.png)
