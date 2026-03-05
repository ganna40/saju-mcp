"""명리학 지식 검색기 — numpy 코사인 유사도 벡터 검색."""
from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np

DEFAULT_DB_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_db")
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
INDEX_FILE = "index.pkl"

# 싱글톤 캐싱
_index_data = None
_model = None


def _load_index(db_dir: str = DEFAULT_DB_DIR) -> dict | None:
    """인덱스 로드 (싱글톤 캐싱)."""
    global _index_data

    if _index_data is not None:
        return _index_data

    index_path = os.path.join(db_dir, INDEX_FILE)
    if not os.path.exists(index_path):
        return None

    with open(index_path, "rb") as f:
        _index_data = pickle.load(f)

    return _index_data


def _get_model():
    """임베딩 모델 로드 (싱글톤)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _encode_query(query: str) -> np.ndarray:
    """쿼리를 벡터로 인코딩."""
    model = _get_model()
    vec = model.encode([query])
    vec = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def search(
    query: str,
    top_k: int = 5,
    db_dir: str = DEFAULT_DB_DIR,
    session_filter: int | None = None,
    min_score: float = 0.3,
) -> list[dict]:
    """명리학 지식 검색.

    Args:
        query: 검색 질의 (예: "편관격의 특성과 해석", "공망이 년주에 걸리면")
        top_k: 반환할 결과 수
        db_dir: 인덱스 경로
        session_filter: 특정 회차만 검색 (1~10)
        min_score: 최소 유사도 점수 (0~1)

    Returns:
        [{"text": "...", "topic": "...", "session": 1, "score": 0.85, ...}]
    """
    index = _load_index(db_dir)
    if index is None:
        return [{"error": "지식 베이스가 아직 생성되지 않았습니다. python build_knowledge.py를 먼저 실행하세요."}]

    chunks = index["chunks"]
    embeddings = index["embeddings"]

    # 쿼리 인코딩
    query_vec = _encode_query(query)

    # 세션 필터링
    if session_filter is not None:
        mask = np.array([c["metadata"].get("session") == session_filter for c in chunks])
        filtered_embeddings = embeddings[mask]
        filtered_chunks = [c for c, m in zip(chunks, mask) if m]
    else:
        filtered_embeddings = embeddings
        filtered_chunks = chunks

    if len(filtered_chunks) == 0:
        return []

    # 코사인 유사도 계산 (정규화 완료 상태이므로 내적 = 코사인)
    scores = np.dot(filtered_embeddings, query_vec.T).flatten()

    # 상위 top_k
    top_indices = np.argsort(scores)[::-1][:top_k]

    output = []
    for idx in top_indices:
        score = float(scores[idx])
        if score < min_score:
            continue

        chunk = filtered_chunks[idx]
        meta = chunk["metadata"]

        output.append({
            "text": chunk["text"],
            "topic": meta.get("topic", ""),
            "session": meta.get("session", 0),
            "part": meta.get("part", 0),
            "part_title": meta.get("part_title", ""),
            "date": meta.get("date", ""),
            "filename": meta.get("filename", ""),
            "score": round(score, 4),
        })

    return output


def search_by_saju_context(
    day_stem: str = "",
    pattern_name: str = "",
    yongshin: str = "",
    interactions: list[str] | None = None,
    sinsal: list[str] | None = None,
    strength_label: str = "",
    top_k: int = 5,
    db_dir: str = DEFAULT_DB_DIR,
) -> list[dict]:
    """사주 분석 컨텍스트 기반 자동 검색.

    사주 분석 결과에서 핵심 키워드를 추출하여 관련 강의 내용을 찾아줌.
    """
    queries = []

    if day_stem:
        queries.append(f"{day_stem} 일간의 특성과 해석")

    if pattern_name:
        queries.append(f"{pattern_name} 격국의 의미와 실제 적용")

    if yongshin:
        queries.append(f"용신 {yongshin} 오행 활용법")

    if strength_label:
        if "신강" in strength_label:
            queries.append("신강한 사주의 특성과 용신 설정")
        elif "신약" in strength_label:
            queries.append("신약한 사주의 특성과 용신 설정")

    if interactions:
        for inter in interactions[:2]:
            queries.append(f"{inter} 합충의 의미와 실생활 해석")

    if sinsal:
        for s in sinsal[:2]:
            queries.append(f"{s} 신살의 의미와 해석법")

    all_results = []
    seen_topics = set()

    for q in queries:
        results = search(q, top_k=3, db_dir=db_dir)
        for r in results:
            if "error" in r:
                continue
            topic_key = r.get("topic", "")
            if topic_key not in seen_topics:
                seen_topics.add(topic_key)
                r["query"] = q
                all_results.append(r)

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results[:top_k]


def get_stats(db_dir: str = DEFAULT_DB_DIR) -> dict:
    """지식 베이스 통계."""
    index = _load_index(db_dir)
    if index is None:
        return {"status": "not_built", "total_chunks": 0}

    return {
        "status": "ready",
        "total_chunks": index["total_chunks"],
        "embedding_model": index.get("model_name", EMBEDDING_MODEL),
        "embedding_dim": index["embeddings"].shape[1] if index.get("embeddings") is not None else 0,
        "db_dir": db_dir,
    }
