from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Document, ExtractedText, DocumentChunk
from .serializers import DocumentUploadSerializer, DocumentListSerializer
from .processor import process_document


class DocumentUploadView(APIView):
    """Upload a new document and automatically extract text"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response(
                {'error': 'No file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith('.pdf'):
            return Response(
                {'error': 'Only PDF files are allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        title = request.data.get('title', file.name)

        document = Document.objects.create(
            owner=request.user,
            title=title,
            file=file,
            file_size=file.size,
        )

        # Automatically extract text and chunk after upload
        success = process_document(document.id)
        print(f"Processing result: {success}")  # add this line


        # ✅ This is the fix — refresh object from DB
        # so is_processed shows the updated value
        document.refresh_from_db()

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


class DocumentDetailView(generics.RetrieveAPIView):
    """Get details of a single document"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)


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

class DocumentChunksView(APIView):
    """Preview chunks created from a document (for debugging)"""
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

        from .models import DocumentChunk
        chunks = DocumentChunk.objects.filter(document=document)

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