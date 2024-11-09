from django.contrib import admin

from .models import Session, Plan


class SessionAdmin(admin.ModelAdmin):
    list_display = ("plan", "session_goal", "date", "duration", "marked_done")
    search_fields = ("plan", "session_goal")
    list_filter = ("marked_done",)


admin.site.register(Session, SessionAdmin)


class PlanAdmin(admin.ModelAdmin):
    list_display = ("plan_goal", "description", "start_date", "end_date", "explanation")
    search_fields = ("plan_goal", "description")
    list_filter = ("start_date", "end_date")


admin.site.register(Plan, PlanAdmin)
