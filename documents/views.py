from django.shortcuts import render

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Document
from .serializers import DocumentUploadSerializer, DocumentListSerializer


class DocumentUploadView(APIView):
    """Upload a new document"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only allow PDF files
        if not file.name.endswith('.pdf'):
            return Response(
                {'error': 'Only PDF files are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get title from request or use filename
        title = request.data.get('title', file.name)

        document = Document.objects.create(
            owner=request.user,
            title=title,
            file=file,
            file_size=file.size,
        )

        serializer = DocumentUploadSerializer(document)
        return Response(
            {
                'message': 'Document uploaded successfully.',
                'document': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class DocumentListView(generics.ListAPIView):
    """List all documents belonging to the logged-in user"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            owner=self.request.user
        ).order_by('-upload_date')


class DocumentDetailView(generics.RetrieveAPIView):
    """Get details of a single document"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)