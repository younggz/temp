# 智能博客 Agent 交付与部署说明

## 1. 项目交付形态

本项目中的 Agent 不是单独的聊天模型，而是一个可部署的 Web Agent：

```
用户口语输入
→ Web 页面 / CLI / API
→ NLPEngine Agent
→ V4 达尔文集成意图识别
→ Skills 技能调用
→ 返回结果给用户
```

可交付入口：

- Web 页面：`/`
- 扫码分享页：`/share/`
- Agent API：`/nlp/chat/`
- CLI：`python manage.py blogcli ask "你的自然语言请求"`
- Skills 清单：`agent_skills_manifest.json`

## 2. 安装依赖

```powershell
pip install -r requirements.txt
```

## 3. 初始化数据

```powershell
python manage.py migrate
python create_initial_data.py
```

## 4. 课堂演示版运行

绑定到 `0.0.0.0` 后，同一 Wi-Fi/热点/局域网下的用户可以访问。

```powershell
python manage.py runserver 0.0.0.0:8000
```

本机访问：

```text
http://127.0.0.1:8000/
```

其他设备访问：

```text
http://你的电脑IP:8000/
```

扫码页：

```text
http://你的电脑IP:8000/share/
```

## 5. 二维码使用方式

打开：

```text
http://127.0.0.1:8000/share/
```

页面会显示局域网访问链接和二维码。手机和电脑需要连接同一个 Wi-Fi、热点或局域网。

## 6. Web 用户怎么使用

用户打开首页：

```text
http://你的电脑IP:8000/
```

在聊天框输入：

```text
帮我找Python文章
有其他算法吗
最新文章
查看Python标签下的文章
推荐机器学习文章
```

系统会返回：

- 识别意图
- 意图置信度
- 使用算法
- 技能执行结果
- 文章可信度（如果是文章查询）

## 7. API 调用方式

接口：

```text
POST /nlp/chat/
```

表单参数：

```text
message=用户输入
```

示例：

```powershell
Invoke-WebRequest -Uri http://127.0.0.1:8000/nlp/chat/ `
  -Method POST `
  -Body @{ message = "有其他算法吗" }
```

返回字段：

```json
{
  "success": true,
  "message": "回复文本",
  "intent": "算法咨询",
  "intent_confidence": 0.88,
  "intent_algorithm": "ensemble",
  "intent_threshold": 0.30
}
```

## 8. CLI 调用方式

```powershell
python manage.py blogcli ask "有其他算法吗"
python manage.py blogcli ask "帮我找Python文章"
python manage.py blogcli ask "查看Python标签下的文章"
```

CLI 和 Web 使用同一个 `NLPEngine`，所以调度逻辑一致。

## 9. Skills 打包说明

Skills 清单在：

```text
agent_skills_manifest.json
```

该文件描述了 Agent 入口、API 入口、CLI 调用方式和可调用 Skills。

核心 Skills：

- `query_article_qa`
- `get_latest_articles`
- `filter_by_tag`
- `recommend_articles`
- `explain_algorithms`
- `say_hello`

## 10. 正式部署建议

课堂演示可使用 `runserver`。如果要长期给用户使用，建议：

Linux：

```text
Django + Gunicorn + Nginx
```

Windows：

```text
Django + Waitress
```

正式部署时需要修改：

```python
DEBUG = False
ALLOWED_HOSTS = ["服务器IP", "域名"]
```

并配置静态文件：

```powershell
python manage.py collectstatic
```

## 11. 验证

```powershell
python manage.py check
python manage.py test
python _run_full_optimization.py
```

当前测试覆盖：

- 首页
- 扫码页
- 达尔文演示页
- 聊天 API
- 算法咨询意图
- 文章可信度
- V4 达尔文集成算法测评

