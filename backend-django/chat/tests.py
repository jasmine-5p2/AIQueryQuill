from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
class ApiTests(APITestCase):
    def test_health_is_public(self): self.assertEqual(self.client.get("/api/health/").status_code, 200)
    def test_registration_and_private_chats(self):
        response = self.client.post("/api/auth/register/", {"username": "student", "password": "portfolio-pass-123"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + response.data["token"])
        self.client.post("/api/chats/", {"title": "My private chat"}, format="json")
        chat_id = self.client.get("/api/chats/").data[0]["id"]
        self.assertEqual(len(self.client.get("/api/chats/").data), 1)
        other = get_user_model().objects.create_user("other", password="another-pass-123")
        self.assertEqual(other.chat_sessions.count(), 0)
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.client.force_authenticate(user=other)
        self.assertEqual(self.client.get(f"/api/chats/{chat_id}/messages/").status_code, 404)
