from django.contrib import admin
from .models import Quiz, Question, Option, Score, Summary


class QuizAdmin(admin.ModelAdmin):
    list_display = ("topic", "difficulty", "number_of_questions")
    search_fields = ("topic",)
    list_filter = ("difficulty", "number_of_questions")


admin.site.register(Quiz, QuizAdmin)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "quiz")
    search_fields = ("question",)
    list_filter = ("quiz",)


admin.site.register(Question, QuestionAdmin)


class OptionAdmin(admin.ModelAdmin):
    list_display = ("option", "question", "is_correct")
    search_fields = ("option",)
    list_filter = ("question", "is_correct")


admin.site.register(Option, OptionAdmin)


class ScoreAdmin(admin.ModelAdmin):
    list_display = ("score", "quiz", "created_at")
    search_fields = ("score",)
    list_filter = ("quiz", "created_at")


admin.site.register(Score, ScoreAdmin)


class SummaryAdmin(admin.ModelAdmin):
    list_display = ("topic", "processing_status")
    search_fields = ("topic",)
    list_filter = ("processing_status",)


admin.site.register(Summary, SummaryAdmin)
