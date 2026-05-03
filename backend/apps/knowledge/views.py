import json

from django.http import StreamingHttpResponse
from rest_framework import viewsets, decorators, response, status, parsers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import HasSkill, IsAdmin
from .models import KnowledgeDocument, QASession
from .serializers import (KnowledgeDocumentSerializer, QASessionSerializer,
                          QuestionSerializer, IngestTextSerializer, IngestFileSerializer)
from . import services


class KnowledgeQAView(APIView):
    """问答接口 - 所有具备 knowledge_qa skill 的角色可用。"""
    permission_classes = [IsAuthenticated, HasSkill]
    required_skill = 'knowledge_qa'

    def post(self, request):
        ser = QuestionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = services.answer_question(
            ser.validated_data['question'], top_k=ser.validated_data['top_k'])
        session = QASession.objects.create(
            user=request.user,
            question=ser.validated_data['question'],
            answer=result['answer'],
            sources=result['sources'],
        )
        return response.Response({
            'id': session.id,
            'question': session.question,
            'answer': session.answer,
            'sources': session.sources,
            'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })


class KnowledgeQAStreamView(APIView):
    """流式问答接口 - SSE 逐 token 推送。"""
    permission_classes = [IsAuthenticated, HasSkill]
    required_skill = 'knowledge_qa'

    def post(self, request):
        ser = QuestionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        question = ser.validated_data['question']
        top_k = ser.validated_data['top_k']

        def event_stream():
            for line in services.answer_question_stream(question, top_k=top_k):
                yield f'data: {line}\n\n'

        return StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
        )


class QASessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QASessionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ('user',)
    search_fields = ('question', 'answer')

    def get_queryset(self):
        qs = QASession.objects.all().order_by('-created_at')
        # 普通角色只看自己的;管理员可看全部
        if self.request.user.role != 'admin':
            qs = qs.filter(user=self.request.user)
        return qs


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """知识库文档管理 - 仅管理员可改/删,所有人可看。"""
    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdmin()]

    @decorators.action(detail=False, methods=['post'])
    def ingest_text(self, request):
        ser = IngestTextSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        doc = services.ingest_text(
            source=ser.validated_data['source'],
            title=ser.validated_data['title'],
            text=ser.validated_data['text'],
            description=ser.validated_data['description'],
            uploader=request.user,
        )
        return response.Response(KnowledgeDocumentSerializer(doc).data,
                                 status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'])
    def ingest_file(self, request):
        ser = IngestFileSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        doc = services.ingest_file(
            ser.validated_data['file'],
            title=ser.validated_data['title'],
            description=ser.validated_data['description'],
            uploader=request.user,
        )
        return response.Response(KnowledgeDocumentSerializer(doc).data,
                                 status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=['post'])
    def reload_corpus(self, request):
        n = services.ingest_default_corpus()
        return response.Response({'detail': f'已重置内置语料,共 {n} 条'})

    def perform_destroy(self, instance):
        services.delete_document(instance)
