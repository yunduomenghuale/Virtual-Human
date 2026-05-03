from rest_framework import serializers
from .models import Lab


class LabSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.real_name', read_only=True)

    class Meta:
        model = Lab
        fields = ('id', 'name', 'manager', 'manager_name', 'created_at', 'updated_at')
