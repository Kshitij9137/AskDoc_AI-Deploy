from django.db import models
from users.models import CustomUser


class Document(models.Model):
    """Stores uploaded document info and metadata"""
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    upload_date = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} (uploaded by {self.owner.username})"


class ExtractedText(models.Model):
    """Stores raw text extracted from each page of a document"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='extracted_texts'
    )
    page_number = models.PositiveIntegerField()
    raw_text = models.TextField()

    class Meta:
        ordering = ['page_number']

    def __str__(self):
        return f"Page {self.page_number} of {self.document.title}"


class DocumentChunk(models.Model):
    """Stores cleaned text chunks ready for AI embedding"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    page_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
    

class ChunkEmbedding(models.Model):
    """Stores the vector embedding for each document chunk"""
    chunk = models.OneToOneField(
        DocumentChunk,
        on_delete=models.CASCADE,
        related_name='embedding'
    )
    embedding_vector = models.TextField()  # stored as JSON string

    def __str__(self):
        return f"Embedding for chunk {self.chunk.chunk_index} of {self.chunk.document.title}"