from rest_framework import serializers
from .models import HazardDetection


class HazardDetectionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    hazard_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HazardDetection
        fields = ('id', 'user', 'user_name', 'lab_name',
                  'original_image', 'annotated_image',
                  'summary', 'overall_severity', 'hazards',
                  'image_width', 'image_height', 'hazard_count', 'created_at')
        read_only_fields = fields


class DetectRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()
    lab_name = serializers.CharField(required=False, allow_blank=True, default='')
    extra_instruction = serializers.CharField(required=False, allow_blank=True, default='')
    lab_id = serializers.IntegerField(required=False, allow_null=True)
    other_location = serializers.CharField(required=False, allow_blank=True, default='')
