from rest_framework import serializers
from .models import Conversation,Feedback

class ChatbotSerializer(serializers.Serializer):
    message = serializers.CharField(required=True)
    model_choice = serializers.CharField(default="openai/gpt-3.5-turbo")
    search_type = serializers.CharField(default="Text")

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['feedback', 'timestamp']

class FeedbackSubmissionSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=True)
    feedback = serializers.IntegerField(required=True, min_value=-1, max_value=1)

class ConversationSerializer(serializers.ModelSerializer):
    feedback = FeedbackSerializer(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = [
            'id', 'question', 'answer', 'section', 'model_used', 'response_time',
            'relevance', 'relevance_explanation', 'prompt_tokens', 'completion_tokens',
            'total_tokens', 'eval_prompt_tokens', 'eval_completion_tokens', 'eval_total_tokens',
            'openai_cost', 'timestamp','feedback'
        ]

class FeedbackStatsSerializer(serializers.Serializer):
    thumbs_up = serializers.IntegerField()
    thumbs_down = serializers.IntegerField()