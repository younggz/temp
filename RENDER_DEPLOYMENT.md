# Render 部署步骤

## 1. 推送到 GitHub

本仓库需要推送到 GitHub，然后在 Render 导入。

```powershell
git init
git add .
git commit -m "Deploy Django NLP agent"
git branch -M main
git remote add origin https://github.com/younggz/temp.git
git push -u origin main
```

## 2. Render 导入项目

Render -> New -> Web Service -> 选择 GitHub 仓库。

项目中已经提供 `render.yaml` 和 `build.sh`。

如果手动填写：

```text
Build Command: ./build.sh
Start Command: gunicorn django_blog.wsgi:application
```

## 3. 必填环境变量

```text
DEBUG=0
SECRET_KEY=Render 自动生成或自己生成
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
LLM_ENABLED=1
LLM_BASE_URL=https://www.vivaapi.cn/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=你的大模型密钥
```

## 4. 数据库建议

课堂演示可以先使用默认 SQLite，但 Render 免费实例文件系统可能不会长期持久保存数据。

如果要多人长期使用，建议创建 Render PostgreSQL 或 Neon/Supabase PostgreSQL，然后配置：

```text
DATABASE_URL=postgresql://...
```

## 5. 部署后访问

部署完成后 Render 会给出：

```text
https://你的项目名.onrender.com
```

用户访问：

```text
https://你的项目名.onrender.com/
https://你的项目名.onrender.com/share/
```

API：

```text
POST https://你的项目名.onrender.com/nlp/chat/
```
