from django.urls import path
from .views import ChatView, ClearChatHistoryView, RecentConversationsView, FeedbackView, FeedbackStatsView,ConversationDetailView


urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('conversations', RecentConversationsView.as_view(), name='get_conversations'),
    path('conversations/<str:id>', ConversationDetailView.as_view(), name='conversation_detail'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),
    path('feedback/stats/', FeedbackStatsView.as_view(), name='feedback_stats'),
    path('clear', ClearChatHistoryView.as_view(), name='clear_chat_history'),
]