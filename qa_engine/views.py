from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .pipeline import answer_question
from .models import QueryLog
from .serializers import QueryLogSerializer


class AskQuestionView(APIView):
    """POST /api/qa/ask/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()

        # Input validation
        if not question:
            return Response(
                {'error': 'Please provide a question.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(question) < 5:
            return Response(
                {'error': 'Question is too short. Minimum 5 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(question) > 500:
            return Response(
                {'error': 'Question is too long. Maximum 500 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = answer_question(
                question=question,
                user=request.user
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to process question: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'question': result['question'],
                'answer': result['answer'],
                'sources': result['sources'],
            },
            status=status.HTTP_200_OK
        )


class ChatHistoryView(APIView):
    """GET /api/qa/history/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get page size from query params (default 10)
        try:
            limit = int(request.query_params.get('limit', 10))
            limit = min(limit, 50)  # max 50 at a time
        except ValueError:
            limit = 10

        logs = QueryLog.objects.filter(
            user=request.user
        ).prefetch_related('query_sources__document')[:limit]

        serializer = QueryLogSerializer(logs, many=True)
        return Response({
            'count': logs.count(),
            'results': serializer.data
        })


class ClearHistoryView(APIView):
    """DELETE /api/qa/history/clear/"""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = QueryLog.objects.filter(
            user=request.user
        ).delete()

        return Response(
            {'message': f'Deleted {deleted_count} queries from history.'},
            status=status.HTTP_200_OK
        )
