import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.common.llm import get_vision_llm


class Command(BaseCommand):
    help = '测试视觉模型直接理解本地视频文件'

    def add_arguments(self, parser):
        parser.add_argument('video_path', help='本地视频路径,如 C:\\path\\demo.mp4')
        parser.add_argument(
            '--instruction',
            default='',
            help='补充说明,如关注电气线路、消防通道等',
        )

    def handle(self, *args, **options):
        path = Path(options['video_path'])
        if not path.exists():
            raise CommandError(f'视频不存在: {path}')
        if not path.is_file():
            raise CommandError(f'不是文件: {path}')

        result = get_vision_llm().detect_hazards_in_video(
            path,
            extra_instruction=options['instruction'],
        )
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
