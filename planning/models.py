from datetime import timedelta
from django.db import models
from content.models import BaseProcessModel
from django.db.models import Sum

from documents.models import FileReference


class Plan(BaseProcessModel):
    plan_goal = models.TextField()
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    explanation = models.TextField(blank=True, null=True)

    @property
    def total_sessions(self):
        return self.session_set.count()

    @property
    def sum_session_duration(self):
        total_time = self.session_set.aggregate(Sum("duration"))["duration__sum"]
        return total_time if total_time else timedelta(0)

    @property
    def all_done(self):
        return all([session.marked_done for session in self.session_set.all()])

    @property
    def progress(self):
        total_sessions = self.total_sessions
        if total_sessions == 0:
            return 0
        done_sessions = self.session_set.filter(marked_done=True).count()
        return done_sessions / total_sessions * 100

    def __str__(self):
        return self.plan_goal


class Session(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    file_references = models.ManyToManyField(FileReference, blank=True)
    session_goal = models.TextField()
    date = models.DateField()
    duration = models.DurationField()
    marked_done = models.BooleanField(default=False)

    def __str__(self):
        return self.session_goal

    def get_full_text(self, in_html=False):
        text = "\n---\n".join(
            ref.get_reference_text(in_html) for ref in self.file_references.all()
        )
        return text

    def get_page_count(self):
        return sum(
            ref.end_page_index - ref.start_page_index + 1
            for ref in self.file_references.all()
        )
