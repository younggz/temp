import json

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings

from blog.models import ChatLog, Post
from nlp.relevance import rebuild_index


@override_settings(ALLOWED_HOSTS=["testserver", "127.0.0.1", "172.20.10.2"])
class FrontendPageTests(TestCase):
    def setUp(self):
        Post.objects.create(
            title="Python入门教程",
            tags="Python,入门,编程",
            category="编程语言",
            content="Python是一种简单易学的编程语言，适合初学者入门。",
        )
        rebuild_index()

    def test_homepage_renders_project_dashboard(self):
        user = User.objects.create_user(username="home_user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.get("/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "项目成果看板")
        self.assertContains(response, "V4")
        self.assertContains(response, "TF-IDF")

    def test_homepage_redirects_anonymous_user_to_login(self):
        response = Client().get("/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_demo_login_account_is_ready(self):
        response = self.client.post(
            "/accounts/login/",
            {"demo_login": "1", "next": "/"},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")
        self.assertTrue(User.objects.filter(username="demo").exists())

    def test_skill_demo_page_renders_darwin_dashboard(self):
        user = User.objects.create_user(username="skill_user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.get("/skill_demo/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "NLP 意图识别达尔文优化演示")
        self.assertContains(response, "生产默认算法")
        self.assertContains(response, "V4 Ensemble")

    def test_share_page_and_qr_endpoint_are_available(self):
        user = User.objects.create_user(username="share_user", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.get("/share/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "智能助手")
        self.assertContains(response, "扫码使用智能助手")
        self.assertContains(response, ":8000/share/")

        qr_response = self.client.get(
            "/share/qr.png?url=http://127.0.0.1:8000/",
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(qr_response.status_code, 200)
        self.assertIn(qr_response["Content-Type"], {"image/png", "text/plain; charset=utf-8"})

    def test_share_page_on_lan_device_only_shows_assistant(self):
        self.client.force_login(User.objects.create_user(username="lan_user", password="StrongPass123"))
        response = self.client.get("/share/", HTTP_HOST="172.20.10.2:8000")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "智能助手")
        self.assertNotContains(response, "扫码使用智能助手")
        self.assertNotContains(response, "扫码打开智能助手")

    def test_lan_share_redirects_anonymous_user_to_login(self):
        response = self.client.get("/share/", HTTP_HOST="172.20.10.2:8000")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_desktop_login_redirects_to_home_by_default(self):
        User.objects.create_user(username="desktop_user", password="StrongPass123")
        response = self.client.post(
            "/accounts/login/",
            {"username": "desktop_user", "password": "StrongPass123"},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_chat_api_returns_intent_and_article_confidence_payload(self):
        response = self.client.post(
            "/nlp/chat/",
            {"message": "帮我找Python文章"},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "查询文章")
        self.assertEqual(data["intent_algorithm"], "ensemble")
        self.assertIn("qa_result", data)
        self.assertGreater(data["qa_result"]["overall_confidence"], 0)

    def test_chat_api_accepts_external_post_without_csrf_cookie(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/nlp/chat/",
            {"message": "Python"},
            HTTP_HOST="172.20.10.2:8000",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_logged_in_chat_is_recorded_by_user(self):
        user = User.objects.create_user(username="alice", password="StrongPass123")
        self.client.force_login(user)
        response = self.client.post(
            "/nlp/chat/",
            {"message": "Python"},
            HTTP_HOST="172.20.10.2:8000",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(ChatLog.objects.filter(user=user).count(), 1)
        self.assertEqual(ChatLog.objects.get(user=user).id, data["chat_log_id"])

    def test_profile_requires_login_and_shows_user_stats(self):
        anonymous_response = self.client.get("/profile/", HTTP_HOST="127.0.0.1")
        self.assertEqual(anonymous_response.status_code, 302)

        user = User.objects.create_user(username="profile_user", password="StrongPass123")
        ChatLog.objects.create(
            user=user,
            user_input="Python",
            predicted_intent="查询文章",
            confidence=0.86,
            algorithm="ensemble",
            response_text="result",
            is_helpful=True,
        )
        self.client.force_login(user)
        response = self.client.get("/profile/", HTTP_HOST="127.0.0.1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "我的智能画像")
        self.assertContains(response, "查询文章")
        self.assertContains(response, "86%")

    def test_chat_api_answers_algorithm_question_without_article_recommendation(self):
        response = self.client.post(
            "/nlp/chat/",
            {"message": "有其他算法吗"},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "算法咨询")
        self.assertNotIn("qa_result", data)
        self.assertIn("V4", data["message"])

    def test_chat_api_can_create_public_article_in_steps(self):
        user = User.objects.create_user(username="writer", password="StrongPass123")
        self.client.force_login(user)

        first = self.client.post("/nlp/chat/", {"message": "创建文章"}, HTTP_HOST="127.0.0.1")
        self.assertEqual(first.status_code, 200)
        self.assertIn("标题", first.json()["message"])

        second = self.client.post("/nlp/chat/", {"message": "课堂演示文章"}, HTTP_HOST="127.0.0.1")
        self.assertEqual(second.status_code, 200)
        self.assertIn("内容", second.json()["message"])

        third = self.client.post(
            "/nlp/chat/",
            {"message": "这是一篇通过智能助手发布的公开文章，所有账号都应该能看到。"},
            HTTP_HOST="127.0.0.1",
        )
        self.assertEqual(third.status_code, 200)
        self.assertIn("发送", third.json()["message"])

        final = self.client.post("/nlp/chat/", {"message": "发送"}, HTTP_HOST="127.0.0.1")
        self.assertEqual(final.status_code, 200)
        data = final.json()
        self.assertIn("发布成功", data["message"])
        self.assertTrue(Post.objects.filter(title="课堂演示文章").exists())
        self.assertGreaterEqual(ChatLog.objects.filter(user=user, predicted_intent="创建文章").count(), 4)

    def test_chat_api_lists_available_skills(self):
        response = self.client.post(
            "/nlp/chat/",
            {"message": "全部技能"},
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "技能列表")
        self.assertIn("创建公开文章", data["message"])

    @override_settings(
        SITE_URL="https://blog-nlp-agent.onrender.com",
        ALLOWED_HOSTS=["testserver", "127.0.0.1", "172.20.10.2", "blog-nlp-agent.onrender.com"],
    )
    def test_share_qr_uses_deployed_site_url(self):
        user = User.objects.create_user(username="qr_user", password="StrongPass123")
        self.client.force_login(user)

        response = self.client.get("/share/?qr=1", HTTP_HOST="blog-nlp-agent.onrender.com")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://blog-nlp-agent.onrender.com/share/")

    def test_skill_demo_optimization_api_returns_recommendation(self):
        response = self.client.post(
            "/skill_demo_api/",
            data=json.dumps({
                "action": "run_optimization",
                "optimization_type": "full_report",
            }),
            content_type="application/json",
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("V4.0", data["result"]["recommendation"])

# Create your tests here.
