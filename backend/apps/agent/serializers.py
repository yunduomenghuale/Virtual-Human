from rest_framework import serializers
from .models import ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_real_name = serializers.CharField(source='user.real_name', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = (
            'id', 'user', 'user_name', 'user_real_name',
            'title', 'messages', 'message_count',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def get_message_count(self, obj: ChatSession) -> int:
        return len(obj.messages) if isinstance(obj.messages, list) else 0
