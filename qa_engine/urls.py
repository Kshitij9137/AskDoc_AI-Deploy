from django.urls import path
from .views import AskQuestionView, ChatHistoryView, ClearHistoryView

urlpatterns = [
    path('ask/', AskQuestionView.as_view(), name='ask-question'),
    path('history/', ChatHistoryView.as_view(), name='chat-history'),
    path('history/clear/', ClearHistoryView.as_view(), name='clear-history'),
]