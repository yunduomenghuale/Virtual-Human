from rest_framework import serializers
from .models import Report


class ReportListSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='created_by.username', read_only=True)
    detection_count = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = ('id', 'title', 'lab_name', 'address', 'inspector', 'overall_severity',
                  'summary_stats', 'creator_name', 'detection_count',
                  'pdf_file', 'docx_file', 'created_at', 'updated_at')

    def get_detection_count(self, obj):
        return obj.detections.count()


class ReportDetailSerializer(ReportListSerializer):
    detections = serializers.SerializerMethodField()

    class Meta(ReportListSerializer.Meta):
        fields = ReportListSerializer.Meta.fields + (
            'agent_evaluation', 'references', 'extra_notes', 'detections',
        )

    def get_detections(self, obj):
        return [
            {
                'id': d.id, 'lab_name': d.lab_name,
                'media_type': d.media_type,
                'summary': d.summary,
                'overall_severity': d.overall_severity,
                'hazards': d.hazards,
                'cover_image': d.cover_image.url if d.cover_image else None,
                'original_image': d.original_image.url if d.original_image else None,
                'annotated_image': d.annotated_image.url if d.annotated_image else None,
                'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for d in obj.detections.all().order_by('created_at')
        ]


class GenerateReportSerializer(serializers.Serializer):
    title = serializers.CharField()
    lab_name = serializers.CharField(required=False, allow_blank=True, default='')
    address = serializers.CharField(required=False, allow_blank=True, default='')
    inspector = serializers.CharField(required=False, allow_blank=True, default='')
    detection_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    extra_notes = serializers.CharField(required=False, allow_blank=True, default='')
    lab_id = serializers.IntegerField(required=False, allow_null=True)
    other_location = serializers.CharField(required=False, allow_blank=True, default='')
