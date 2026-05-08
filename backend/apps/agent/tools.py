"""Agent 可调用的工具定义 + 派发逻辑。

每个工具对应一项 LLM skill,执行时:
1) 校验该用户对该 skill 的权限(RBAC)
2) 调用对应的业务 service
3) 返回两份结果:
   - `summary_for_llm`: 简短文本,作为 tool message 反馈给 LLM 续推
   - `payload_for_ui`: 结构化数据,前端按 type 渲染卡片
"""
from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from apps.skill_permissions.models import SkillCode
from apps.skill_permissions.services import is_skill_enabled

logger = logging.getLogger(__name__)

# 新增深度分析工具需要的模型导入(延迟导入避免循环依赖)
_QASession = None


def _get_qasession_model():
    global _QASession
    if _QASession is None:
        from apps.knowledge.models import QASession as _m
        _QASession = _m
    return _QASession


# ==========================================================
# Tool 定义(OpenAI tool-calling JSON Schema 格式)
# ==========================================================
TOOL_DEFS: List[Dict[str, Any]] = [
    {
        'type': 'function',
        'function': {
            'name': 'knowledge_qa',
            'description': (
                '检索内置消防安全知识库回答用户问题。适用于"什么是 / 怎么做 / '
                '规范要求"等概念性、规范性、流程性提问。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': '用户的具体问题或检索关键词',
                    },
                },
                'required': ['query'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'hazard_detect',
            'description': (
                '对【用户当前已上传的图片】调用视觉模型识别现场消防 / 安全隐患,'
                '自动框选位置。仅当用户在本轮对话中已上传图片时可用。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'lab_name': {
                        'type': 'string',
                        'description': '实验室名称(若用户在消息里提到)',
                    },
                    'extra_instruction': {
                        'type': 'string',
                        'description': '关注重点 / 额外指令(可空)',
                    },
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'report_gen',
            'description': (
                '为某实验室生成正式安全检查报告(PDF + Word)。系统会自动查询'
                '该实验室的历史隐患识别记录,无需用户手动提供 ID。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': '报告标题'},
                    'lab_name': {
                        'type': 'string',
                        'description': '实验室名称(可选,未提供时自动从识别记录推断)',
                    },
                    'address': {
                        'type': 'string',
                        'description': '检查地址(可选,未提供实验室名称时填写)',
                    },
                    'inspector': {'type': 'string', 'description': '检查人,可空'},
                    'detection_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': '要纳入报告的隐患识别记录 ID 数组(至少提供一个或提供 lab_name)',
                    },
                    'extra_notes': {
                        'type': 'string',
                        'description': '附加说明,可空',
                    },
                },
                'required': ['title'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'analytics_query',
            'description': (
                '查询系统聚合数据。metric 可选:'
                'overview(用户/文档/隐患总览)、severity(隐患等级分布)、'
                'category(隐患分类分布)、trend(近 30 日检测趋势)、'
                'top_labs(隐患排行)、lab_overview(实验室全景)、'
                'recent_detections(最近隐患识别记录,可用于报告生成)、'
                'all(完整 dashboard)。'
                '当用户提到具体实验室名称时,必须将 lab_name 传入以获取该实验室的专项数据,禁止返回全局数据。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'metric': {
                        'type': 'string',
                        'enum': ['overview', 'severity', 'category', 'trend',
                                 'top_labs', 'lab_overview',
                                 'recent_detections', 'all'],
                    },
                    'lab_name': {
                        'type': 'string',
                        'description': '实验室名称,所有指标均支持按实验室过滤。当用户问题涉及具体实验室时必须传入。',
                    },
                },
                'required': ['metric'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'root_cause_analysis',
            'description': (
                '深度根因分析: 基于历史隐患数据,从管理/设备/环境/人员四个维度'
                '分析某实验室隐患反复出现的根本原因。'
                '当用户问"为什么"、"怎么回事"、"原因是什么"、"分析一下"时使用。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'lab_name': {
                        'type': 'string',
                        'description': '实验室名称,不传则分析全部实验室',
                    },
                    'days': {
                        'type': 'integer',
                        'description': '分析最近多少天的数据,默认30',
                        'default': 30,
                    },
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'risk_prediction',
            'description': (
                '风险预测: 基于历史隐患时间序列+季节因素,预测未来风险趋势。'
                '当用户问"未来"、"预测"、"会不会"、"下个月"、"接下来"时使用。'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'lab_name': {
                        'type': 'string',
                        'description': '实验室名称,不传则预测全部',
                    },
                    'days': {
                        'type': 'integer',
                        'description': '历史回溯天数,默认30',
                        'default': 30,
                    },
                    'forecast_days': {
                        'type': 'integer',
                        'description': '预测未来天数,默认30',
                        'default': 30,
                    },
                },
                'required': [],
            },
        },
    },
]


# 工具名 -> SkillCode
SKILL_MAP: Dict[str, str] = {
    'knowledge_qa': SkillCode.KNOWLEDGE_QA,
    'hazard_detect': SkillCode.HAZARD_DETECT,
    'report_gen': SkillCode.REPORT_GEN,
    'analytics_query': SkillCode.ANALYTICS,
    'root_cause_analysis': SkillCode.ANALYTICS,
    'risk_prediction': SkillCode.ANALYTICS,
}


# ==========================================================
# 工具列表筛选
# ==========================================================
def filter_tools_for_user(user, has_attachment: bool) -> List[Dict[str, Any]]:
    """根据用户角色权限 + 是否上传图片,过滤可用工具。"""
    allowed: List[Dict[str, Any]] = []
    for t in TOOL_DEFS:
        name = t['function']['name']
        skill = SKILL_MAP.get(name)
        if skill and not is_skill_enabled(user.role, skill):
            continue
        if name == 'hazard_detect' and not has_attachment:
            continue
        allowed.append(t)
    return allowed


def list_skill_codes_for_user(user) -> List[str]:
    return [code for name, code in SKILL_MAP.items()
            if is_skill_enabled(user.role, code)]


# ==========================================================
# 工具执行
# ==========================================================
def execute_tool(*, name: str, args: Dict[str, Any], user,
                 attachment=None) -> Tuple[str, Dict[str, Any]]:
    """执行一个工具调用,返回 (LLM 续推用文本, 前端渲染用 payload)。"""
    skill = SKILL_MAP.get(name)
    if not skill:
        return f'工具 {name} 不存在。', _err_payload('未知工具', name)
    if not is_skill_enabled(user.role, skill):
        return (f'您当前角色没有 {name} 权限,已被系统拒绝。',
                _err_payload('权限不足', name))

    try:
        if name == 'knowledge_qa':
            return _run_knowledge_qa(args, user)
        if name == 'hazard_detect':
            return _run_hazard_detect(args, user, attachment)
        if name == 'report_gen':
            return _run_report_gen(args, user)
        if name == 'analytics_query':
            return _run_analytics(args)
        if name == 'root_cause_analysis':
            return _run_root_cause_analysis(args, user)
        if name == 'risk_prediction':
            return _run_risk_prediction(args, user)
    except Exception as exc:  # noqa: BLE001
        logger.exception('工具 %s 执行失败: %s', name, exc)
        return f'工具 {name} 执行失败:{exc}', _err_payload(str(exc), name)

    return f'未实现的工具 {name}', _err_payload('未实现', name)


# ----- knowledge_qa -----
def _run_knowledge_qa(args: Dict[str, Any], user) -> Tuple[str, Dict[str, Any]]:
    from apps.knowledge.services import answer_question
    from apps.knowledge.models import QASession
    query = (args.get('query') or '').strip()
    if not query:
        return '工具调用缺少 query 参数。', _err_payload('缺少 query', 'knowledge_qa')
    res = answer_question(query, top_k=4)
    answer = res.get('answer', '')
    QASession.objects.create(
        user=user,
        question=query,
        answer=answer,
        sources=res.get('sources', []),
    )
    # 返回给 LLM 的摘要简化为答案本身,不再列出参考资料
    return answer[:2000], {
        'type': 'knowledge_qa',
        'query': query,
        'answer': answer,
    }


# ----- hazard_detect -----
def _run_hazard_detect(args: Dict[str, Any], user, attachment) -> Tuple[str, Dict[str, Any]]:
    from apps.hazards.services import detect_and_annotate
    from apps.hazards.serializers import HazardDetectionSerializer
    if attachment is None:
        return ('用户尚未上传图片,无法执行隐患识别;请告知用户上传一张现场照片。',
                _err_payload('缺少图片', 'hazard_detect'))
    lab_name = (args.get('lab_name') or '').strip()
    extra = (args.get('extra_instruction') or '').strip()
    content_type = getattr(attachment, 'content_type', '') or ''
    name_lower = (getattr(attachment, 'name', '') or '').lower()
    media_type = 'video' if content_type.startswith('video/') or name_lower.endswith(('.mp4', '.mov', '.webm', '.m4v')) else 'image'
    detection = detect_and_annotate(
        user=user, image_file=attachment,
        lab_name=lab_name, extra_instruction=extra,
        media_type=media_type,
    )
    payload = HazardDetectionSerializer(detection).data
    hazards = payload.get('hazards') or []
    by_sev = {'high': 0, 'medium': 0, 'low': 0}
    for h in hazards:
        by_sev[h.get('severity', 'medium')] = by_sev.get(h.get('severity', 'medium'), 0) + 1

    high_risks = [h['name'] for h in hazards if h.get('severity') == 'high']
    # 清理建议末尾标点，避免拼接后重复
    _raw_suggestions = [h['suggestion'].rstrip('；;。.,') for h in hazards[:2]]
    suggestions = [s for s in _raw_suggestions if s]

    parts = [
        f'本次检查共发现 {len(hazards)} 项隐患'
        f'(高风险 {by_sev.get("high",0)} / 中风险 {by_sev.get("medium",0)} / 低风险 {by_sev.get("low",0)})。'
    ]
    if high_risks:
        parts.append(f'其中{"、".join(high_risks)} 属于高风险问题，需立即整改。')
    if suggestions:
        parts.append('建议优先处理：' + '；'.join(suggestions) + '。')
    user_summary = '\n'.join(parts)

    # 精简 payload:去掉 annotated_image 和 bbox
    clean_payload = {
        'id': payload.get('id'),
        'lab_name': payload.get('lab_name'),
        'media_type': payload.get('media_type'),
        'cover_image': payload.get('cover_image'),
        'overall_severity': payload.get('overall_severity'),
        'summary': payload.get('summary'),
        'hazard_count': payload.get('hazard_count'),
        'hazards': [
            {k: v for k, v in h.items() if k != 'bbox'}
            for h in hazards
        ],
        'original_image': payload.get('original_image'),
        'created_at': payload.get('created_at'),
    }

    return user_summary, {
        'type': 'hazard_detection',
        'data': clean_payload,
        'user_summary': user_summary,
    }


# ----- report_gen -----
def _run_report_gen(args: Dict[str, Any], user) -> Tuple[str, Dict[str, Any]]:
    from apps.reports.services import build_report
    from apps.reports.serializers import ReportDetailSerializer
    from apps.hazards.models import HazardDetection
    title = (args.get('title') or '').strip()
    lab_name = (args.get('lab_name') or '').strip()
    address = (args.get('address') or '').strip()
    detection_ids = args.get('detection_ids') or []
    if not title:
        return ('缺少必填参数:title。', _err_payload('缺少 title', 'report_gen'))
    if not lab_name:
        return ('请提供实验室名称或地点，以便查询对应的隐患识别记录。',
                _err_payload('缺少地点', 'report_gen'))
    # 若未提供识别记录,按 lab_name 自动查询最新的一条
    if not isinstance(detection_ids, list) or not detection_ids:
        qs = HazardDetection.objects.filter(lab_name=lab_name).order_by('-created_at')
        if not qs.exists():
            qs = HazardDetection.objects.filter(lab__name=lab_name).order_by('-created_at')
        if not qs.exists():
            normalized = lab_name.replace(' ', '').replace('　', '')
            candidates = HazardDetection.objects.exclude(lab_name='').order_by('-created_at')[:50]
            matched_ids = []
            for d in candidates:
                if d.lab_name.replace(' ', '').replace('　', '') == normalized:
                    matched_ids.append(d.id)
                if len(matched_ids) >= 10:
                    break
            if matched_ids:
                qs = HazardDetection.objects.filter(id__in=matched_ids).order_by('-created_at')
        detection_ids = [d.id for d in qs[:10]]
    else:
        detection_ids = detection_ids[:10]
    if not detection_ids:
        return ('该实验室暂无常患识别记录，无法生成报告。您可以先上传一张现场照片，我将为您识别隐患并保存记录，随后即可生成正式的安全检查报告。',
                _err_payload('无记录', 'report_gen'))
    # 尝试查找 Lab 实体建立外键绑定
    lab_id = None
    if lab_name:
        from apps.labs.models import Lab
        try:
            lab_id = Lab.objects.get(name=lab_name).id
        except Lab.DoesNotExist:
            pass
    report = build_report(
        title=title, lab_name=lab_name,
        address=address,
        inspector=(args.get('inspector') or user.username),
        detection_ids=[int(x) for x in detection_ids],
        extra_notes=(args.get('extra_notes') or ''),
        user=user,
        lab_id=lab_id,
    )
    payload = ReportDetailSerializer(report).data
    loc = lab_name or address or '未指定'
    evaluation = (payload.get('agent_evaluation') or '')[:300]
    count = payload.get('detection_count', 0)
    summary = (
        f'「{title}」已生成完毕。'
        f'本次报告共纳入 {count} 次隐患识别记录，检查地点为 {loc}。'
        f'{evaluation}'
    )
    return summary, {
        'type': 'report',
        'data': payload,
    }


# ----- analytics_query -----
def _run_analytics(args: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    from apps.analytics import services as a
    from apps.hazards.models import HazardDetection
    metric = args.get('metric', 'overview')
    lab_name = (args.get('lab_name') or '').strip()
    payload: Dict[str, Any]
    if metric == 'overview':
        data = a.overview(lab_name=lab_name)
    elif metric == 'severity':
        data = a.severity_distribution(lab_name=lab_name)
    elif metric == 'category':
        data = a.category_distribution(lab_name=lab_name)
    elif metric == 'trend':
        data = a.detection_trend(lab_name=lab_name)
    elif metric == 'top_labs':
        data = a.top_labs(lab_name=lab_name)
    elif metric == 'lab_overview':
        data = a.lab_overview()
        if lab_name:
            data = [row for row in data if row['lab_name'] == lab_name]
    elif metric == 'recent_detections':
        qs = HazardDetection.objects.all().order_by('-created_at')
        if lab_name:
            qs = qs.filter(lab_name=lab_name)
        data = [
            {
                'id': d.id,
                'lab_name': d.lab_name,
                'overall_severity': d.overall_severity,
                'hazard_count': len(d.hazards or []),
                'created_at': d.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for d in qs[:10]
        ]
    elif metric == 'all':
        data = a.dashboard()
        if lab_name:
            data = {
                'lab_name': lab_name,
                'overview': a.overview(lab_name=lab_name),
                'severity_distribution': a.severity_distribution(lab_name=lab_name),
                'category_distribution': a.category_distribution(lab_name=lab_name),
                'detection_trend': a.detection_trend(lab_name=lab_name),
                'recent_detections': data.get('recent_detections', []),
            }
    else:
        return f'未知 metric: {metric}', _err_payload('未知 metric', 'analytics_query')

    payload = {'type': 'analytics', 'metric': metric, 'lab_name': lab_name or None, 'data': data}
    summary = f'数据查询 ({metric}) 完成,结果如下(JSON 摘要):\n{json.dumps(data, ensure_ascii=False)[:1200]}'
    return summary, payload


# ----- root_cause_analysis -----
def _run_root_cause_analysis(args: Dict[str, Any], user) -> Tuple[str, Dict[str, Any]]:
    from apps.analytics.deep_analysis import analyze_root_cause
    lab_name = (args.get('lab_name') or '').strip() or None
    days = args.get('days', 30)
    result = analyze_root_cause(lab_name=lab_name, days=days)
    summary = result.get('summary', '')
    return summary, result


# ----- risk_prediction -----
def _run_risk_prediction(args: Dict[str, Any], user) -> Tuple[str, Dict[str, Any]]:
    from apps.analytics.deep_analysis import predict_risks
    lab_name = (args.get('lab_name') or '').strip() or None
    days = args.get('days', 30)
    forecast_days = args.get('forecast_days', 30)
    result = predict_risks(lab_name=lab_name, days=days, forecast_days=forecast_days)
    summary = result.get('summary', '')
    return summary, result


# ----- helpers -----
def _err_payload(msg: str, tool: str) -> Dict[str, Any]:
    return {'type': 'error', 'tool': tool, 'message': msg}
