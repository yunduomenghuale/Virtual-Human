import re
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import FireScenario, TrainingMaterial
from .serializers import FireScenarioSerializer, TrainingMaterialSerializer
from .doc_processor import DocProcessor
from apps.common.llm import get_text_llm

class FireScenarioViewSet(viewsets.ModelViewSet):
    queryset = FireScenario.objects.all().order_by('-created_at')
    serializer_class = FireScenarioSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        qs = super().get_queryset()
        topic = self.request.query_params.get('topic')
        difficulty = self.request.query_params.get('difficulty')
        if topic:
            qs = qs.filter(topic__icontains=topic)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    @action(detail=True, methods=['post'])
    def evaluate(self, request, pk=None):
        """对学员的演练答案进行 AI 评分。"""
        scenario = self.get_object()
        user_answer = request.data.get('answer', '').strip()
        if not user_answer:
            return Response({'error': '答案不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        llm = get_text_llm()
        prompt = (
            f"你是消防安全培训教官。请根据以下标准处置流程，对学员的回答进行严格评分。\n\n"
            f"场景：{scenario.title}\n"
            f"场景描述：{scenario.description}\n"
            f"标准处置流程：{scenario.correct_actions}\n\n"
            f"学员回答：\n{user_answer}\n\n"
            f"请按以下格式输出：\n"
            f"【评分】：X分\n"
            f"【理由】：(详细列出得分项和扣分项，如遗漏了致命步骤直接扣除大部分分数，并给出正确的标准操作)"
        )
        result = llm.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=1500)

        score_match = re.search(r'【评分】[：:]\s*(\d+)', result)
        score = int(score_match.group(1)) if score_match else 0

        return Response({
            'score': score,
            'analysis': result,
            'scenario_id': scenario.id,
        })

class TrainingMaterialViewSet(viewsets.ModelViewSet):
    queryset = TrainingMaterial.objects.all().order_by('-created_at')
    serializer_class = TrainingMaterialSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def perform_create(self, serializer):
        file_obj = self.request.data.get('file')
        serializer.save(
            file_name=file_obj.name,
            file_type=file_obj.name.split('.')[-1]
        )

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        material = self.get_object()
        material.status = 'processing'
        material.save()
        
        try:
            processor = DocProcessor()
            result = processor.analyze_content(material.file.path, material.file_type)
            
            material.raw_analysis = result
            material.result_teaching = result.get('teaching_content')
            material.result_scenarios = result.get('scenarios')
            material.status = 'completed'
            material.save()
            return Response(TrainingMaterialSerializer(material).data)
        except Exception as e:
            material.status = 'failed'
            material.error_message = str(e)
            material.save()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_import(self, request, pk=None):
        material = self.get_object()
        if material.status != 'completed':
            return Response({'error': '素材尚未解析完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        teaching_content = request.data.get('teaching_content', material.result_teaching)
        scenarios_data = request.data.get('scenarios', material.result_scenarios)
        
        created_count = 0
        for item in scenarios_data:
            FireScenario.objects.create(
                title=item.get('title'),
                topic=item.get('topic'),
                difficulty=item.get('difficulty', 'medium'),
                description=item.get('description'),
                correct_actions=item.get('correct_actions'),
                analysis=item.get('analysis'),
                teaching_content=teaching_content,
                material=material
            )
            created_count += 1
            
        return Response({'message': f'成功导入 {created_count} 个场景题目'})
