"""PDF 渲染。使用 reportlab,自动注册中文字体。"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any

import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)


CN_FONT_CANDIDATES = [
    ('MSYH', 'C:/Windows/Fonts/msyh.ttc'),
    ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
    ('SimSun', 'C:/Windows/Fonts/simsun.ttc'),
]
CN_FONT_NAME = 'Helvetica'


def _ensure_cn_font() -> str:
    global CN_FONT_NAME
    if CN_FONT_NAME != 'Helvetica':
        return CN_FONT_NAME
    for name, path in CN_FONT_CANDIDATES:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                CN_FONT_NAME = name
                return name
            except Exception:
                continue
    return CN_FONT_NAME


def _styles() -> Dict[str, ParagraphStyle]:
    font = _ensure_cn_font()
    base = getSampleStyleSheet()
    title = ParagraphStyle('zh-title', parent=base['Title'], fontName=font,
                           fontSize=20, leading=26, alignment=1, spaceAfter=14)
    h2 = ParagraphStyle('zh-h2', parent=base['Heading2'], fontName=font,
                        fontSize=14, leading=20, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle('zh-body', parent=base['BodyText'], fontName=font,
                          fontSize=10.5, leading=16)
    small = ParagraphStyle('zh-small', parent=body, fontSize=9, leading=13)
    return {'title': title, 'h2': h2, 'body': body, 'small': small, 'font': font}


SEVERITY_LABEL = {'low': '低', 'medium': '中', 'high': '高'}
SEVERITY_COLOR = {
    'low': colors.HexColor('#3da35d'),
    'medium': colors.HexColor('#ff8c00'),
    'high': colors.HexColor('#d62828'),
}


def _escape_xml(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _md_to_pdf_flowables(text: str, styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """把 markdown 简单语法转成 reportlab Paragraph 列表。"""
    flowables: List[Any] = []
    blocks = text.split('\n\n')
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # 整段被 ** 包裹 → 加粗标题段落
        m = re.match(r'\*\*(.+?)\*\*$', block, re.S)
        if m:
            title = _escape_xml(m.group(1))
            p = Paragraph(f'<b>{title}</b>', styles['body'])
            flowables.append(p)
            continue
        # 普通段落：转义 XML → 替换 markdown 标记 → 换行变 <br/>
        lines = block.split('\n')
        processed_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            line = _escape_xml(line)
            # **bold**
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            # *italic* (但不匹配 ** 已处理的)
            line = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', line)
            processed_lines.append(line)
        html = '<br/>'.join(processed_lines)
        flowables.append(Paragraph(html, styles['body']))
    return flowables


def render_pdf(report, detections: List[Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    font = styles['font']
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    flow: List[Any] = []
    flow.append(Paragraph(report.title, styles['title']))

    # 1. 基本信息
    flow.append(Paragraph('一、基本信息', styles['h2']))
    if report.lab_name:
        info_rows = [
            ['实验室', report.lab_name, '检查人', report.inspector or '-'],
            ['总体风险', SEVERITY_LABEL.get(report.overall_severity, '中'),
             '生成时间', report.created_at.strftime('%Y-%m-%d %H:%M')],
            ['创建人', report.created_by.username if report.created_by_id else '-',
             '隐患记录数', str(len(detections))],
        ]
    elif report.address:
        info_rows = [
            ['地址', report.address, '检查人', report.inspector or '-'],
            ['总体风险', SEVERITY_LABEL.get(report.overall_severity, '中'),
             '生成时间', report.created_at.strftime('%Y-%m-%d %H:%M')],
            ['创建人', report.created_by.username if report.created_by_id else '-',
             '隐患图片数', str(len(detections))],
        ]
    else:
        info_rows = [
            ['检查人', report.inspector or '-', '生成时间',
             report.created_at.strftime('%Y-%m-%d %H:%M')],
            ['创建人', report.created_by.username if report.created_by_id else '-',
             '隐患图片数', str(len(detections))],
        ]
    t = Table(info_rows, colWidths=[2.4 * cm, 5.6 * cm, 2.4 * cm, 5.6 * cm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4ff')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f4ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    flow.append(t)

    # 2. 汇总统计
    flow.append(Paragraph('二、汇总统计', styles['h2']))
    stats = report.summary_stats or {}
    by_sev = stats.get('by_severity', {}) or {}
    by_cat = stats.get('by_category', {}) or {}
    sev_rows = [['等级', '数量']]
    for k in ('high', 'medium', 'low'):
        sev_rows.append([SEVERITY_LABEL[k], str(by_sev.get(k, 0))])
    sev_rows.append(['合计', str(stats.get('total', 0))])
    cat_rows = [['类别', '数量']] + [[k, str(v)] for k, v in by_cat.items()]
    sev_table = Table(sev_rows, colWidths=[3 * cm, 2 * cm])
    sev_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f4ff')),
    ]))
    cat_table = Table(cat_rows, colWidths=[3.5 * cm, 2 * cm])
    cat_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f4ff')),
    ]))
    flow.append(Table([[sev_table, cat_table]], colWidths=[6 * cm, 7 * cm]))

    # 3. 隐患明细 + 图片快照
    flow.append(Paragraph('三、隐患明细', styles['h2']))
    idx = 0
    for det in detections:
        idx += 1
        flow.append(Paragraph(f'{idx}. {det.lab_name or "现场图片"}({det.created_at.strftime("%Y-%m-%d %H:%M")})',
                              styles['body']))
        if getattr(det, 'media_type', 'image') == 'video':
            flow.append(Paragraph(f'[视频文件] {Path(det.original_image.name).name}', styles['small']))
        else:
            img_path = det.annotated_image.path if det.annotated_image else det.original_image.path
            try:
                img = Image(img_path, width=14 * cm, height=10.5 * cm, kind='proportional')
                flow.append(img)
            except Exception:
                flow.append(Paragraph('[图片加载失败]', styles['small']))
        flow.append(Spacer(1, 4))
        flow.append(Paragraph(f'整体评估:{det.summary or "-"}', styles['small']))
        # 隐患明细表
        if det.hazards:
            rows = [['#', '隐患', '类别', '风险', '描述', '建议']]
            for j, h in enumerate(det.hazards, start=1):
                rows.append([
                    str(j),
                    Paragraph(h.get('name', ''), styles['small']),
                    Paragraph(h.get('category', ''), styles['small']),
                    SEVERITY_LABEL.get(h.get('severity', 'medium'), '中'),
                    Paragraph(h.get('description', ''), styles['small']),
                    Paragraph(h.get('suggestion', ''), styles['small']),
                ])
            # 页面可用宽度 ≈ 17cm (A4 21cm - 左右边距 4cm)
            tb = Table(rows, colWidths=[0.6 * cm, 2 * cm, 1.2 * cm, 1 * cm, 6.1 * cm, 6.1 * cm],
                       repeatRows=1)
            tb.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eef8')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            flow.append(tb)
        flow.append(Spacer(1, 12))

    # 4. 参考依据
    if report.references:
        flow.append(Paragraph('四、参考依据', styles['h2']))
        for ref in report.references:
            flow.append(Paragraph(f'• <b>{ref.get("title", "")}</b>:{ref.get("snippet", "")}',
                                  styles['small']))

    # 5. agent 评价
    flow.append(Paragraph('五、AI 评价与整改建议', styles['h2']))
    for para in _md_to_pdf_flowables(report.agent_evaluation or '(未生成)', styles):
        flow.append(para)

    if report.extra_notes:
        flow.append(Paragraph('六、备注', styles['h2']))
        flow.append(Paragraph(report.extra_notes, styles['body']))

    doc.build(flow)
    return output_path
