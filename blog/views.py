from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Avg, Count
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatLog, Post, FailedLog
from nlp.agent import Agent
from nlp.engine import NLPEngine
from nlp.skill_adapter import SkillAdapter, AgentCapability, ModelCapability
from nlp.skill_router import SkillRouter
from nlp.skill_compiler import SkillCompiler
from nlp.agent_capability import AgentCapabilityRegistry
from nlp.intent_optimization import IntentOptimizationSkill
from io import BytesIO
import socket


ARTICLE_DRAFT_SESSION_KEY = 'article_creation_draft'


DEMO_USERNAME = 'demo'
DEMO_PASSWORD = 'Demo@123456'


def _ensure_demo_user():
    user, created = User.objects.get_or_create(username=DEMO_USERNAME)
    if created or not user.has_usable_password():
        user.set_password(DEMO_PASSWORD)
        user.save()
    return user


def login_view(request):
    """用户登录页。"""
    next_url = request.GET.get('next') or request.POST.get('next') or '/'
    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        if request.POST.get('demo_login') == '1':
            _ensure_demo_user()
            username = DEMO_USERNAME
            password = DEMO_PASSWORD
        else:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        messages.error(request, '用户名或密码不正确')

    return render(request, 'accounts/login.html', {
        'next': next_url,
        'demo_username': DEMO_USERNAME,
        'demo_password': DEMO_PASSWORD,
    })


def register_view(request):
    """用户注册页。"""
    next_url = request.GET.get('next') or request.POST.get('next') or '/'
    if request.user.is_authenticated:
        return redirect(next_url)

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url)
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


def logout_view(request):
    """退出登录。"""
    logout(request)
    return redirect('/accounts/login/?next=/share/')


@login_required
def profile_view(request):
    """用户智能画像与个性化反馈分析页。"""
    logs = ChatLog.objects.filter(user=request.user)
    total_chats = logs.count()
    avg_confidence = logs.aggregate(value=Avg('confidence'))['value'] or 0
    helpful_count = logs.filter(is_helpful=True).count()
    feedback_count = logs.filter(is_helpful__isnull=False).count()
    helpful_rate = helpful_count / feedback_count if feedback_count else 0
    low_confidence_logs = FailedLog.objects.filter(user=request.user)

    intent_rows = list(
        logs.values('predicted_intent')
        .annotate(count=Count('id'), avg_confidence=Avg('confidence'))
        .order_by('-count', 'predicted_intent')[:8]
    )
    top_intent = intent_rows[0]['predicted_intent'] if intent_rows else '暂无'
    for row in intent_rows:
        row['percent'] = round(row['count'] * 100 / total_chats) if total_chats else 0
        row['avg_percent'] = round((row['avg_confidence'] or 0) * 100)

    if total_chats == 0:
        suggestion = '还没有对话数据。先使用智能助手提问几次，系统会自动生成用户画像。'
    elif low_confidence_logs.count() > 0:
        suggestion = '该用户存在低置信意图样本，建议把这些表达补充到意图识别测试集，继续优化 V4 Ensemble。'
    elif avg_confidence < 0.6:
        suggestion = '该用户平均置信度偏低，建议扩充同义词、口语表达和领域关键词。'
    else:
        suggestion = '该用户意图识别较稳定，可基于高频意图继续做个性化文章推荐。'

    return render(request, 'profile.html', {
        'total_chats': total_chats,
        'avg_confidence_percent': round(avg_confidence * 100),
        'feedback_count': feedback_count,
        'helpful_rate_percent': round(helpful_rate * 100),
        'low_confidence_count': low_confidence_logs.count(),
        'top_intent': top_intent,
        'intent_rows': intent_rows,
        'recent_logs': logs[:10],
        'failed_logs': low_confidence_logs[:8],
        'suggestion': suggestion,
    })


@login_required
def index(request):
    """首页 - 展示文章列表"""
    posts = Post.objects.all()[:10]
    return render(request, 'index.html', {'posts': posts})


@login_required
def post_list(request):
    """文章列表页"""
    posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts})


@login_required
def post_detail(request, pk):
    """文章详情页"""
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'post_detail.html', {'post': post})


@login_required
def search(request):
    """搜索功能"""
    keyword = request.GET.get('keyword', '')
    if keyword:
        posts = Post.objects.filter(title__icontains=keyword)
    else:
        posts = Post.objects.all()
    return render(request, 'post_list.html', {'posts': posts, 'keyword': keyword})


def _get_lan_ip():
    """获取课堂演示常用的局域网 IPv4 地址。"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


@login_required
def share(request):
    """用户交付入口：展示可访问地址和二维码。"""
    host = request.get_host()
    operator_mode = (
        host.startswith('127.0.0.1')
        or host.startswith('localhost')
        or request.GET.get('qr') == '1'
    )
    configured_site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
    if configured_site_url:
        public_url = f'{configured_site_url}/share/'
        api_url = f'{configured_site_url}/nlp/chat/'
    elif operator_mode:
        port = host.split(':')[1] if ':' in host else '8000'
        public_host = f'{_get_lan_ip()}:{port}'
        public_url = f'http://{public_host}/share/'
        api_url = f'http://{public_host}/nlp/chat/'
    else:
        proto = request.headers.get('x-forwarded-proto') or ('https' if host.endswith('.onrender.com') else request.scheme)
        public_url = f'{proto}://{host}/share/'
        api_url = f'{proto}://{host}/nlp/chat/'
    if not operator_mode and not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next={request.path}')
    return render(request, 'share.html', {
        'public_url': public_url,
        'qr_url': f'/share/qr.png?url={public_url}',
        'api_url': api_url,
        'operator_mode': operator_mode,
    })


def share_qr(request):
    """生成分享链接二维码。"""
    url = request.GET.get('url') or f'http://{request.get_host()}/'
    try:
        import qrcode
        img = qrcode.make(url)
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    except Exception:
        return HttpResponse(url, content_type='text/plain; charset=utf-8')


def _build_user_profile_summary(user):
    if not user.is_authenticated:
        return {}

    logs = ChatLog.objects.filter(user=user)
    recent_logs = logs[:5]
    intent_rows = (
        logs.values('predicted_intent')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    return {
        'username': user.username,
        'recent_inputs': [item.user_input for item in recent_logs],
        'top_intents': [
            {'intent': row['predicted_intent'], 'count': row['count']}
            for row in intent_rows
        ],
    }


def _truncate_for_log(text, limit=500):
    text = text or ''
    return text[:limit]


def _save_chat_log(request, user_input, intent, confidence, algorithm, response_text):
    return ChatLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        user_input=_truncate_for_log(user_input),
        predicted_intent=intent,
        confidence=confidence,
        algorithm=algorithm,
        response_text=response_text,
    )


def _chat_response(request, user_input, message, intent, confidence=1.0, algorithm='skill'):
    chat_log = _save_chat_log(
        request=request,
        user_input=user_input,
        intent=intent,
        confidence=confidence,
        algorithm=algorithm,
        response_text=message,
    )
    return {
        'success': True,
        'message': message,
        'intent': intent,
        'intent_confidence': confidence,
        'intent_algorithm': algorithm,
        'intent_threshold': 0,
        'low_confidence': False,
        'routing_source': 'skill',
        'chat_log_id': chat_log.id,
    }


def _is_article_create_start(text):
    triggers = [
        '创建文章', '发布文章', '新增文章', '写文章', '发文章',
        '投稿', '新建文章', '帮我发布', '我要发布',
    ]
    return any(trigger in text for trigger in triggers)


def _is_skill_help_request(text):
    triggers = ['技能列表', '所有skill', '全部skill', '全部技能', '能做什么', '你会什么']
    return any(trigger in text for trigger in triggers)


def _build_skill_help_message():
    return (
        "当前输入框可以直接调度这些 skill：\n\n"
        "1. 文章检索：例如“帮我找 Python 文章”。\n"
        "2. 最新文章：例如“最新文章”。\n"
        "3. 标签筛选：例如“查看 Django 标签下的文章”。\n"
        "4. 个性化推荐：例如“推荐机器学习入门文章”。\n"
        "5. 算法解释：例如“意图识别算法是什么”。\n"
        "6. 创建公开文章：发送“创建文章”，我会依次让你输入标题和内容，最后发送“发送”完成发布。\n\n"
        "发布后的文章会写入网站文章库，所有账号都可以在首页和文章列表看到。"
    )


def _handle_article_creation(request, user_input):
    text = (user_input or '').strip()
    draft = request.session.get(ARTICLE_DRAFT_SESSION_KEY)

    if text in {'取消', '退出', '停止'} and draft:
        request.session.pop(ARTICLE_DRAFT_SESSION_KEY, None)
        request.session.modified = True
        return _chat_response(
            request, user_input, '已取消本次文章创建。你可以重新发送“创建文章”开始。',
            '创建文章', 1.0, 'create_article_skill'
        )

    if not draft and _is_article_create_start(text):
        request.session[ARTICLE_DRAFT_SESSION_KEY] = {'step': 'title'}
        request.session.modified = True
        return _chat_response(
            request,
            user_input,
            '好的，我来帮你发布一篇所有账号都能看到的公开文章。\n\n请先发送文章标题。',
            '创建文章',
            1.0,
            'create_article_skill',
        )

    if not draft:
        return None

    step = draft.get('step')
    if step == 'title':
        if len(text) < 2:
            return _chat_response(
                request, user_input, '标题太短了，请重新发送一个更完整的文章标题。',
                '创建文章', 0.9, 'create_article_skill'
            )
        draft['title'] = text[:200]
        draft['step'] = 'content'
        request.session[ARTICLE_DRAFT_SESSION_KEY] = draft
        request.session.modified = True
        return _chat_response(
            request,
            user_input,
            f'标题已记录：{draft["title"]}\n\n现在请发送文章内容。内容可以直接粘贴一整段，写完后直接发出来即可。',
            '创建文章',
            1.0,
            'create_article_skill',
        )

    if step == 'content':
        if len(text) < 10:
            return _chat_response(
                request, user_input, '内容太短了，请发送更完整的文章正文。',
                '创建文章', 0.9, 'create_article_skill'
            )
        draft['content'] = text
        draft['step'] = 'confirm'
        request.session[ARTICLE_DRAFT_SESSION_KEY] = draft
        request.session.modified = True
        return _chat_response(
            request,
            user_input,
            (
                f'文章内容已记录。\n\n'
                f'标题：{draft["title"]}\n'
                f'正文长度：{len(text)} 字\n\n'
                '确认发布到网站，请发送：发送\n'
                '如果不想发布，请发送：取消'
            ),
            '创建文章',
            1.0,
            'create_article_skill',
        )

    if step == 'confirm':
        if text in {'发送', '发布', '确认', '提交'}:
            post = Post.objects.create(
                title=draft.get('title', '未命名文章'),
                content=draft.get('content', ''),
                tags='用户发布,智能助手',
                category='用户发布',
            )
            request.session.pop(ARTICLE_DRAFT_SESSION_KEY, None)
            request.session.modified = True
            try:
                from nlp.relevance import rebuild_index
                rebuild_index()
            except Exception:
                pass
            return _chat_response(
                request,
                user_input,
                (
                    f'发布成功！文章已经发布到网站，所有账号都可以看到。\n\n'
                    f'标题：{post.title}\n'
                    f'文章链接：/post/{post.id}/\n\n'
                    '你可以继续让我检索文章、推荐内容，或者再次发送“创建文章”发布下一篇。'
                ),
                '创建文章',
                1.0,
                'create_article_skill',
            )

        return _chat_response(
            request,
            user_input,
            '如果确认发布，请发送“发送”。如果放弃本次创建，请发送“取消”。',
            '创建文章',
            0.9,
            'create_article_skill',
        )

    request.session.pop(ARTICLE_DRAFT_SESSION_KEY, None)
    request.session.modified = True
    return _chat_response(
        request, user_input, '文章创建状态已重置。请重新发送“创建文章”开始。',
        '创建文章', 0.8, 'create_article_skill'
    )


@csrf_exempt
def nlp_chat(request):
    """
    NLP 智能交互接口（含 QA 可信度评估）
    
    返回格式（含结构化可信度数据）：
    {
        'success': bool,
        'message': str,          # 文本回复（含可信度标记）
        'intent': str,           # 识别的意图
        'intent_confidence': float,  # 意图识别置信度
        'low_confidence': bool,  # 意图是否低置信度
        'qa_result': {           # 结构化 QA 结果（搜索文章时存在）
            'query': str,
            'total': int,
            'overall_confidence': float,
            'results': [{
                'id': int,
                'title': str,
                'confidence': float,      # 可信度 0~1
                'confidence_label': str,  # '高'/'中'/'低'
                'snippet': str,
                'tags': str,
            }, ...]
        } | None
    }
    """
    if request.method == 'POST':
        user_input = request.POST.get('message', '')
        
        # 使用 NLP Engine 处理（支持 QA + 可信度）
        article_response = _handle_article_creation(request, user_input)
        if article_response:
            return JsonResponse(article_response)

        if _is_skill_help_request(user_input):
            return JsonResponse(_chat_response(
                request,
                user_input,
                _build_skill_help_message(),
                '技能列表',
                1.0,
                'skill_catalog',
            ))

        engine = NLPEngine()
        result_data = engine.process(
            user_input,
            user_profile=_build_user_profile_summary(request.user),
        )
        
        intent_confidence = result_data['confidence']
        response_text = result_data['response']
        qa_result = result_data.get('qa_result')
        
        # 构建响应
        response = {
            'success': True,
            'message': response_text,
            'intent': result_data['intent'],
            'intent_confidence': intent_confidence,
            'intent_algorithm': result_data.get('algorithm', ''),
            'intent_threshold': result_data.get('threshold', 0),
            'low_confidence': False,
            'routing_source': result_data.get('routing_source', 'local_nlp'),
        }
        if result_data.get('freeform_analysis'):
            response['freeform_analysis'] = result_data['freeform_analysis']
        if result_data.get('llm_analysis'):
            response['llm_analysis'] = result_data['llm_analysis']

        chat_log = _save_chat_log(
            request=request,
            user_input=user_input,
            intent=result_data['intent'],
            confidence=intent_confidence,
            algorithm=result_data.get('algorithm', ''),
            response_text=response_text,
        )
        response['chat_log_id'] = chat_log.id
        
        # 附带结构化 QA 数据（前端用于显示可信度进度条）
        if qa_result:
            response['qa_result'] = {
                'query': qa_result['query'],
                'total': qa_result['total'],
                'overall_confidence': qa_result['overall_confidence'],
                'results': [
                    {
                        'id': r['id'],
                        'title': r['title'],
                        'confidence': r['confidence'],
                        'confidence_label': r['confidence_label'],
                        'snippet': r['snippet'],
                        'tags': r.get('tags', ''),
                    }
                    for r in qa_result.get('results', [])
                ],
            }
        
        # 如果意图识别置信度低于阈值，记录日志
        if intent_confidence < 0.3:
            failed_log = FailedLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                user_input=_truncate_for_log(user_input, 200),
                predicted_intent=result_data['intent'],
                confidence=intent_confidence
            )
            response['low_confidence'] = True
            response['log_id'] = failed_log.id
        
        return JsonResponse(response)
    
    return JsonResponse({'success': False, 'message': '无效的请求'})


@csrf_exempt
def feedback(request):
    """处理用户反馈"""
    if request.method == 'POST':
        log_id = request.POST.get('log_id')
        chat_log_id = request.POST.get('chat_log_id')
        is_correct = request.POST.get('is_correct') == 'true'

        if chat_log_id:
            ChatLog.objects.filter(
                id=chat_log_id,
                user=request.user if request.user.is_authenticated else None,
            ).update(is_helpful=is_correct)

        if not log_id:
            return JsonResponse({'success': True, 'message': '感谢您的反馈，系统已记录。'})

        try:
            log = FailedLog.objects.get(id=log_id)
            if is_correct:
                # 如果用户确认意图是对的，只是系统没识别出来
                # 这里可以加入自动学习逻辑，比如把这句话加入模板
                log.is_corrected = True
                log.save()
                return JsonResponse({'success': True, 'message': '感谢您的反馈，系统已记录！'})
            else:
                log.delete()
                return JsonResponse({'success': True, 'message': '已忽略该记录。'})
        except FailedLog.DoesNotExist:
            return JsonResponse({'success': False, 'message': '记录不存在。'})

    return JsonResponse({'success': False, 'message': '无效的请求'})


# ==================== 技能适配演示相关视图 ====================

@login_required
def skill_demo(request):
    """技能适配演示首页"""
    return render(request, 'skill_demo/index.html')


def skill_demo_api(request):
    """技能适配演示API"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        action = data.get('action', '')
        
        if action == 'list_skills':
            return JsonResponse(get_all_skills_info(), safe=False)
        
        elif action == 'list_agents':
            return JsonResponse(get_agents_info(), safe=False)
        
        elif action == 'list_models':
            return JsonResponse(get_models_info(), safe=False)
        
        elif action == 'check_compatibility':
            skill_name = data.get('skill_name', '')
            agent_key = data.get('agent_key', 'basic')
            model_key = data.get('model_key', 'small')
            
            result = check_skill_compatibility(skill_name, agent_key, model_key)
            return JsonResponse(result)
        
        elif action == 'compile_skill':
            skill_name = data.get('skill_name', '')
            agent_key = data.get('agent_key', 'basic')
            model_key = data.get('model_key', 'small')
            
            result = compile_skill_demo(skill_name, agent_key, model_key)
            return JsonResponse(result)
        
        elif action == 'compare_agents':
            agent_keys = data.get('agent_keys', ['basic', 'standard', 'advanced'])
            result = compare_agents_demo(agent_keys)
            return JsonResponse(result)
        
        elif action == 'compare_models':
            model_keys = data.get('model_keys', ['small', 'medium', 'large'])
            result = compare_models_demo(model_keys)
            return JsonResponse(result)
        
        elif action == 'run_optimization':
            opt_type = data.get('optimization_type', 'full_report')
            result = run_intent_optimization(opt_type)
            return JsonResponse(result)
    
    return JsonResponse({'success': False, 'message': '无效的请求'})


def get_all_skills_info():
    """获取所有技能信息"""
    adapter = create_demo_skill_adapter()
    skills = adapter.list_skills()
    return {
        'success': True,
        'skills': skills,
        'count': len(skills)
    }


def get_agents_info():
    """获取所有Agent信息"""
    registry = AgentCapabilityRegistry()
    agents = registry.list_agents()
    return {
        'success': True,
        'agents': agents,
        'count': len(agents)
    }


def get_models_info():
    """获取所有模型信息"""
    registry = AgentCapabilityRegistry()
    models = registry.list_models()
    return {
        'success': True,
        'models': models,
        'count': len(models)
    }


def check_skill_compatibility(skill_name, agent_key, model_key):
    """检查技能兼容性"""
    adapter = create_demo_skill_adapter()
    registry = AgentCapabilityRegistry()
    
    agent_profile = registry.get_agent(agent_key)
    model_profile = registry.get_model(model_key)
    
    if not agent_profile or not model_profile:
        return {
            'success': False,
            'message': 'Agent或模型不存在'
        }
    
    if skill_name not in adapter.skills:
        return {
            'success': False,
            'message': f'技能 {skill_name} 不存在'
        }
    
    compatibility = adapter.check_skill_compatibility(
        skill_name,
        agent_profile.capabilities,
        model_profile.capabilities,
        model_profile.context_length
    )
    
    skill_info = adapter.get_skill_info(skill_name)
    
    return {
        'success': True,
        'skill': skill_info,
        'agent': {
            'name': agent_profile.name,
            'capabilities': [c.value for c in agent_profile.capabilities]
        },
        'model': {
            'name': model_profile.name,
            'capabilities': [c.value for c in model_profile.capabilities]
        },
        'compatibility': compatibility
    }


def compile_skill_demo(skill_name, agent_key, model_key):
    """演示技能编译"""
    adapter = create_demo_skill_adapter()
    router = SkillRouter(adapter)
    compiler = SkillCompiler(adapter, router)
    registry = AgentCapabilityRegistry()
    
    agent_profile = registry.get_agent(agent_key)
    model_profile = registry.get_model(model_key)
    
    if not agent_profile or not model_profile:
        return {
            'success': False,
            'message': 'Agent或模型不存在'
        }
    
    compile_result = compiler.compile_skill(
        skill_name,
        agent_profile.capabilities,
        model_profile.capabilities,
        model_profile.context_length
    )
    
    report = compiler.get_compilation_report(compile_result)
    
    return {
        'success': compile_result['success'],
        'compile_result': compile_result,
        'report': report
    }


def compare_agents_demo(agent_keys):
    """比较Agent能力"""
    registry = AgentCapabilityRegistry()
    comparison = registry.get_agent_comparison(agent_keys)
    return {
        'success': True,
        'comparison': comparison
    }


def compare_models_demo(model_keys):
    """比较模型能力"""
    registry = AgentCapabilityRegistry()
    comparison = registry.get_model_comparison(model_keys)
    return {
        'success': True,
        'comparison': comparison
    }


def run_intent_optimization(opt_type="full_report"):
    """执行意图识别达尔文优化技能"""
    try:
        import io
        from contextlib import redirect_stdout

        skill = IntentOptimizationSkill()
        with redirect_stdout(io.StringIO()):
            result = skill.execute(opt_type)
        return {
            'success': True,
            'optimization_type': opt_type,
            'result': result
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'优化技能执行失败: {str(e)}'
        }


def create_demo_skill_adapter():
    """创建演示用的技能适配器（包含示例技能）"""
    adapter = SkillAdapter()
    
    # 注册示例技能
    adapter.register_skill(
        name='query_article',
        func=lambda **kwargs: f"查询文章: {kwargs.get('keyword', '')}",
        description='根据关键词查询博客文章',
        category='blog',
        required_agent_capabilities={AgentCapability.TOOL_USE},
        required_model_capabilities={ModelCapability.FUNCTION_CALLING},
        min_context_length=2048,
        tags=['文章', '搜索', '查询']
    )
    
    adapter.register_skill(
        name='get_latest_articles',
        func=lambda **kwargs: "获取最新文章",
        description='获取最新发布的文章列表',
        category='blog',
        required_agent_capabilities={AgentCapability.TOOL_USE},
        min_context_length=1024,
        tags=['文章', '最新']
    )
    
    adapter.register_skill(
        name='advanced_search',
        func=lambda **kwargs: f"高级搜索: {kwargs.get('query', '')}",
        description='使用复杂条件搜索文章（需要推理能力）',
        category='blog',
        required_agent_capabilities={AgentCapability.TOOL_USE, AgentCapability.MEMORY},
        required_model_capabilities={ModelCapability.REASONING, ModelCapability.FUNCTION_CALLING},
        min_context_length=8192,
        alternatives=['query_article'],
        tags=['搜索', '高级', '推理']
    )
    
    adapter.register_skill(
        name='long_task_analysis',
        func=lambda **kwargs: "长时任务分析",
        description='执行长时间的文章分析任务',
        category='analysis',
        required_agent_capabilities={
            AgentCapability.LONG_TASK,
            AgentCapability.MEMORY,
            AgentCapability.CODE_EXEC
        },
        required_model_capabilities={ModelCapability.REASONING, ModelCapability.CODE_GENERATION},
        min_context_length=16384,
        max_execution_time=300,
        alternatives=['advanced_search'],
        tags=['分析', '长时任务', '代码']
    )
    
    # 注册达尔文优化技能 —— 对 NLP 意图识别算法进行对比测评与参数优化
    adapter.register_skill(
        name='intent_optimization',
        func=lambda **kwargs: "意图识别达尔文优化技能",
        description='NLP意图识别达尔文优化技能 - 三代算法对比测评 + 阈值参数优化',
        category='optimization',
        required_agent_capabilities={AgentCapability.TOOL_USE, AgentCapability.CODE_EXEC},
        required_model_capabilities={ModelCapability.REASONING},
        min_context_length=4096,
        tags=['NLP', '意图识别', '优化', '达尔文', '测评']
    )

    adapter.register_skill(
        name='web_research',
        func=lambda **kwargs: f"网络研究: {kwargs.get('topic', '')}",
        description='通过网络搜索进行主题研究',
        category='research',
        required_agent_capabilities={
            AgentCapability.WEB_SEARCH,
            AgentCapability.MEMORY,
            AgentCapability.MULTI_TURN
        },
        required_model_capabilities={
            ModelCapability.REASONING,
            ModelCapability.MULTI_LANGUAGE,
            ModelCapability.FUNCTION_CALLING
        },
        min_context_length=8192,
        alternatives=['long_task_analysis'],
        tags=['研究', '网络', '多语言']
    )
    
    return adapter
