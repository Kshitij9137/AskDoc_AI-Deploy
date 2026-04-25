
from django.db import models
from users.models import CustomUser
from documents.models import Document


class QueryLog(models.Model):
    """
    Stores every question asked and the answer generated.
    Used for chat history and analytics.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='queries'
    )
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Q: {self.question[:50]} (by {self.user.username})"


class QuerySource(models.Model):
    """
    Stores the source references for each answer.
    Each QueryLog can have multiple sources.
    """
    query = models.ForeignKey(
        QueryLog,
        on_delete=models.CASCADE,
        related_name='query_sources'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='query_sources'
    )
    page_number = models.PositiveIntegerField()
    relevant_text = models.TextField()  # the chunk text used

    def __str__(self):
        return f"Source: {self.document.title} (Page {self.page_number})"