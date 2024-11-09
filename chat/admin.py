from django.contrib import admin
from .models import Chat, Message


class ChatAdmin(admin.ModelAdmin):
    list_display = ("topic", "created_at")
    search_fields = ("topic",)
    list_filter = ("created_at",)


admin.site.register(Chat, ChatAdmin)


class MessageAdmin(admin.ModelAdmin):
    list_display = ("chat", "sender", "created_at")
    search_fields = ("chat", "sender")
    list_filter = ("created_at",)


admin.site.register(Message, MessageAdmin)
