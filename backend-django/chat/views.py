import json
import logging
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.http import StreamingHttpResponse
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import ChatMessage, ChatSession
logger = logging.getLogger(__name__)
def event(payload): return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request): return Response({"status": "ok"})
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username, password = str(request.data.get("username", "")).strip(), str(request.data.get("password", ""))
    if len(username) < 3 or len(password) < 8: return Response({"error": "Username must have 3 characters and password 8 characters."}, status=400)
    User = get_user_model()
    if User.objects.filter(username=username).exists(): return Response({"error": "That username is already taken."}, status=400)
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username}, status=201)
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    user = authenticate(username=request.data.get("username", ""), password=request.data.get("password", ""))
    if not user: return Response({"error": "Username or password is incorrect."}, status=400)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})
@api_view(["GET", "POST"])
def chats(request):
    if request.method == "GET":
        return Response([{"id": c.id, "title": c.title, "updated_at": c.updated_at} for c in ChatSession.objects.filter(owner=request.user)])
    chat = ChatSession.objects.create(owner=request.user, title=str(request.data.get("title", "New conversation"))[:120])
    return Response({"id": chat.id, "title": chat.title}, status=201)
@api_view(["GET"])
def chat_messages(request, chat_id):
    chat = ChatSession.objects.filter(owner=request.user, id=chat_id).first()
    if not chat: return Response({"error": "Conversation not found."}, status=404)
    return Response([{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in chat.messages.all()])
@api_view(["DELETE"])
def delete_chat(request, chat_id):
    deleted, _ = ChatSession.objects.filter(owner=request.user, id=chat_id).delete()
    return Response(status=204) if deleted else Response({"error": "Conversation not found."}, status=404)
@api_view(["POST"])
def chat_stream(request):
    prompt = str(request.data.get("message", "")).strip()
    if not prompt or len(prompt) > 12000: return Response({"error": "Message must contain 1–12,000 characters."}, status=400)
    chat_id = request.data.get("chat_id")
    chat = ChatSession.objects.filter(owner=request.user, id=chat_id).first() if chat_id else ChatSession.objects.create(owner=request.user, title=prompt[:48])
    if not chat: return Response({"error": "Conversation not found."}, status=404)
    model = str(request.data.get("model", settings.GEMINI_MODEL))[:80]
    try: temperature = max(0.0, min(float(request.data.get("temperature", 0.7)), 1.0))
    except (TypeError, ValueError): return Response({"error": "Temperature must be a number between 0 and 1."}, status=400)
    history = list(chat.messages.all())[-20:]
    ChatMessage.objects.create(session=chat, role=ChatMessage.Role.USER, content=prompt)
    if len(history) == 0:
        chat.title = prompt[:48]; chat.save(update_fields=["title", "updated_at"])
    def generate():
        parts = []
        contents = [{"role": "model" if msg.role == "assistant" else "user", "parts": [{"text": msg.content}]} for msg in history]
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                stream = client.models.generate_content_stream(model=model, contents=contents, config=types.GenerateContentConfig(temperature=temperature))
                for chunk in stream:
                    if chunk.text:
                        parts.append(chunk.text); yield event({"text": chunk.text})
            except Exception:
                logger.exception("Gemini request failed for chat %s; trying Groq fallback", chat.id)

        if not parts and settings.GROQ_API_KEY:
            try:
                from urllib.request import Request, urlopen
                messages = [{"role": "assistant" if msg.role == "assistant" else "user", "content": msg.content} for msg in history]
                messages.append({"role": "user", "content": prompt})
                request = Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps({"model": settings.GROQ_MODEL, "messages": messages, "temperature": temperature, "stream": True}).encode(),
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json",
                        "User-Agent": "QueryQuill/1.0",
                    },
                    method="POST",
                )
                with urlopen(request, timeout=60) as response:
                    for raw_line in response:
                        line = raw_line.decode("utf-8").strip()
                        if not line.startswith("data: ") or line == "data: [DONE]":
                            continue
                        text = json.loads(line[6:]).get("choices", [{}])[0].get("delta", {}).get("content")
                        if text:
                            parts.append(text); yield event({"text": text})
            except Exception:
                logger.exception("Groq fallback failed for chat %s", chat.id)

        if not parts:
            message = "No AI provider is available. Configure GEMINI_API_KEY or GROQ_API_KEY and try again."
            yield event({"error": message})
            return
        answer = "".join(parts)
        ChatMessage.objects.create(session=chat, role=ChatMessage.Role.ASSISTANT, content=answer)
        yield event({"done": True, "chat_id": chat.id})
    response = StreamingHttpResponse(generate(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"; response["X-Accel-Buffering"] = "no"
    return response
