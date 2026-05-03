"""嵌入函数:优先使用本地模型,加载失败时回退到远程 API(阿里云/DashScope/OpenAI 兼容),mock 兜底。"""
from __future__ import annotations
import hashlib
import logging
import math
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)
_model = None
_dim = 384
_emb_client = None


def _get_emb_client():
    """初始化 OpenAI 兼容的嵌入客户端(阿里云 DashScope 等)——仅作为回退。"""
    global _emb_client
    if _emb_client is not None:
        return _emb_client
    api_key = getattr(settings, 'EMBEDDING_API_KEY', '') or getattr(settings, 'TEXT_LLM_API_KEY', '')
    base_url = getattr(settings, 'EMBEDDING_BASE_URL', '') or getattr(settings, 'TEXT_LLM_BASE_URL', '')
    if not api_key:
        return None
    try:
        from openai import OpenAI
        _emb_client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info('已初始化远程嵌入客户端(回备用): %s', base_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning('初始化远程嵌入客户端失败 (%s)', exc)
        _emb_client = False
    return _emb_client


def _try_load_model():
    global _model, _dim
    if settings.USE_MOCK_EMBEDDING:
        return None
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        local_model = getattr(settings, 'EMBEDDING_LOCAL_MODEL', 'BAAI/bge-small-zh-v1.5')
        _model = SentenceTransformer(local_model)
        # sentence-transformers 3.x 起改名为 get_embedding_dimension,旧版仍提供 alias
        get_dim = (getattr(_model, 'get_embedding_dimension', None)
                   or getattr(_model, 'get_sentence_embedding_dimension', None))
        _dim = (get_dim() if callable(get_dim) else None) or 384
        logger.info('已加载本地嵌入模型: %s (dim=%s)', local_model, _dim)
    except Exception as exc:  # noqa: BLE001
        logger.warning('加载本地嵌入模型失败 (%s),将回退到远程 API 或 mock', exc)
        _model = False  # 标记尝试过
    return _model


def embed(text: str) -> List[float]:
    # 1) 优先使用本地模型(速度最快)
    model = _try_load_model()
    if model and model is not False:
        try:
            vec = model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        except Exception as exc:  # noqa: BLE001
            logger.warning('本地模型编码失败 (%s),回退到远程 API', exc)

    # 2) 远程 API 回退
    client = _get_emb_client()
    if client and client is not False:
        try:
            resp = client.embeddings.create(
                model=getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-v3'),
                input=text,
                encoding_format='float',
            )
            return resp.data[0].embedding
        except Exception as exc:  # noqa: BLE001
            logger.warning('远程嵌入 API 调用失败 (%s),降级到 mock 嵌入', exc)

    # 3) mock 兜底
    return _mock_embed(text)


def _mock_embed(text: str, dim: int = 384) -> List[float]:
    """基于多个 md5 切片产生稳定的伪向量。"""
    text = (text or '').strip().lower()
    out: List[float] = []
    seed = 0
    while len(out) < dim:
        h = hashlib.md5(f'{seed}::{text}'.encode('utf-8')).digest()
        for byte in h:
            out.append((byte - 128) / 128.0)
            if len(out) >= dim:
                break
        seed += 1
    # L2 normalize
    norm = math.sqrt(sum(x * x for x in out)) or 1.0
    return [x / norm for x in out]
