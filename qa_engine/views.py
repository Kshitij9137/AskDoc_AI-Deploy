from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .pipeline import answer_question
from .models import QueryLog
from .serializers import QueryLogSerializer


class AskQuestionView(APIView):
    """
    POST /api/qa/ask/
    Accept a question and return an AI-generated answer
    with source references.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        question = request.data.get('question', '').strip()

        # Validate input
        if not question:
            return Response(
                {'error': 'Please provide a question.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(question) < 5:
            return Response(
                {'error': 'Question is too short.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(question) > 500:
            return Response(
                {'error': 'Question is too long. Max 500 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Run Q&A pipeline
        result = answer_question(
            question=question,
            user=request.user
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
    """
    GET /api/qa/history/
    Return all previous questions and answers
    for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        logs = QueryLog.objects.filter(
            user=request.user
        ).prefetch_related('query_sources__document')[:20]

        serializer = QueryLogSerializer(logs, many=True)
        return Response(serializer.data)


class ClearHistoryView(APIView):
    """
    DELETE /api/qa/history/clear/
    Clear all chat history for the logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = QueryLog.objects.filter(
            user=request.user
        ).delete()

        return Response(
            {'message': f'Deleted {deleted_count} queries from history.'},
            status=status.HTTP_200_OK
        )