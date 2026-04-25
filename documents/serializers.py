from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Used when uploading a document"""
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', 'file_size', 'upload_date', 'is_processed')
        read_only_fields = ('id', 'file_size', 'upload_date', 'is_processed')


class DocumentListSerializer(serializers.ModelSerializer):
    """Used when listing documents"""
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Document
        fields = ('id', 'title', 'file_size', 'upload_date', 'is_processed', 'owner_name')