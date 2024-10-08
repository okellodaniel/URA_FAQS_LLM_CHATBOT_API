from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    question = models.TextField()
    answer = models.TextField()
    section = models.CharField(max_length=255)
    model_used = models.CharField(max_length=255)
    response_time = models.FloatField()
    relevance = models.CharField(max_length=50)
    relevance_explanation = models.TextField()
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    total_tokens = models.IntegerField()
    eval_prompt_tokens = models.IntegerField()
    eval_completion_tokens = models.IntegerField()
    eval_total_tokens = models.IntegerField()
    openai_cost = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.id


class Feedback(models.Model):
    conversation =  models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='feedback')
    feedback = models.IntegerField()  # Positive (1) or Negative (-1)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback for {self.conversation.id} - {self.feedback}"
