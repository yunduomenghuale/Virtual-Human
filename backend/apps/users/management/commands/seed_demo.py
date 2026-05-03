"""一键初始化:默认账号 + skill 权限 + 示例知识库。

用法::

    python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import User, Role
from apps.skill_permissions.services import ensure_defaults


DEFAULT_USERS = [
    {'username': 'admin', 'password': 'admin123', 'role': Role.ADMIN,
     'real_name': '系统管理员', 'lab_name': '总控中心', 'is_staff': True, 'is_superuser': True},
    {'username': 'safety', 'password': 'safety123', 'role': Role.SAFETY_OFFICER,
     'real_name': '李安全', 'lab_name': '化学楼 301'},
    {'username': 'student', 'password': 'student123', 'role': Role.EXPERIMENTER,
     'real_name': '王同学', 'lab_name': '化学楼 305'},
]


class Command(BaseCommand):
    help = '初始化默认账号 / skill 权限 / 知识库'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. 默认权限矩阵
        ensure_defaults()
        self.stdout.write(self.style.SUCCESS('✔ 默认 skill 权限已就绪'))

        # 2. 默认用户
        for original in DEFAULT_USERS:
            cfg = dict(original)
            password = cfg.pop('password')
            user, created = User.objects.get_or_create(
                username=cfg['username'], defaults=cfg,
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"✔ 创建账号 {user.username} (密码: {password})"))
            else:
                self.stdout.write(f"○ 已存在账号 {user.username}")

        # 3. 加载示例知识库
        from apps.knowledge.services import ingest_default_corpus
        n = ingest_default_corpus()
        self.stdout.write(self.style.SUCCESS(f'✔ 已写入 {n} 条知识库片段'))

        self.stdout.write(self.style.SUCCESS('\n=== 演示账号 ==='))
        for cfg in DEFAULT_USERS:
            self.stdout.write(f"  {cfg['username']:10s} / {cfg['username']}123  ({Role(cfg['role']).label})")
