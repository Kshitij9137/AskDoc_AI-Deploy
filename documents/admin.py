from django.contrib import admin
from .models import Document, ExtractedText, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'file_size', 'upload_date', 'is_processed')
    list_filter = ('is_processed', 'upload_date')
    search_fields = ('title', 'owner__username')


@admin.register(ExtractedText)
class ExtractedTextAdmin(admin.ModelAdmin):
    list_display = ('document', 'page_number')
    search_fields = ('document__title',)


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'page_number')
    search_fields = ('document__title',)


from .models import ChunkEmbedding

@admin.register(ChunkEmbedding)
class ChunkEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('chunk', )