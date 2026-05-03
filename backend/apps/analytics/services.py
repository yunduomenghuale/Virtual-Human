"""数据分析聚合服务。"""
from __future__ import annotations
from collections import Counter
from datetime import timedelta
from typing import Dict, Any

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.users.models import User
from apps.knowledge.models import KnowledgeDocument, QASession
from apps.hazards.models import HazardDetection
from apps.reports.models import Report


def overview(lab_name: str = '') -> Dict[str, Any]:
    user_qs = User.objects.all()
    det_qs = HazardDetection.objects.all()
    rep_qs = Report.objects.all()
    if lab_name:
        user_qs = user_qs.filter(lab_name=lab_name)
        det_qs = det_qs.filter(lab_name=lab_name)
        rep_qs = rep_qs.filter(lab_name=lab_name)
    return {
        'users': {
            'total': user_qs.count(),
            'admin': user_qs.filter(role='admin').count(),
            'safety_officer': user_qs.filter(role='safety_officer').count(),
            'experimenter': user_qs.filter(role='experimenter').count(),
        },
        'knowledge_docs': KnowledgeDocument.objects.count(),
        'qa_sessions': QASession.objects.count(),
        'detections': det_qs.count(),
        'reports': rep_qs.count(),
        'lab_name': lab_name or '全部',
    }


def severity_distribution(lab_name: str = '') -> Dict[str, int]:
    """隐患等级分布。支持按实验室过滤。"""
    qs = HazardDetection.objects.all()
    if lab_name:
        qs = qs.filter(lab_name=lab_name)
    counter = Counter()
    for det in qs.values_list('hazards', flat=True):
        for h in (det or []):
            counter[h.get('severity', 'medium')] += 1
    return dict(counter)


def category_distribution(limit: int = 10, lab_name: str = '') -> list:
    qs = HazardDetection.objects.all()
    if lab_name:
        qs = qs.filter(lab_name=lab_name)
    counter = Counter()
    for det in qs.values_list('hazards', flat=True):
        for h in (det or []):
            counter[h.get('category', '其他')] += 1
    return [{'category': k, 'count': v}
            for k, v in counter.most_common(limit)]


def detection_trend(days: int = 30, lab_name: str = '') -> list:
    start = timezone.now().date() - timedelta(days=days - 1)
    qs = HazardDetection.objects.filter(created_at__date__gte=start)
    if lab_name:
        qs = qs.filter(lab_name=lab_name)
    qs = (qs.annotate(d=TruncDate('created_at'))
          .values('d')
          .annotate(c=Count('id'))
          .order_by('d'))
    by_date = {row['d']: row['c'] for row in qs}
    points = []
    for i in range(days):
        day = start + timedelta(days=i)
        points.append({'date': day.strftime('%Y-%m-%d'), 'count': by_date.get(day, 0)})
    return points


def top_labs(limit: int = 5, lab_name: str = '') -> list:
    qs = HazardDetection.objects.all()
    if lab_name:
        qs = qs.filter(lab_name=lab_name)
    counter = Counter()
    for det in qs:
        if not det.lab_name:
            continue
        counter[det.lab_name] += len(det.hazards or [])
    return [{'lab_name': lab, 'hazards': cnt}
            for lab, cnt in counter.most_common(limit)]


def lab_overview() -> list:
    """以实验室为维度聚合:用户数 / 报告数 / 累计隐患 / 高中低 / 最近报告时间。"""
    labs: Dict[str, Dict[str, Any]] = {}

    def _bucket(name: str) -> Dict[str, Any]:
        if name not in labs:
            labs[name] = {
                'lab_name': name,
                'user_count': 0,
                'detection_count': 0,
                'report_count': 0,
                'hazards_total': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'last_report_at': None,
                'overall_severity': 'low',
            }
        return labs[name]

    for u in User.objects.exclude(lab_name=''):
        _bucket(u.lab_name)['user_count'] += 1

    for det in HazardDetection.objects.exclude(lab_name=''):
        b = _bucket(det.lab_name)
        b['detection_count'] += 1
        for h in (det.hazards or []):
            b['hazards_total'] += 1
            sev = h.get('severity', 'medium')
            if sev in ('high', 'medium', 'low'):
                b[sev] += 1

    for r in Report.objects.exclude(lab_name='').order_by('-created_at'):
        b = _bucket(r.lab_name)
        b['report_count'] += 1
        if not b['last_report_at']:
            b['last_report_at'] = r.created_at.strftime('%Y-%m-%d %H:%M')
            b['overall_severity'] = r.overall_severity or 'low'

    rows = list(labs.values())
    rows.sort(key=lambda x: (-x['hazards_total'], -x['report_count'], x['lab_name']))
    return rows


def skill_usage() -> Dict[str, int]:
    """近 30 天各 skill 的调用量(用于估算热度)。"""
    since = timezone.now() - timedelta(days=30)
    return {
        'knowledge_qa': QASession.objects.filter(created_at__gte=since).count(),
        'hazard_detect': HazardDetection.objects.filter(created_at__gte=since).count(),
        'report_gen': Report.objects.filter(created_at__gte=since).count(),
    }


def dashboard() -> Dict[str, Any]:
    return {
        'overview': overview(),
        'severity_distribution': severity_distribution(),
        'category_distribution': category_distribution(),
        'detection_trend': detection_trend(),
        'top_labs': top_labs(),
        'skill_usage': skill_usage(),
    }
