from django.db.models import Q
from blog.models import Post
from nlp.relevance import get_scorer


class Skills:

    @staticmethod
    def query_article(keyword='', count=5):
        if not keyword:
            return "请告诉我你想查找什么主题的文章？"
        terms = keyword.split()
        q = Q()
        for term in terms:
            q |= Q(title__icontains=term)
        posts = Post.objects.filter(q).distinct()
        if posts.exists():
            result = f"找到 {posts.count()} 篇关于「{keyword}」的文章：\n\n"
            for post in posts[:count]:
                result += f"[{post.id}] {post.title}\n"
                result += f"   时间：{post.created_time.strftime('%Y-%m-%d %H:%M')}\n"
                if post.tags:
                    result += f"   标签：{post.tags}\n"
                result += f"   预览：{post.content[:60]}...\n\n"
            return result
        else:
            return f"没有找到关于「{keyword}」的文章，试试其他关键词？"

    @staticmethod
    def query_article_qa(query='', top_k=5, min_confidence=0.15):
        """
        问答式搜索：使用 TF-IDF 语义相关性搜索，返回每条结果的可信度。

        Args:
            query: 用户自然语言查询（支持问句形式，如"Python列表怎么用"）
            top_k: 返回前 k 条结果
            min_confidence: 最低可信度阈值。默认过滤极低相关结果，避免把
                明显不相关的文章展示为候选答案。

        Returns:
            dict: {
                'found': bool,        # 是否找到结果
                'total': int,          # 结果数量
                'query': str,          # 原始查询
                'overall_confidence': float,  # 整体可信度（最高分）
                'results': [{          # 每条结果
                    'id': int,
                    'title': str,
                    'confidence': float,
                    'confidence_label': str,
                    'snippet': str,
                    'tags': str,
                    'created_time': str,
                }, ...],
                'text_response': str,  # 文本格式的回复（兼容旧版前端）
            }
        """
        if not query or not query.strip():
            return {
                'found': False,
                'total': 0,
                'query': query,
                'overall_confidence': 0.0,
                'results': [],
                'text_response': '请告诉我你想查询什么内容？',
            }

        try:
            scorer = get_scorer()
            search_result = scorer.search_with_confidence(
                query, top_k=top_k, min_confidence=min_confidence
            )
        except Exception as e:
            # 降级：使用传统关键词搜索
            return Skills._fallback_keyword_search(query, top_k)

        # 从数据库获取完整文章信息
        results = []
        for sr in search_result['results']:
            try:
                post = Post.objects.get(id=sr['id'])
                results.append({
                    'id': sr['id'],
                    'title': sr['title'],
                    'confidence': sr['confidence'],
                    'confidence_label': sr['confidence_label'],
                    'snippet': sr['snippet'],
                    'tags': post.tags or '',
                    'created_time': post.created_time.strftime('%Y-%m-%d %H:%M'),
                })
            except Post.DoesNotExist:
                continue

        # 构建文本回复（含可信度标记）
        text_lines = [f'关于「{query}」的搜索结果（可信度评估）：\n']
        for r in results:
            label_icon = {'高': '🟢', '中': '🟡', '低': '🔴'}
            icon = label_icon.get(r['confidence_label'], '⚪')
            text_lines.append(
                f'{icon} [{r["id"]}] {r["title"]}\n'
                f'   可信度: {r["confidence"]*100:.0f}% ({r["confidence_label"]})\n'
                f'   预览: {r["snippet"]}\n'
            )

        if not results:
            text_lines.append('没有找到高可信相关文章，试试换个关键词或换一种问法？\n')

        overall = search_result.get('overall_confidence', 0.0)

        return {
            'found': len(results) > 0,
            'total': len(results),
            'query': query,
            'overall_confidence': overall,
            'results': results,
            'text_response': '\n'.join(text_lines),
        }

    @staticmethod
    def _fallback_keyword_search(keyword='', top_k=5):
        """降级方案：使用传统 ORM 关键词搜索"""
        posts = Post.objects.all()
        if keyword:
            terms = keyword.split()
            q = Q()
            for term in terms:
                q |= Q(title__icontains=term) | Q(content__icontains=term)
            posts = posts.filter(q).distinct()

        results = []
        for post in posts[:top_k]:
            results.append({
                'id': post.id,
                'title': post.title,
                'confidence': 0.5,  # 降级模式下给中等置信度
                'confidence_label': '中',
                'snippet': post.content[:120] + ('...' if len(post.content) > 120 else ''),
                'tags': post.tags or '',
                'created_time': post.created_time.strftime('%Y-%m-%d %H:%M'),
            })

        return {
            'found': len(results) > 0,
            'total': len(results),
            'query': keyword,
            'overall_confidence': 0.5 if results else 0.0,
            'results': results,
            'text_response': f'找到 {len(results)} 篇相关文章（关键词匹配模式）' if results else '没有找到相关文章',
        }

    @staticmethod
    def get_latest_articles(count=5):
        posts = Post.objects.all()[:count]
        if posts.exists():
            result = f"最近 {count} 篇文章：\n\n"
            for i, post in enumerate(posts, 1):
                result += f"{i}. [{post.id}] {post.title}\n"
                result += f"   时间：{post.created_time.strftime('%Y-%m-%d %H:%M')}\n"
                if post.tags:
                    result += f"   标签：{post.tags}\n"
                result += f"   预览：{post.content[:60]}...\n\n"
            return result
        else:
            return "目前还没有发布任何文章哦~"

    @staticmethod
    def search_articles():
        return "我可以帮助你搜索文章！请直接告诉我你想找什么内容，比如：「帮我找Python文章」"

    @staticmethod
    def say_hello():
        return ("你好！我是智能博客助手，可以帮助你：\n\n"
                "  • 查找文章（如：帮我找Python文章）\n"
                "  • 查看最新文章（如：最新文章）\n"
                "  • 解释算法（如：有其他算法吗）\n"
                "  • 标签筛选（如：查看 Django 标签下的文章）\n"
                "  • 内容推荐（如：推荐机器学习文章）\n\n"
                "请告诉我你想做什么？")

    @staticmethod
    def explain_algorithms():
        return (
            "这个项目目前围绕「NLP 意图识别」实现了 4 个算法版本：\n\n"
            "V1 Baseline：关键词规则匹配，作为最基础的对照组。\n"
            "V2 SequenceMatcher：计算用户输入和意图模板的字符串相似度，短句效果较好。\n"
            "V3 Jieba+Jaccard：先做中文分词，再计算词集合相似度，适合中文关键词表达。\n"
            "V4 Darwin Ensemble：把 V2 和 V3 加权融合，是当前默认生产算法。\n\n"
            "真实测评结果：V4 的 F1-Score 为 0.9556，高于 V2 的 0.8958。"
            "所以系统现在默认用 V4 来识别用户意图。"
        )

    @staticmethod
    def unknown_intent():
        return ("抱歉，我没有理解你的意思。你可以：\n\n"
                "  • 说「帮我找XX文章」来搜索内容\n"
                "  • 说「最新文章」查看最新动态\n"
                "  • 说「有其他算法吗」了解项目算法\n"
                "  • 说「查看XX标签下的文章」按标签筛选\n"
                "  • 说「推荐XX文章」获取推荐\n"
                "  • 说「你好」打个招呼")

    @staticmethod
    def recommend_articles(keyword='', count=5):
        base_qs = Post.objects.all()
        if keyword:
            terms = keyword.split()
            q = Q()
            for term in terms:
                q |= Q(content__icontains=term) | Q(title__icontains=term)
            base_qs = base_qs.filter(q)
        if not base_qs.exists():
            base_qs = Post.objects.all()
        posts = base_qs.order_by('-created_time')[:count]
        if posts.exists():
            label = f"关于「{keyword}」的" if keyword else ""
            result = f"为你推荐{label}文章：\n\n"
            for i, post in enumerate(posts, 1):
                result += f"{i}. [{post.id}] {post.title}\n"
                result += f"   时间：{post.created_time.strftime('%Y-%m-%d %H:%M')}\n"
                if post.tags:
                    result += f"   标签：{post.tags}\n"
                result += f"   预览：{post.content[:60]}...\n\n"
            return result
        return "目前还没有文章可以推荐~"

    @staticmethod
    def filter_by_tag(tag='', count=10):
        if not tag:
            return "请告诉我你想查看哪个标签的文章？"
        posts = Post.objects.filter(tags__icontains=tag)
        if posts.exists():
            result = f"找到 {posts.count()} 篇标签包含「{tag}」的文章：\n\n"
            for post in posts[:count]:
                result += f"[{post.id}] {post.title}\n"
                result += f"   标签：{post.tags}\n"
                result += f"   时间：{post.created_time.strftime('%Y-%m-%d %H:%M')}\n"
                result += f"   预览：{post.content[:60]}...\n\n"
            return result
        else:
            return f"没有找到标签包含「{tag}」的文章。"

    @staticmethod
    def fallback(user_input=''):
        return (f"我不太理解「{user_input}」的含义。\n\n"
                "你可以尝试以下指令：\n"
                "  • 「帮我找Python文章」- 搜索文章\n"
                "  • 「最新文章」- 查看最新文章\n"
                "  • 「查看Django标签下的文章」- 按标签筛选\n"
                "  • 「推荐机器学习文章」- 获取推荐")
