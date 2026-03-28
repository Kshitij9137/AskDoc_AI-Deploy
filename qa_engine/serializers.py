from rest_framework import serializers
from .models import QueryLog, QuerySource


class QuerySourceSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(
        source='document.title',
        read_only=True
    )

    class Meta:
        model = QuerySource
        fields = ('document_title', 'page_number', 'relevant_text')


class QueryLogSerializer(serializers.ModelSerializer):
    sources = QuerySourceSerializer(
        source='query_sources',
        many=True,
        read_only=True
    )

    class Meta:
        model = QueryLog
        fields = ('id', 'question', 'answer', 'created_at', 'sources')