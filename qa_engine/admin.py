from django.contrib import admin
from .models import QueryLog, QuerySource


class QuerySourceInline(admin.TabularInline):
    model = QuerySource
    extra = 0
    readonly_fields = ('document', 'page_number', 'relevant_text')


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'created_at')
    search_fields = ('question', 'user__username')
    readonly_fields = ('question', 'answer', 'user', 'created_at')
    inlines = [QuerySourceInline]


@admin.register(QuerySource)
class QuerySourceAdmin(admin.ModelAdmin):
    list_display = ('query', 'document', 'page_number')
    search_fields = ('document__title',)