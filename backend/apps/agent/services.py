"""Agent 主循环:LLM tool-calling 调度。

流程:
  1) 把用户消息 + 系统提示词送入 TextLLM(附带 tools)
  2) 若返回 tool_calls,逐个执行(权限校验 + 业务调用),把工具输出
     作为 tool message 追加到上下文,继续推理
  3) 直到模型返回最终 content(无 tool_calls),或达到迭代上限
"""
from __future__ import annotations
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from apps.common.llm import get_text_llm

from apps.skill_permissions.models import SkillCode
from apps.skill_permissions.services import is_skill_enabled
from .tools import (TOOL_DEFS, execute_tool,
                    filter_tools_for_user, list_skill_codes_for_user)

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5


SYSTEM_PROMPT_TMPL = (
    '你是「小安」,智安平台的 AI 助手,具备以下 5 项 skill,通过 tool-calling 调度:\n'
    '  - knowledge_qa: 检索消防安全知识库回答规范性问题\n'
    '  - hazard_detect: 对用户上传的现场图片识别隐患(需有图片)\n'
    '  - report_gen: 为某实验室生成 PDF / Word 安全检查报告\n'
    '  - analytics_query: 查询系统数据指标 / 实验室排行 / 最近隐患记录\n'
    '  - scenario_training: 当用户要求进行消防培训、出题、演练或者分析事故场景时调用\n'
    '\n'
    '当前用户:{username}({role}),启用的 skill:{enabled_skills}。\n'
    '本轮用户附件:{attachment_state}。\n'
    '\n'
    '工作原则:\n'
    '1. 当问题明显属于上述某项 skill 时,必须立即调用对应工具,禁止直接输出操作说明或占位符。\n'
    '2. 用户上传图片时,直接调用 hazard_detect。\n'
    '3. 用户要求"生成报告"时,直接调用 report_gen,禁止输出"我将为您生成..."等描述。\n'
    '4. scenario_training 场景演练流程：\n'
    '   a) 用户首次要求培训/演练且未指定具体场景时，先调用 scenario_training(mode="list")，工具返回所有可选场景列表卡片，用户点击选择后自动发送选择消息。\n'
    '   b) 用户选择具体场景后，调用 scenario_training(mode="teaching") 进行教学讲解。\n'
    '   c) 用户要求测试时，调用 scenario_training(mode="testing")，工具返回场景描述，你向用户描述事故并提问。\n'
    '   d) 用户回答后，再次调用 scenario_training(mode="testing", answer="用户回答")，工具返回评分结果，你直接展示给用户。\n'
    '   e) 你的回复中禁止出现"任务指示"、"教学讲义内容"等元话语，直接输出讲解内容或评分结果即可。\n'
    '5. 工具结果会以结构化卡片形式呈现给用户;你只需用 1-2 句话点出要点 / 提示 / '
    '建议,不要冗长复述工具数据。\n'
    '6. 数据分析(analytics_query)的结果禁止罗列数字,必须给出"结论+建议":\n'
    '   - 点出最高风险项(哪个实验室/哪类隐患最严重)\n'
    '   - 指出变化趋势(上升/下降/持平,与平均水平的差距)\n'
    '   - 给出可执行建议("建议本周复查XX实验室"、"建议关注电气安全")\n'
    '   - 最多 2 句话,禁止输出 JSON 或表格\n'
    '   - 当用户提到具体实验室名称时,必须在 analytics_query 中传入 lab_name 参数,禁止返回全局数据\n'
    '7. 严禁在回复中输出 /media/ 路径的 markdown 下载链接,前端会自动展示下载按钮。\n'
    '8. 严禁以 JSON、markdown 代码块或文本形式输出工具参数,必须通过正式的 tool-calling 机制调用。\n'
    '9. 若用户问题与消防安全无关,礼貌引导回主题。\n'
    '10. 中文回答,语气专业、简洁。\n'
    '11. 最重要:不要描述你要做什么,直接调用工具。禁止输出"我将为您调用..."等任何说明性文字。\n'
)


def _extract_report_args(text: str) -> Optional[Dict[str, str]]:
    """从用户消息中提取 report_gen 参数。返回 {'title': ..., 'lab_name': ...} 或 None。"""
    t = text.strip()
    if not re.search(r'(生成|制作).{0,30}报告', t):
        return None
    # 去掉常见前缀
    cleaned = re.sub(r'^(帮我|请|帮我一下|请帮我|请帮我一下|给我|给我一份)', '', t).strip()
    # 匹配 "生成 ... 的 ... 报告" 或 "生成 ... 报告"
    m = re.search(r'(?:生成|制作)(?:了|一下|一个|一份)?\s*(.+?)\s*(?:的)?\s*(?:安全)?(?:检查)?报告', cleaned)
    if m:
        lab_name = m.group(1).strip()
        if lab_name:
            return {'title': f'{lab_name}安全检查报告', 'lab_name': lab_name}
    return None


def _extract_scenario_args(text: str) -> Optional[Dict[str, str]]:
    """从用户消息中提取 scenario_training 参数。返回 {'mode': ...} 或 None。"""
    t = text.strip()
    # 1. 如果用户已经明确选择了具体场景（如"我要学习「XXX」"），直接走 teaching
    selected_m = re.search(r'(我要学习|选择|学习)[\s「【]*([\u4e00-\u9fa5]{2,20})', t)
    if selected_m:
        return {'mode': 'teaching', 'topic': selected_m.group(2).strip()}
    # 2. 必须包含明确意图词
    if not re.search(r'(消防培训|场景演练|案例测试|实战演练|消防演练|消防知识学习|出题|考考我|来一题)', t):
        return None
    # 判断模式
    if re.search(r'(测试|演练|演习|做题|答题|考考我|来一题|实战)', t):
        mode = 'testing'
    else:
        mode = 'teaching'
    # 判断难度
    difficulty = ''
    if re.search(r'(简单|低难度|初级)', t):
        difficulty = 'low'
    elif re.search(r'(困难|高难度|高级)', t):
        difficulty = 'high'
    elif re.search(r'(中等|中难度|中级)', t):
        difficulty = 'medium'
    # 尝试提取主题
    topic = ''
    # 匹配 "XX 场景" / "XX 演练" / "关于 XX" 等
    m = re.search(r'(?:关于|来个|来一道|来一题|讲解|演练|培训)\s*([\u4e00-\u9fa5]{2,10})(?:场景|演练|培训|案例|火灾|起火|事故)', t)
    if m:
        topic = m.group(1).strip()
    # 如果没有指定具体场景/主题，先列出场景列表让用户选择
    if not topic:
        return {'mode': 'list'}
    args: Dict[str, str] = {'mode': mode}
    if difficulty:
        args['difficulty'] = difficulty
    if topic:
        args['topic'] = topic
    return args


def _system_prompt(user, has_attachment: bool) -> str:
    return SYSTEM_PROMPT_TMPL.format(
        username=user.username,
        role=user.role,
        enabled_skills=','.join(list_skill_codes_for_user(user)) or '无',
        attachment_state='已上传 1 张图片' if has_attachment else '无',
    )


def _try_parse_tool_calls_from_content(text: str) -> List[Dict[str, Any]]:
    """后备解析:从 LLM 文本回复中提取工具调用(qwen 兼容模式常把 tool call 写成文本)。"""
    tool_names = {t['function']['name'] for t in TOOL_DEFS}
    found: List[Dict[str, Any]] = []
    found_ids: set = set()  # 避免同一位置重复匹配

    # 先去掉 markdown 代码块标记,保留内部内容
    cleaned = re.sub(r'```(?:json|python)?\s*', '', text)
    cleaned = cleaned.replace('```', '')

    # 模式 A: 工具名 + 换行 + JSON 对象 (最常见)
    pattern_a = re.compile(
        r'(' + '|'.join(re.escape(n) for n in tool_names) + r')'
        r'\s*\n?\s*({[\s\S]*?})',
        re.S,
    )
    for m in pattern_a.finditer(cleaned):
        if m.start() in found_ids:
            continue
        name = m.group(1)
        raw_json = m.group(2)
        try:
            args = json.loads(raw_json)
        except Exception:
            continue
        found_ids.add(m.start())
        found.append({
            'id': f'extracted_{len(found)}',
            'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)},
        })

    # 模式 B: 工具名({...}) — JSON 包在圆括号里
    pattern_b = re.compile(
        r'(' + '|'.join(re.escape(n) for n in tool_names) + r')'
        r'\s*\(\s*({[\s\S]*?})\s*\)',
        re.S,
    )
    for m in pattern_b.finditer(cleaned):
        if m.start() in found_ids:
            continue
        name = m.group(1)
        raw_json = m.group(2)
        try:
            args = json.loads(raw_json)
        except Exception:
            continue
        found_ids.add(m.start())
        found.append({
            'id': f'extracted_{len(found)}',
            'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)},
        })

    # 模式 C: 工具名(key="value", ...) — Python 风格关键字参数
    pattern_c = re.compile(
        r'(' + '|'.join(re.escape(n) for n in tool_names) + r')'
        r'\s*\(\s*([^)]*)\s*\)',
        re.S,
    )
    for m in pattern_c.finditer(cleaned):
        if m.start() in found_ids:
            continue
        name = m.group(1)
        kwargs_str = m.group(2).strip()
        if not kwargs_str:
            continue
        # 排除已经匹配过的 JSON 形式 (包含 { )
        if '{' in kwargs_str:
            continue
        args: Dict[str, Any] = {}
        # 匹配 key="value" 或 key='value' 或 key=value
        kv_pattern = re.compile(r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|([^,\s]+))")
        for kv in kv_pattern.finditer(kwargs_str):
            k = kv.group(1)
            v = kv.group(2) or kv.group(3) or kv.group(4)
            args[k] = v.strip() if v else ''
        if not args:
            continue
        found_ids.add(m.start())
        found.append({
            'id': f'extracted_{len(found)}',
            'type': 'function',
            'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)},
        })

    return found


def _try_extract_tool_intent(text: str, user_query: str) -> List[Dict[str, Any]]:
    """最终兜底:从文本中检测工具意图,构造合成 tool_call。

    当 LLM 输出"我将为您调用知识库..."等描述性文字、但又没有给出可解析的参数时,
    根据提到的工具名 + 原始用户问题,直接构造一次工具调用。
    """
    tool_names = {t['function']['name'] for t in TOOL_DEFS}
    found: List[Dict[str, Any]] = []
    lowered = text.lower()

    # knowledge_qa: 提到知识库 / 检索 / 查询 / 知识问答
    if 'knowledge_qa' in lowered or '知识库' in lowered or '检索' in lowered:
        # 尝试从文本中捞出引号内的内容作为 query
        m = re.search(r'[\"\']([^\"\']+)[\"\']', text)
        query = m.group(1).strip() if m else user_query.strip()
        if query:
            found.append({
                'id': f'intent_{len(found)}',
                'type': 'function',
                'function': {
                    'name': 'knowledge_qa',
                    'arguments': json.dumps({'query': query}, ensure_ascii=False),
                },
            })

    # hazard_detect: 提到图片 / 识别隐患 / 检测
    if 'hazard_detect' in lowered or ('图片' in lowered and '隐患' in lowered):
        found.append({
            'id': f'intent_{len(found)}',
            'type': 'function',
            'function': {'name': 'hazard_detect', 'arguments': '{}'},
        })

    # report_gen: 提到生成报告
    if 'report_gen' in lowered or '生成报告' in lowered:
        # 尝试复用已有的正则提取参数
        args = _extract_report_args(user_query) or {'title': '安全检查报告'}
        found.append({
            'id': f'intent_{len(found)}',
            'type': 'function',
            'function': {
                'name': 'report_gen',
                'arguments': json.dumps(args, ensure_ascii=False),
            },
        })

    # analytics_query: 提到数据 / 统计 / 查询
    if 'analytics_query' in lowered or '数据' in lowered or '统计' in lowered:
        found.append({
            'id': f'intent_{len(found)}',
            'type': 'function',
            'function': {
                'name': 'analytics_query',
                'arguments': json.dumps({'metric': 'all'}, ensure_ascii=False),
            },
        })

    # scenario_training: 仅检测明确的工具名，避免 LLM 回复中的"演练"等字样误触发
    # 用户的明确请求已通过 _extract_scenario_args 硬规则短路处理
    if 'scenario_training' in lowered:
        found.append({
            'id': f'intent_{len(found)}',
            'type': 'function',
            'function': {
                'name': 'scenario_training',
                'arguments': json.dumps({'mode': 'teaching'}, ensure_ascii=False),
            },
        })

    return found


def _tool_name(tc) -> str:
    func = getattr(tc, 'function', None) or {}
    return getattr(func, 'name', 'unknown')


def _serialize_assistant_msg(msg) -> Dict[str, Any]:
    """把 LLM 返回的 assistant message 序列化成下一轮可发送的 dict 形态。"""
    out: Dict[str, Any] = {'role': 'assistant', 'content': getattr(msg, 'content', None) or ''}
    tcs = getattr(msg, 'tool_calls', None)
    if tcs:
        out['tool_calls'] = []
        for tc in tcs:
            func = getattr(tc, 'function', None)
            if func is None:
                continue
            out['tool_calls'].append({
                'id': getattr(tc, 'id', 'unknown'),
                'type': 'function',
                'function': {
                    'name': getattr(func, 'name', 'unknown'),
                    'arguments': getattr(func, 'arguments', '{}') or '{}',
                },
            })
    return out


def chat(*, user, messages: List[Dict[str, Any]],
         attachment=None) -> Dict[str, Any]:
    """运行一次 agent 对话。

    :param user: 当前登录用户(用于 RBAC + 业务记录归属)
    :param messages: [{'role': 'user'|'assistant', 'content': str}, ...]
    :param attachment: 可选的 InMemoryUploadedFile / TemporaryUploadedFile,
                       hazard_detect 工具会消费该附件
    :return: {
        'message': str,                # 最终 assistant 文本
        'tool_calls': [...],           # 工具调用日志(供前端渲染卡片)
        'enabled_skills': [...],       # 当前用户的可用 skill
    }
    """
    has_attachment = attachment is not None

    # 硬规则:有附件直接隐患识别,跳过 LLM 决策轮次(更快且避免 LLM 不调用工具)
    if has_attachment and is_skill_enabled(user.role, SkillCode.HAZARD_DETECT):
        summary, payload = execute_tool(
            name='hazard_detect', args={}, user=user, attachment=attachment,
        )
        return {
            'message': payload.get('user_summary', summary) if payload.get('type') == 'hazard_detection' else summary,
            'tool_calls': [{
                'name': 'hazard_detect',
                'args': {},
                'skill': 'hazard_detect',
                'ok': payload.get('type') != 'error',
                'result': payload,
            }],
            'enabled_skills': list_skill_codes_for_user(user),
        }

    # 硬规则:检测到"生成报告"关键词直接调用 report_gen,跳过 LLM 决策
    if is_skill_enabled(user.role, SkillCode.REPORT_GEN):
        last_user_msg = next((m for m in reversed(messages or []) if m.get('role') == 'user'), None)
        if last_user_msg:
            report_args = _extract_report_args(last_user_msg.get('content', ''))
            if report_args:
                summary, payload = execute_tool(
                    name='report_gen', args=report_args, user=user, attachment=None,
                )
                return {
                    'message': summary,
                    'tool_calls': [{
                        'name': 'report_gen',
                        'args': report_args,
                        'skill': 'report_gen',
                        'ok': payload.get('type') != 'error',
                        'result': payload,
                    }],
                    'enabled_skills': list_skill_codes_for_user(user),
                }

    # 硬规则:检测到消防培训/场景演练关键词直接调用 scenario_training,跳过 LLM 决策
    if is_skill_enabled(user.role, SkillCode.SCENARIO_TRAINING):
        last_user_msg = next((m for m in reversed(messages or []) if m.get('role') == 'user'), None)
        if last_user_msg:
            scenario_args = _extract_scenario_args(last_user_msg.get('content', ''))
            if scenario_args:
                summary, payload = execute_tool(
                    name='scenario_training', args=scenario_args, user=user, attachment=None,
                )
                return {
                    'message': summary,
                    'tool_calls': [{
                        'name': 'scenario_training',
                        'args': scenario_args,
                        'skill': 'scenario_training',
                        'ok': payload.get('type') != 'error',
                        'result': payload,
                    }],
                    'enabled_skills': list_skill_codes_for_user(user),
                }

    sys_prompt = _system_prompt(user, has_attachment)
    full_messages: List[Dict[str, Any]] = [
        {'role': 'system', 'content': sys_prompt},
    ]
    full_messages.extend(messages or [])
    if has_attachment:
        # 显式提示模型本轮附件存在(并非要它自己读 URL,只是触发 tool 调度)
        full_messages.append({
            'role': 'system',
            'content': '【附件提示】用户在本轮上传了一张图片。如其与消防安全相关,'
                       '请调用 hazard_detect。该图片只在本轮可用。',
        })

    tools = filter_tools_for_user(user, has_attachment)
    llm = get_text_llm()
    tool_log: List[Dict[str, Any]] = []
    attachment_consumed = False

    final_text = ''
    single_knowledge_qa = False  # 标记是否为单一知识问答短路
    for it in range(MAX_ITERATIONS):
        logger.info('Agent 第 %d 轮,可用工具:%s', it + 1, [t['function']['name'] for t in tools])
        if tools:
            msg = llm.chat_with_tools(full_messages, tools)
        else:
            # 没有任何可用工具,退化为纯文本对话,优先使用快速模型
            fast_model = getattr(settings, 'FAST_LLM_MODEL', None) or None
            text = llm.chat(full_messages, temperature=0.3, max_tokens=1200, model=fast_model)

            class _Plain:
                pass
            msg = _Plain()
            msg.content = text
            msg.tool_calls = None

        tool_calls = getattr(msg, 'tool_calls', None) or []
        extracted: List[Dict[str, Any]] = []
        # 后备解析:qwen 有时会把 tool call 直接输出到 content 中
        if not tool_calls:
            content = getattr(msg, 'content', None) or ''
            extracted = _try_parse_tool_calls_from_content(content)
            if extracted:
                logger.info('Agent 第 %d 轮,从 content 中提取到 %d 个 tool_calls', it + 1, len(extracted))
                class _FakeFunc:
                    def __init__(self, data):
                        self.name = data['name']
                        self.arguments = data['arguments']
                class _FakeTC:
                    def __init__(self, data):
                        self.id = data['id']
                        self.type = data['type']
                        self.function = _FakeFunc(data['function'])
                tool_calls = [_FakeTC(d) for d in extracted]
                msg.content = ''
        # 最终兜底:若 LLM 仍输出描述性文字且未触发 tool-calling,检测意图并强制构造 tool_call
        if not tool_calls and not extracted:
            content = getattr(msg, 'content', None) or ''
            last_user_msg = next((m for m in reversed(messages or []) if m.get('role') == 'user'), None)
            user_query = last_user_msg.get('content', '') if last_user_msg else ''
            intent_calls = _try_extract_tool_intent(content, user_query)
            if intent_calls:
                logger.info('Agent 第 %d 轮,从意图中构造 %d 个 tool_calls', it + 1, len(intent_calls))
                class _FakeFunc:
                    def __init__(self, data):
                        self.name = data['name']
                        self.arguments = data['arguments']
                class _FakeTC:
                    def __init__(self, data):
                        self.id = data['id']
                        self.type = data['type']
                        self.function = _FakeFunc(data['function'])
                tool_calls = [_FakeTC(d) for d in intent_calls]
                msg.content = ''

        logger.info('Agent 第 %d 轮,返回 tool_calls 数:%d', it + 1, len(tool_calls))
        if not tool_calls:
            final_text = getattr(msg, 'content', None) or ''
            break

        # 短路优化:单一知识问答、隐患识别或场景演练直接返回结果,不再走第二轮 LLM
        if len(tool_calls) == 1:
            func = getattr(tool_calls[0], 'function', None) or {}
            name = getattr(func, 'name', '')
            if name in ('knowledge_qa', 'hazard_detect', 'scenario_training'):
                single_knowledge_qa = True

        # 把模型这一轮的 tool 调用追加进上下文
        full_messages.append(_serialize_assistant_msg(msg))

        # 并行执行 tool:先串行处理 hazard_detect(消耗附件),其余并行
        def _exec_tool(tc_item) -> Tuple[Any, str, Dict[str, Any], str, Dict[str, Any]]:
            func = getattr(tc_item, 'function', None) or {}
            raw_args = getattr(func, 'arguments', '{}') or '{}'
            try:
                a = json.loads(raw_args)
            except Exception:
                a = {}
            name = getattr(func, 'name', 'unknown')
            # 兜底: knowledge_qa 若 LLM 没传 query,用最后一条用户消息补全
            if name == 'knowledge_qa' and not a.get('query'):
                last_user_msg = next(
                    (m for m in reversed(messages or []) if m.get('role') == 'user'), None
                )
                if last_user_msg:
                    a['query'] = last_user_msg.get('content', '')
            logger.info('Agent 执行工具:%s, args:%s', name, a)
            att = None if attachment_consumed else attachment
            s, p = execute_tool(name=name, args=a, user=user, attachment=att)
            return tc_item, name, a, s, p

        hazard_tcs = [tc for tc in tool_calls if _tool_name(tc) == 'hazard_detect']
        other_tcs = [tc for tc in tool_calls if _tool_name(tc) != 'hazard_detect']
        exec_results = []

        # hazard_detect 串行(可能消耗 attachment)
        for tc in hazard_tcs:
            tc_item, name, a, s, p = _exec_tool(tc)
            if name == 'hazard_detect' and not attachment_consumed:
                attachment_consumed = True
            exec_results.append((tc_item, name, a, s, p))

        # 其余并行
        if len(other_tcs) > 1:
            with ThreadPoolExecutor(max_workers=len(other_tcs)) as executor:
                futures = {executor.submit(_exec_tool, tc): tc for tc in other_tcs}
                for future in futures:
                    exec_results.append(future.result())
        else:
            for tc in other_tcs:
                exec_results.append(_exec_tool(tc))

        # 按原始 tool_calls 顺序追加结果到上下文
        tc_order = {id(tc): i for i, tc in enumerate(tool_calls)}
        exec_results.sort(key=lambda r: tc_order.get(id(r[0]), 0))

        for tc_item, name, a, s, p in exec_results:
            tool_log.append({
                'name': name,
                'args': a,
                'skill': name,
                'ok': p.get('type') != 'error',
                'result': p,
            })

            # knowledge_qa / hazard_detect / scenario_training 短路:直接把答案作为最终输出
            if single_knowledge_qa and name in ('knowledge_qa', 'hazard_detect', 'scenario_training'):
                if name == 'hazard_detect':
                    final_text = p.get('user_summary', s)
                else:
                    final_text = s
                break

            full_messages.append({
                'role': 'tool',
                'tool_call_id': getattr(tc_item, 'id', 'unknown'),
                'content': s,
            })

        # 如果已短路,跳出迭代
        if single_knowledge_qa:
            break
    else:
        final_text = final_text or '(已达到最大调用轮次,本次未给出最终回答。)'

    return {
        'message': final_text,
        'tool_calls': tool_log,
        'enabled_skills': list_skill_codes_for_user(user),
    }
