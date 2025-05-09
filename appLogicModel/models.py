from django.db import models
from django.utils import timezone


class Session(models.Model):
    user_name = models.CharField(max_length=100)
    run_number = models.CharField(max_length=20)
    final_evaluation = models.BooleanField(null=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    user_answer = models.TextField(blank=True)
    correct_answer = models.TextField(blank=True)
    time_spent = models.CharField(max_length=50, blank=True)
    levels_data = models.JSONField(null=True, blank=True)  # Добавьте это поле

    def __str__(self):
        return f"{self.user_name} - Прогон {self.run_number}"
