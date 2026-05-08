"""报告生成业务流。"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from typing import List

from django.conf import settings
from django.core.files import File
from django.utils import timezone

from apps.common.llm import get_text_llm
from apps.knowledge.services import retrieve
from apps.hazards.models import HazardDetection

from .models import Report
from .pdf_writer import render_pdf
from .docx_writer import render_docx


def _aggregate_stats(detections) -> dict:
    by_sev = Counter()
    by_cat = Counter()
    for det in detections:
        for h in (det.hazards or []):
            by_sev[h.get('severity', 'medium')] += 1
            by_cat[h.get('category', '其他')] += 1
    total = sum(by_sev.values())
    return {
        'total': total,
        'by_severity': dict(by_sev),
        'by_category': dict(by_cat),
    }


def _overall_severity(stats: dict) -> str:
    by = stats.get('by_severity', {})
    if by.get('high', 0) > 0:
        return 'high'
    if by.get('medium', 0) > 0:
        return 'medium'
    return 'low'


def _agent_evaluation(report_data: dict) -> str:
    summary = (
        f"实验室:{report_data['lab_name']}; 总体风险:{report_data['overall_severity']}; "
        f"统计:{report_data['summary_stats']}; 主要隐患:{report_data['hazards_brief']}"
    )
    prompt = (
        '请根据以下检查数据,生成一段不少于 200 字的实验室消防安全检查总结评价,'
        '需包含:1) 整体安全评估;2) 主要风险点;3) 整改优先级建议;4) 后续复查建议。'
        '\n\n' + summary
    )
    return get_text_llm().chat([
        {'role': 'system', 'content': '你是实验室消防安全专家,撰写专业、严谨、可执行的检查评价。'},
        {'role': 'user', 'content': prompt},
    ], temperature=0.3, max_tokens=2000)


def _references(detections) -> list:
    """为报告附上 RAG 检索到的参考资料。"""
    keys = []
    for det in detections:
        for h in det.hazards or []:
            keys.append(h.get('category', ''))
    seen = set()
    refs = []
    for k in keys:
        if not k or k in seen:
            continue
        seen.add(k)
        for chunk in retrieve(k + ' 实验室 隐患 整改', top_k=2):
            title = chunk['metadata'].get('title', '')
            if title and title not in {r['title'] for r in refs}:
                refs.append({'title': title, 'snippet': chunk['text'][:160]})
        if len(refs) >= 5:
            break
    return refs[:5]


def build_report(*, title: str, lab_name: str, address: str = '', inspector: str,
                 detection_ids: List[int], extra_notes: str, user,
                 lab_id: int = None, other_location: str = '') -> Report:
    lab = None
    if lab_id:
        from apps.labs.models import Lab
        try:
            lab = Lab.objects.get(pk=lab_id)
        except Lab.DoesNotExist:
            pass
    effective_lab_name = lab.name if lab else (other_location or lab_name)

    detections = list(HazardDetection.objects.filter(id__in=detection_ids).order_by('created_at'))
    stats = _aggregate_stats(detections)
    overall = _overall_severity(stats)

    hazards_brief = []
    for det in detections:
        for h in det.hazards or []:
            hazards_brief.append(f"[{h.get('severity','m')}]{h.get('name','')}")
    hazards_brief_text = '; '.join(hazards_brief[:30]) or '无'

    eval_input = {
        'lab_name': effective_lab_name,
        'overall_severity': overall,
        'summary_stats': stats,
        'hazards_brief': hazards_brief_text,
    }
    evaluation = _agent_evaluation(eval_input)
    refs = _references(detections)

    report = Report.objects.create(
        title=title,
        lab_name=effective_lab_name,
        address=address,
        inspector=inspector,
        summary_stats=stats,
        agent_evaluation=evaluation,
        references=refs,
        extra_notes=extra_notes,
        overall_severity=overall,
        created_by=user,
        lab=lab,
        other_location=other_location if not lab else '',
    )
    if detections:
        report.detections.set(detections)

    # 渲染 PDF / DOCX
    base = settings.REPORTS_DIR
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_lab = (effective_lab_name or 'lab').replace('/', '_').replace('\\', '_')
    pdf_path = base / 'pdf' / f'report_{report.id}_{safe_lab}_{ts}.pdf'
    docx_path = base / 'docx' / f'report_{report.id}_{safe_lab}_{ts}.docx'
    render_pdf(report, detections, pdf_path)
    render_docx(report, detections, docx_path)

    with open(pdf_path, 'rb') as fh:
        report.pdf_file.save(pdf_path.name, File(fh), save=False)
    with open(docx_path, 'rb') as fh:
        report.docx_file.save(docx_path.name, File(fh), save=False)
    report.save()
    return report


def regenerate_files(report: Report) -> Report:
    detections = list(report.detections.all().order_by('created_at'))
    base = settings.REPORTS_DIR
    ts = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_lab = (report.lab_name or 'lab').replace('/', '_').replace('\\', '_')
    pdf_path = base / 'pdf' / f'report_{report.id}_{safe_lab}_{ts}.pdf'
    docx_path = base / 'docx' / f'report_{report.id}_{safe_lab}_{ts}.docx'
    render_pdf(report, detections, pdf_path)
    render_docx(report, detections, docx_path)
    with open(pdf_path, 'rb') as fh:
        report.pdf_file.save(pdf_path.name, File(fh), save=True)
    with open(docx_path, 'rb') as fh:
        report.docx_file.save(docx_path.name, File(fh), save=True)
    return report


def trend_for_lab(lab_name: str) -> dict:
    """同一实验室的趋势分析:按时间序列统计隐患数与等级分布。"""
    reports = Report.objects.filter(lab_name=lab_name).order_by('created_at')
    points = []
    for r in reports:
        stats = r.summary_stats or {}
        by = stats.get('by_severity', {})
        points.append({
            'id': r.id,
            'title': r.title,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            'total': stats.get('total', 0),
            'high': by.get('high', 0),
            'medium': by.get('medium', 0),
            'low': by.get('low', 0),
            'overall_severity': r.overall_severity,
        })
    return {'lab_name': lab_name, 'points': points}
