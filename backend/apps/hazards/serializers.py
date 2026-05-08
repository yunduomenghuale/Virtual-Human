from rest_framework import serializers
from .models import HazardDetection


class HazardDetectionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    hazard_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HazardDetection
        fields = ('id', 'user', 'user_name', 'lab', 'lab_name', 'other_location', 'media_type',
                  'original_image', 'cover_image', 'annotated_image',
                  'summary', 'overall_severity', 'hazards',
                  'image_width', 'image_height', 'hazard_count', 'created_at')
        read_only_fields = fields


class DetectRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=False,
        write_only=True,
    )
    video = serializers.FileField(required=False)
    videos = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=False,
        write_only=True,
    )
    lab_name = serializers.CharField(required=False, allow_blank=True, default='')
    extra_instruction = serializers.CharField(required=False, allow_blank=True, default='')
    lab_id = serializers.IntegerField(required=False, allow_null=True)
    other_location = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        request = self.context.get('request')
        uploaded_items = []
        if attrs.get('image'):
            uploaded_items.append(('image', attrs['image']))
        if attrs.get('images'):
            uploaded_items.extend(('image', image) for image in attrs['images'])
        if attrs.get('video'):
            uploaded_items.append(('video', attrs['video']))
        if attrs.get('videos'):
            uploaded_items.extend(('video', video) for video in attrs['videos'])
        if request is not None:
            uploaded_items.extend(('image', image) for image in request.FILES.getlist('images'))
            uploaded_items.extend(('video', video) for video in request.FILES.getlist('videos'))

        deduped = []
        seen = set()
        for media_type, file_obj in uploaded_items:
            marker = id(file_obj)
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append((media_type, file_obj))

        if not deduped:
            raise serializers.ValidationError({'images': '请至少上传 1 张图片或视频'})
        attrs['media_items'] = deduped
        return attrs
