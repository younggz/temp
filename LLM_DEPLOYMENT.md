# LLM 增强意图识别部署说明

本项目现在采用混合架构：

```text
LLMIntentAnalyzer
-> V4 Darwin Ensemble fallback
-> ArticleRetriever / Skills
-> ChatLog / UserProfile
```

大模型负责开放式、口语化、复杂表达的意图理解；原有 NLP 意图识别算法继续保留，作为可解释、可测评、可离线运行的兜底能力。

## 环境变量

不要把密钥写入源码。部署时通过环境变量配置：

```powershell
$env:LLM_ENABLED="1"
$env:LLM_API_KEY="your-api-key"
$env:LLM_BASE_URL="https://www.vivaapi.cn/v1"
$env:LLM_MODEL="gpt-4o-mini"
$env:LLM_TIMEOUT="8"
python manage.py runserver 0.0.0.0:8000
```

Linux 服务器示例：

```bash
export LLM_ENABLED=1
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://www.vivaapi.cn/v1"
export LLM_MODEL="gpt-4o-mini"
python manage.py runserver 0.0.0.0:8000
```

## 运行逻辑

```text
用户输入
-> 大模型解析 intent / keywords / need_article / user_goal
-> 如果大模型置信度 >= 0.55，优先使用大模型结果
-> 如果 need_article=true，系统检索文章库并返回文章、理由、可信度
-> 如果大模型失败、未配置或置信度低，自动回退到 V4 Darwin Ensemble
-> ChatLog 记录用户意图、算法来源、回复和反馈
```

## API 返回新增字段

`POST /nlp/chat/` 会新增：

```json
{
  "routing_source": "llm",
  "intent_algorithm": "llm+v4_fallback",
  "llm_analysis": {
    "intent": "article_recommendation",
    "intent_label": "文章推荐",
    "confidence": 0.88,
    "need_article": true,
    "keywords": ["机器学习", "入门"],
    "query": "机器学习 入门",
    "user_goal": "学习机器学习入门内容"
  }
}
```

如果大模型不可用：

```json
{
  "routing_source": "local_nlp",
  "intent_algorithm": "ensemble"
}
```

## 汇报话术

本项目不是简单套壳大模型，而是 LLM + 传统 NLP 的混合架构。LLM 负责开放式语义理解，V4 Darwin Ensemble 负责可解释意图识别和离线兜底，文章检索模块负责从数据库中找出可信文章，用户画像模块负责记录不同用户的意图和反馈，从而形成个性化推荐闭环。
