from rest_framework import viewsets, decorators, response, status, parsers
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import HasSkill
from .models import HazardDetection
from .serializers import HazardDetectionSerializer, DetectRequestSerializer
from .services import detect_and_annotate


class HazardDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HazardDetectionSerializer
    permission_classes = [IsAuthenticated, HasSkill]
    required_skill = 'hazard_detect'
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filterset_fields = ('lab_name', 'overall_severity', 'user', 'lab')
    search_fields = ('lab_name', 'summary')

    def get_queryset(self):
        qs = HazardDetection.objects.all().order_by('-created_at')
        if self.request.user.role != 'admin':
            qs = qs.filter(user=self.request.user)
        return qs

    @decorators.action(detail=False, methods=['post'])
    def detect(self, request):
        ser = DetectRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lab_id = ser.validated_data.get('lab_id')
        other_location = ser.validated_data.get('other_location', '')
        lab = None
        if lab_id:
            from apps.labs.models import Lab
            try:
                lab = Lab.objects.get(pk=lab_id)
            except Lab.DoesNotExist:
                pass
        detection = detect_and_annotate(
            user=request.user,
            image_file=ser.validated_data['image'],
            lab_name=lab.name if lab else other_location,
            extra_instruction=ser.validated_data['extra_instruction'],
        )
        detection.lab = lab
        detection.other_location = other_location if not lab else ''
        detection.save()
        return response.Response(HazardDetectionSerializer(detection).data,
                                 status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        # 普通角色只能删自己的;admin 可删全部
        instance = self.get_object()
        if request.user.role != 'admin' and instance.user_id != request.user.id:
            return response.Response({'detail': '无权删除'}, status=status.HTTP_403_FORBIDDEN)
        for f in (instance.original_image, instance.annotated_image):
            if f:
                try:
                    f.delete(save=False)
                except Exception:
                    pass
        instance.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=False, methods=['get'])
    def labs(self, request):
        labs = (HazardDetection.objects.values_list('lab_name', flat=True).distinct()
                .order_by('lab_name'))
        return response.Response({'labs': [l for l in labs if l]})

    @decorators.action(detail=True, methods=['patch'])
    def update_lab(self, request, pk=None):
        instance = self.get_object()
        if request.user.role != 'admin' and instance.user_id != request.user.id:
            return response.Response({'detail': '无权修改'}, status=status.HTTP_403_FORBIDDEN)
        lab_name = request.data.get('lab_name', '').strip()
        instance.lab_name = lab_name
        instance.save(update_fields=['lab_name'])
        return response.Response(HazardDetectionSerializer(instance).data)

    @decorators.action(detail=True, methods=['patch'])
    def update_location(self, request, pk=None):
        instance = self.get_object()
        if request.user.role != 'admin' and instance.user_id != request.user.id:
            return response.Response({'detail': '无权修改'}, status=status.HTTP_403_FORBIDDEN)
        lab_id = request.data.get('lab_id')
        other_location = request.data.get('other_location', '').strip()
        if lab_id:
            from apps.labs.models import Lab
            try:
                instance.lab = Lab.objects.get(pk=lab_id)
                instance.other_location = ''
            except Lab.DoesNotExist:
                instance.lab = None
        else:
            instance.lab = None
            instance.other_location = other_location
        instance.save()
        return response.Response(HazardDetectionSerializer(instance).data)

    http_method_names = ['get', 'post', 'delete', 'patch']
