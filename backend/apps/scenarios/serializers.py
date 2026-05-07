from rest_framework import serializers
from .models import FireScenario, TrainingMaterial

class TrainingMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingMaterial
        fields = '__all__'
        read_only_fields = ('file_name', 'file_type', 'status', 'error_message', 'raw_analysis', 'result_teaching', 'result_scenarios')

class FireScenarioSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.file_name')
    
    class Meta:
        model = FireScenario
        fields = '__all__'
