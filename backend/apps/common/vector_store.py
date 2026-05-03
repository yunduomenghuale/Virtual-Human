"""文件型 JSON 向量库。

要求:
* 不引入额外服务(Chroma/FAISS/Milvus 等),向量存储为 JSON 文件;
* 支持 add / search / list / delete;
* 余弦相似度;
* 嵌入函数与本模块解耦,通过构造参数注入。
"""
from __future__ import annotations
import json
import math
import threading
import uuid
from pathlib import Path
from typing import Callable, List, Dict, Any, Optional


class JsonVectorStore:
    """简易 JSON 向量存储。

    存储格式::

        {
          "dim": 512,
          "items": [
              {"id": "...", "text": "...", "metadata": {...}, "vector": [...]}
          ]
        }
    """

    def __init__(self, path: Path | str, embed_fn: Callable[[str], List[float]]):
        self.path = Path(path)
        self.embed_fn = embed_fn
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {'dim': 0, 'items': []}
        self._load()

    # ---------- 持久化 ----------
    def _load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, 'r', encoding='utf-8') as fh:
                    self._data = json.load(fh)
            except Exception:
                self._data = {'dim': 0, 'items': []}
        self._data.setdefault('dim', 0)
        self._data.setdefault('items', [])

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as fh:
            json.dump(self._data, fh, ensure_ascii=False)

    # ---------- 写入 ----------
    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None,
            doc_id: Optional[str] = None) -> str:
        vector = self.embed_fn(text)
        with self._lock:
            if not self._data['dim']:
                self._data['dim'] = len(vector)
            doc_id = doc_id or uuid.uuid4().hex
            self._data['items'].append({
                'id': doc_id,
                'text': text,
                'metadata': metadata or {},
                'vector': vector,
            })
            self._save()
        return doc_id

    def add_many(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        ids: List[str] = []
        metadatas = metadatas or [{} for _ in texts]
        for text, meta in zip(texts, metadatas):
            ids.append(self.add(text, meta))
        return ids

    def delete(self, doc_id: str) -> bool:
        with self._lock:
            before = len(self._data['items'])
            self._data['items'] = [it for it in self._data['items'] if it['id'] != doc_id]
            changed = len(self._data['items']) != before
            if changed:
                self._save()
            return changed

    def delete_by_source(self, source: str) -> int:
        """按 metadata.source 字段删除。"""
        with self._lock:
            before = len(self._data['items'])
            self._data['items'] = [it for it in self._data['items']
                                   if it.get('metadata', {}).get('source') != source]
            removed = before - len(self._data['items'])
            if removed:
                self._save()
            return removed

    def list_sources(self) -> List[Dict[str, Any]]:
        agg: Dict[str, Dict[str, Any]] = {}
        for it in self._data['items']:
            src = it.get('metadata', {}).get('source', '未知')
            if src not in agg:
                agg[src] = {'source': src, 'chunks': 0,
                            'title': it.get('metadata', {}).get('title', src)}
            agg[src]['chunks'] += 1
        return list(agg.values())

    @property
    def size(self) -> int:
        return len(self._data['items'])

    # ---------- 检索 ----------
    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self._data['items']:
            return []
        qv = self.embed_fn(query)
        scored = []
        for it in self._data['items']:
            vec = it.get('vector')
            if not vec or not isinstance(vec, list):
                continue
            scored.append((cosine(qv, vec), it))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                'id': it['id'],
                'text': it['text'],
                'metadata': it['metadata'],
                'score': round(score, 4),
            }
            for score, it in scored[:top_k]
        ]


def cosine(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
