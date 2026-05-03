from django.http import FileResponse, Http404
from rest_framework import viewsets, decorators, response, status
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import HasSkill
from .models import Report
from .serializers import (ReportListSerializer, ReportDetailSerializer,
                          GenerateReportSerializer)
from . import services


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, HasSkill]
    required_skill = 'report_gen'
    filterset_fields = ('lab_name', 'overall_severity', 'created_by', 'lab')
    search_fields = ('title', 'lab_name')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        return ReportDetailSerializer if self.action == 'retrieve' else ReportListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role != 'admin':
            qs = qs.filter(created_by=self.request.user)
        return qs

    @decorators.action(detail=False, methods=['post'])
    def generate(self, request):
        ser = GenerateReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        report = services.build_report(user=request.user, **ser.validated_data)
        return response.Response(ReportDetailSerializer(report).data,
                                 status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        report = self.get_object()
        services.regenerate_files(report)
        return response.Response(ReportDetailSerializer(report).data)

    @decorators.action(detail=True, methods=['get'], url_path='download/pdf')
    def download_pdf(self, request, pk=None):
        report = self.get_object()
        if not report.pdf_file:
            raise Http404
        return FileResponse(report.pdf_file.open('rb'),
                            as_attachment=True,
                            filename=f'{report.title or "report"}.pdf')

    @decorators.action(detail=True, methods=['get'], url_path='download/docx')
    def download_docx(self, request, pk=None):
        report = self.get_object()
        if not report.docx_file:
            raise Http404
        return FileResponse(report.docx_file.open('rb'),
                            as_attachment=True,
                            filename=f'{report.title or "report"}.docx')

    @decorators.action(detail=False, methods=['get'])
    def trend(self, request):
        lab = request.query_params.get('lab_name', '').strip()
        if not lab:
            return response.Response({'detail': 'lab_name 必填'},
                                     status=status.HTTP_400_BAD_REQUEST)
        return response.Response(services.trend_for_lab(lab))

    @decorators.action(detail=False, methods=['get'])
    def labs(self, request):
        labs = (Report.objects.values_list('lab_name', flat=True).distinct()
                .order_by('lab_name'))
        return response.Response({'labs': [l for l in labs if l]})
