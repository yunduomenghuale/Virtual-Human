from rest_framework import serializers
from .models import KnowledgeDocument, QASession


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    uploader_name = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeDocument
        fields = ('id', 'title', 'source', 'description', 'chunk_count',
                  'file', 'uploader_name', 'created_at')
        read_only_fields = fields

    def get_uploader_name(self, obj):
        return obj.uploader.username if obj.uploader_id else ''


class QASessionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = QASession
        fields = ('id', 'user', 'user_name', 'question', 'answer',
                  'sources', 'created_at')
        read_only_fields = fields


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    top_k = serializers.IntegerField(required=False, default=4, min_value=1, max_value=10)


class IngestTextSerializer(serializers.Serializer):
    title = serializers.CharField()
    source = serializers.CharField()
    text = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default='')


class IngestFileSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default='')
    file = serializers.FileField()
