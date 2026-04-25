from django.urls import path
from .views import (
    DocumentUploadView,
    DocumentListView,
    DocumentDetailView,
    DocumentExtractedTextView,
    DocumentChunksView
)

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('', DocumentListView.as_view(), name='document-list'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<int:pk>/text/', DocumentExtractedTextView.as_view(), name='document-text'),
    path('<int:pk>/chunks/', DocumentChunksView.as_view(), name='document-chunks'),
]