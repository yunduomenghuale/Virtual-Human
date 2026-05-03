"""RAG 服务:文本切分 + 入库 + 检索 + 生成。"""
from __future__ import annotations
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.conf import settings
from django.core.cache import cache

from apps.common.embeddings import embed
from apps.common.llm import get_text_llm
from apps.common.vector_store import JsonVectorStore

from .corpus import CORPUS
from .models import KnowledgeDocument

logger = logging.getLogger(__name__)

_store: Optional[JsonVectorStore] = None


def get_store() -> JsonVectorStore:
    global _store
    if _store is None:
        _store = JsonVectorStore(settings.VECTOR_STORE_PATH, embed_fn=embed)
    return _store


# ---------- chunking ----------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    text = (text or '').strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks: List[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i + chunk_size])
        i += max(1, chunk_size - overlap)
    return chunks


# ---------- ingestion ----------
def ingest_text(source: str, title: str, text: str,
                description: str = '', uploader=None) -> KnowledgeDocument:
    """把一段文本切片并写入向量库 + 元数据表。"""
    store = get_store()
    # 先删旧版本
    store.delete_by_source(source)
    chunks = chunk_text(text)
    metadatas = [
        {'source': source, 'title': title, 'chunk_index': i, 'total': len(chunks)}
        for i in range(len(chunks))
    ]
    store.add_many(chunks, metadatas=metadatas)
    doc, _ = KnowledgeDocument.objects.update_or_create(
        source=source,
        defaults={'title': title, 'description': description,
                  'chunk_count': len(chunks), 'uploader': uploader},
    )
    return doc


def ingest_file(uploaded_file, title: str, description: str = '', uploader=None) -> KnowledgeDocument:
    """支持 .txt / .md / .pdf。"""
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    raw = uploaded_file.read()
    if suffix == '.pdf':
        text = _extract_pdf_text(raw)
    else:
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = raw.decode('gbk', errors='ignore')
    source = f'upload::{name}'
    doc = ingest_text(source, title or name, text, description=description, uploader=uploader)
    # 把文件本身保存到 FileField
    uploaded_file.seek(0)
    doc.file.save(name, uploaded_file, save=True)
    return doc


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(raw))
        return '\n'.join((page.extract_text() or '') for page in reader.pages)
    except Exception as exc:  # noqa: BLE001
        logger.warning('PDF 解析失败: %s', exc)
        return ''


def ingest_default_corpus() -> int:
    """把内置语料写入向量库。返回新增条数。"""
    n = 0
    for source, title, body in CORPUS:
        ingest_text(source, title, body, description='内置示例语料')
        n += 1
    return n


# ---------- retrieval + answer ----------
def retrieve(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    return get_store().search(query, top_k=top_k)


SYSTEM_PROMPT = (
    '你是「实验室消防安全数字人助理」。请严格基于检索到的资料回答用户问题,'
    '不得编造未在资料中提及的内容。如资料不足以回答,请明确说明并建议用户补充资料。'
    '直接给出回答即可,不需要列出参考依据或来源文档。'
)


def _build_qa_prompt(query: str, top_k: int = 4) -> tuple[str, list[dict]]:
    """构建问答 prompt,返回 (user_prompt, chunks)。"""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        context = '(知识库为空)'
    else:
        context = '\n\n'.join(
            f"[{i+1}] {c['metadata'].get('title', '')}\n{c['text']}"
            for i, c in enumerate(chunks)
        )
    user_prompt = f'## 用户问题\n{query}\n\n## 检索到的资料\n{context}\n\n请基于以上资料回答。'
    return user_prompt, chunks


def answer_question(query: str, top_k: int = 4) -> Dict[str, Any]:
    cache_key = f'kq:{hashlib.md5(query.strip().lower().encode()).hexdigest()}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    user_prompt, chunks = _build_qa_prompt(query, top_k)
    llm = get_text_llm()
    answer = llm.chat([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_prompt},
    ], temperature=0.2, max_tokens=900)
    result = {
        'answer': answer,
        'sources': [
            {
                'title': c['metadata'].get('title', ''),
                'snippet': c['text'][:160],
                'score': c['score'],
            }
            for c in chunks
        ],
    }
    cache.set(cache_key, result, timeout=3600)
    return result


def answer_question_stream(query: str, top_k: int = 4):
    """流式回答,先 yield sources JSON,然后逐 token yield 答案。"""
    user_prompt, chunks = _build_qa_prompt(query, top_k)
    # 先发送 sources 元数据
    import json
    yield json.dumps({
        'type': 'sources',
        'sources': [
            {'title': c['metadata'].get('title', ''), 'snippet': c['text'][:160], 'score': c['score']}
            for c in chunks
        ],
    }, ensure_ascii=False) + '\n'

    llm = get_text_llm()
    for token in llm.chat_stream([
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_prompt},
    ], temperature=0.2, max_tokens=900):
        yield json.dumps({'type': 'token', 'text': token}, ensure_ascii=False) + '\n'


def list_documents() -> List[Dict[str, Any]]:
    return [
        {
            'id': doc.id,
            'title': doc.title,
            'source': doc.source,
            'description': doc.description,
            'chunk_count': doc.chunk_count,
            'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'uploader': doc.uploader.username if doc.uploader else '',
        }
        for doc in KnowledgeDocument.objects.all()
    ]


def delete_document(doc: KnowledgeDocument) -> None:
    get_store().delete_by_source(doc.source)
    if doc.file:
        try:
            doc.file.delete(save=False)
        except Exception:
            pass
    doc.delete()
