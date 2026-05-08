"""深度分析服务: 趋势根因分析 + 预测性分析。

利用 LLM 的推理能力,结合历史隐患数据进行诊断性和预测性分析。
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.common.llm import get_text_llm
from apps.hazards.models import HazardDetection


# ---------- 数据聚合 ----------

def _fetch_detection_data(lab_name: Optional[str], days: int) -> List[HazardDetection]:
    """查询指定时间范围内的隐患识别记录。"""
    since = timezone.now() - timedelta(days=days)
    qs = HazardDetection.objects.filter(created_at__gte=since)
    if lab_name:
        qs = qs.filter(lab_name=lab_name)
    return list(qs.select_related('lab', 'user').order_by('-created_at'))


def _build_stats(detections: List[HazardDetection]) -> Dict[str, Any]:
    """从隐患记录中提取统计特征。"""
    if not detections:
        return {'total': 0, 'by_category': {}, 'by_severity': {}, 'by_day': {}, 'recurring': []}

    all_hazards = []
    for det in detections:
        all_hazards.extend(det.hazards or [])

    by_category = Counter(h.get('category', '其他') for h in all_hazards)
    by_severity = Counter(h.get('severity', 'medium') for h in all_hazards)

    # 按天聚合
    by_day = defaultdict(lambda: {'count': 0, 'high': 0, 'medium': 0, 'low': 0})
    for det in detections:
        day = det.created_at.strftime('%Y-%m-%d')
        by_day[day]['count'] += len(det.hazards or [])
        for h in det.hazards or []:
            sev = h.get('severity', 'medium')
            by_day[day][sev] += 1

    # 重复隐患模式: 按隐患名称统计出现次数
    by_name = Counter(h.get('name', '未命名') for h in all_hazards)
    recurring = [
        {'name': name, 'count': cnt, 'category': next(
            (h.get('category', '其他') for h in all_hazards if h.get('name') == name), '其他'
        )}
        for name, cnt in by_name.most_common(5) if cnt >= 2
    ]

    # 周内分布
    weekday_dist = Counter(det.created_at.weekday() for det in detections)
    weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    by_weekday = {weekday_labels[i]: weekday_dist.get(i, 0) for i in range(7)}

    # 按实验室聚合(用于全局分析)
    by_lab = defaultdict(lambda: {'count': 0, 'high': 0, 'medium': 0, 'low': 0, 'categories': Counter()})
    for det in detections:
        lab = det.lab_name or '未填写'
        by_lab[lab]['count'] += len(det.hazards or [])
        for h in det.hazards or []:
            sev = h.get('severity', 'medium')
            by_lab[lab][sev] += 1
            by_lab[lab]['categories'][h.get('category', '其他')] += 1

    by_lab_summary = {
        lab: {
            'count': data['count'],
            'high': data['high'],
            'medium': data['medium'],
            'low': data['low'],
            'top_category': data['categories'].most_common(1)[0][0] if data['categories'] else '-',
        }
        for lab, data in sorted(by_lab.items(), key=lambda x: -x[1]['count'])[:10]
    }

    return {
        'total': len(all_hazards),
        'detection_count': len(detections),
        'by_category': dict(by_category),
        'by_severity': dict(by_severity),
        'by_day': dict(by_day),
        'by_weekday': by_weekday,
        'by_lab': by_lab_summary,
        'recurring': recurring,
        'top_hazards': [
            {'name': name, 'count': cnt, 'category': next(
                (h.get('category', '其他') for h in all_hazards if h.get('name') == name), '其他'
            )}
            for name, cnt in by_name.most_common(8)
        ],
    }


def _get_sample_cases(detections: List[HazardDetection], limit: int = 3) -> List[Dict[str, Any]]:
    """提取典型案例用于 LLM 分析。"""
    samples = []
    for det in detections[:limit]:
        samples.append({
            'lab_name': det.lab_name or '未填写',
            'created_at': det.created_at.strftime('%Y-%m-%d %H:%M'),
            'severity': det.overall_severity,
            'summary': det.summary,
            'hazards': [
                {k: v for k, v in h.items() if k != 'bbox'}
                for h in (det.hazards or [])[:3]
            ],
        })
    return samples


# ---------- 根因分析 ----------

RCA_PROMPT = (
    '你是消防安全管理专家,擅长通过数据分析发现隐患背后的系统性根因。'
    '请基于以下实验室隐患数据,进行深度根因分析。'
    '\n\n## 分析要求'
    '\n1. 从"管理因素、设备因素、环境因素、人员因素"四个维度分析根本原因'
    '\n2. 每个维度给出具体发现、支撑证据和置信度(高/中/低)'
    '\n3. 识别高风险热点(哪类隐患在上升/持平/下降)'
    '\n4. 给出具体可执行的整改建议(3-5条)'
    '\n5. 用中文回答,语气专业、简洁,禁止输出markdown代码块'
    '\n\n请严格按以下JSON格式输出,不要附加任何额外文字:'
    '\n{\n'
    '  "summary": "整体结论,2-3句话",\n'
    '  "root_causes": [\n'
    '    {"dimension": "管理|设备|环境|人员", "finding": "具体发现", "evidence": "数据支撑", "confidence": "高|中|低"}\n'
    '  ],\n'
    '  "risk_hotspots": [\n'
    '    {"category": "隐患类别", "trend": "上升|持平|下降", "urgency": "紧急|重要|一般", "reason": "趋势原因"}\n'
    '  ],\n'
    '  "recommendations": ["建议1", "建议2", ...]\n'
    '}'
)


def analyze_root_cause(lab_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """对指定实验室(或全部)进行趋势根因分析。

    :return: 结构化分析结果
    """
    detections = _fetch_detection_data(lab_name, days)
    stats = _build_stats(detections)

    if stats['total'] == 0:
        return {
            'type': 'root_cause_analysis',
            'lab_name': lab_name or '全部',
            'period_days': days,
            'summary': f'最近 {days} 天内无隐患识别记录,无法进行分析。',
            'root_causes': [],
            'risk_hotspots': [],
            'recommendations': ['建议定期开展隐患排查,积累数据后可进行根因分析。'],
            'stats': stats,
        }

    samples = _get_sample_cases(detections, limit=3)

    # 构建数据上下文
    scope_note = '【全局分析】请对各实验室进行横向对比,指出哪些实验室是高风险区域,哪些管理较好。' if not lab_name else ''
    lab_comparison = f'\n各实验室分布: {stats.get("by_lab", {})}\n' if not lab_name else ''
    data_context = (
        f'分析对象: {lab_name or "全部实验室"}\n'
        f'时间范围: 最近 {days} 天\n'
        f'隐患总数: {stats["total"]} (来自 {stats["detection_count"]} 次识别)\n'
        f'类别分布: {stats["by_category"]}\n'
        f'等级分布: {stats["by_severity"]}\n'
        f'周内分布: {stats["by_weekday"]}\n'
        f'重复隐患模式: {stats["recurring"]}\n'
        f'{lab_comparison}'
        f'典型案例: {samples}\n'
        f'{scope_note}'
    )

    llm = get_text_llm()
    response = llm.chat(
        [
            {'role': 'system', 'content': RCA_PROMPT},
            {'role': 'user', 'content': data_context},
        ],
        temperature=0.2,
        max_tokens=1800,
    )

    # 尝试解析 JSON
    result = _parse_json_response(response)
    if not result:
        result = {
            'summary': response[:300] if response else '分析完成',
            'root_causes': [],
            'risk_hotspots': [],
            'recommendations': [],
        }

    result.update({
        'type': 'root_cause_analysis',
        'lab_name': lab_name or '全部',
        'period_days': days,
        'stats': stats,
    })
    return result


# ---------- 预测性分析 ----------

PREDICTION_PROMPT = (
    '你是消防安全风险预测专家,擅长基于历史数据趋势进行前瞻性风险研判。'
    '请基于以下历史隐患数据,预测未来风险趋势。'
    '\n\n## 分析要求'
    '\n1. 分析历史趋势特征(上升/下降/波动/季节性)'
    '\n2. 预测未来各时段的风险等级和可能出现的隐患类别'
    '\n3. 给出早期预警(哪些类别风险正在累积)'
    '\n4. 结合季节因素给出洞察(如夏季高温、梅雨潮湿等)'
    '\n5. 用中文回答,语气专业、简洁,禁止输出markdown代码块'
    '\n\n请严格按以下JSON格式输出,不要附加任何额外文字:'
    '\n{\n'
    '  "summary": "整体预测结论,2-3句话",\n'
    '  "trend_assessment": "历史趋势特征描述",\n'
    '  "forecast": [\n'
    '    {"period": "未来1周|未来2-4周|未来1-3月", "risk_level": "高|中|低", "likely_categories": ["类别1", "类别2"], "confidence": "高|中|低", "reasoning": "推理依据"}\n'
    '  ],\n'
    '  "early_warnings": [\n'
    '    {"category": "隐患类别", "reason": "预警原因", "suggested_action": "建议措施"}\n'
    '  ],\n'
    '  "seasonal_insights": "季节因素分析"\n'
    '}'
)


def predict_risks(lab_name: Optional[str] = None, days: int = 30,
                  forecast_days: int = 30) -> Dict[str, Any]:
    """基于历史数据进行风险预测。

    :return: 结构化预测结果
    """
    detections = _fetch_detection_data(lab_name, days)
    stats = _build_stats(detections)

    # 构建时间序列
    historical_trend = []
    for day_str in sorted(stats['by_day'].keys()):
        d = stats['by_day'][day_str]
        historical_trend.append({
            'date': day_str,
            'count': d['count'],
            'high_risk_count': d['high'],
        })

    if stats['total'] == 0:
        return {
            'type': 'risk_prediction',
            'lab_name': lab_name or '全部',
            'historical_days': days,
            'forecast_days': forecast_days,
            'summary': f'最近 {days} 天内无隐患识别记录,无法建立预测模型。',
            'trend_assessment': '数据不足',
            'forecast': [],
            'early_warnings': [],
            'seasonal_insights': '建议积累至少 2 周以上的隐患数据后再进行预测分析。',
            'historical_trend': [],
            'stats': stats,
        }

    # 当前月份用于季节分析
    current_month = timezone.now().month
    season_hint = {
        3: '春季', 4: '春季', 5: '春季',
        6: '夏季', 7: '夏季', 8: '夏季',
        9: '秋季', 10: '秋季', 11: '秋季',
        12: '冬季', 1: '冬季', 2: '冬季',
    }.get(current_month, '')

    scope_note = '【全局分析】请对各实验室分别预测,指出不同实验室的未来风险差异。' if not lab_name else ''
    lab_comparison = f'\n各实验室分布: {stats.get("by_lab", {})}\n' if not lab_name else ''
    data_context = (
        f'分析对象: {lab_name or "全部实验室"}\n'
        f'历史数据: 最近 {days} 天\n'
        f'预测周期: 未来 {forecast_days} 天\n'
        f'当前季节: {season_hint}\n'
        f'历史隐患总数: {stats["total"]}\n'
        f'类别分布: {stats["by_category"]}\n'
        f'等级分布: {stats["by_severity"]}\n'
        f'{lab_comparison}'
        f'时间序列(按天): {historical_trend[-14:]}\n'  # 最近14天数据
        f'重复隐患模式: {stats["recurring"]}\n'
        f'{scope_note}'
    )

    llm = get_text_llm()
    response = llm.chat(
        [
            {'role': 'system', 'content': PREDICTION_PROMPT},
            {'role': 'user', 'content': data_context},
        ],
        temperature=0.25,
        max_tokens=1800,
    )

    result = _parse_json_response(response)
    if not result:
        result = {
            'summary': response[:300] if response else '预测完成',
            'trend_assessment': '',
            'forecast': [],
            'early_warnings': [],
            'seasonal_insights': '',
        }

    result.update({
        'type': 'risk_prediction',
        'lab_name': lab_name or '全部',
        'historical_days': days,
        'forecast_days': forecast_days,
        'historical_trend': historical_trend,
        'stats': stats,
    })
    return result


# ---------- helpers ----------

def _parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """从 LLM 响应中提取 JSON 对象。"""
    import json, re
    if not text:
        return None
    # 尝试直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    # 尝试提取 ```json ... ```
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # 尝试提取第一个 {...}
    m = re.search(r'(\{.*\})', text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None
