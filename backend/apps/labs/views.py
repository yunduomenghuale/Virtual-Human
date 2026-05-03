from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.common.permissions import IsAdminOrSafetyOfficer
from .models import Lab
from .serializers import LabSerializer


class LabViewSet(viewsets.ModelViewSet):
    serializer_class = LabSerializer
    queryset = Lab.objects.all().order_by('name')
    filterset_fields = ('name',)
    search_fields = ('name', 'address')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrSafetyOfficer()]
