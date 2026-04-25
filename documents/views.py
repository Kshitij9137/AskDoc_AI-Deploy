from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document, ExtractedText, DocumentChunk
from .serializers import DocumentUploadSerializer, DocumentListSerializer
from .processor import process_document



class DocumentUploadView(APIView):
    """Upload a new document and automatically extract text"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')

        # Validate file exists
        if not file:
            return Response(
                {'error': 'No file provided. Please attach a PDF file.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        if not file.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'Invalid file type. Only PDF files are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            return Response(
                {'error': 'File too large. Maximum size is 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        title = request.data.get('title', file.name).strip()
        if not title:
            title = file.name

        try:
            document = Document.objects.create(
                owner=request.user,
                title=title,
                file=file,
                file_size=file.size,
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to save document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Process the document
        try:
            success = process_document(document.id)
            document.refresh_from_db()
        except Exception as e:
            document.delete()
            return Response(
                {'error': f'Failed to process document: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = DocumentUploadSerializer(document)
        return Response(
            {
                'message': 'Document uploaded and processed successfully.'
                           if success else
                           'Document uploaded but text extraction failed.',
                'document': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class DocumentListView(generics.ListAPIView):
    """List all documents belonging to logged-in user"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(
            owner=self.request.user
        ).order_by('-upload_date')


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """Get or delete a single document"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()

        # Delete the actual PDF file from disk
        import os
        if document.file and os.path.exists(document.file.path):
            os.remove(document.file.path)

        # Rebuild FAISS index after deletion
        document.delete()

        from documents.faiss_store import build_faiss_index
        from documents.models import ChunkEmbedding
        if ChunkEmbedding.objects.exists():
            build_faiss_index()

        return Response(
            {'message': 'Document deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class DocumentExtractedTextView(APIView):
    """View extracted text of a document"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            document = Document.objects.get(
                id=pk,
                owner=request.user
            )
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        pages = ExtractedText.objects.filter(document=document)

        if not pages.exists():
            return Response(
                {'error': 'No extracted text found for this document.'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = [
            {
                'page_number': page.page_number,
                'text': page.raw_text[:300] + '...'
            }
            for page in pages
        ]

        return Response({
            'document': document.title,
            'total_pages': pages.count(),
            'pages': data
        })


class DocumentChunksView(APIView):
    """Preview chunks created from a document"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            document = Document.objects.get(
                id=pk,
                owner=request.user
            )
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        chunks = DocumentChunk.objects.filter(document=document)

        if not chunks.exists():
            return Response(
                {'error': 'No chunks found. Document may not be processed yet.'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = [
            {
                'chunk_index': chunk.chunk_index,
                'page_number': chunk.page_number,
                'word_count': len(chunk.text.split()),
                'preview': chunk.text[:200] + '...'
            }
            for chunk in chunks
        ]

        return Response({
            'document': document.title,
            'total_chunks': chunks.count(),
            'chunks': data
        })