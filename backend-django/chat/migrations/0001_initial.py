from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="ChatSession", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(default="New conversation", max_length=120)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)), ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_sessions", to=settings.AUTH_USER_MODEL))], options={"ordering": ["-updated_at"]}),
        migrations.CreateModel(name="ChatMessage", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("role", models.CharField(choices=[("user", "User"), ("assistant", "Assistant")], max_length=12)), ("content", models.TextField()), ("created_at", models.DateTimeField(auto_now_add=True)), ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chat.chatsession"))], options={"ordering": ["created_at", "id"]}),
    ]
