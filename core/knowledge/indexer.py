"""명리학 강의 인덱서 — summary.json + 원문 텍스트를 청킹하여 벡터 인덱스 생성."""
from __future__ import annotations

import json
import os
import re
import pickle
from pathlib import Path

import numpy as np

# ── 설정 ──
DEFAULT_SUMMARY = str(Path.home() / "Documents" / "summary" / "summary.json")
DEFAULT_TEXTS_DIR = str(Path.home() / "Documents" / "Whisper Output" / "_text")
DEFAULT_DB_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_db")
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
INDEX_FILE = "index.pkl"


def _load_summary(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_text(texts_dir: str, filename: str) -> str:
    filepath = os.path.join(texts_dir, filename)
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def _find_relevant_passage(full_text: str, topic: str, points: list[str],
                            window: int = 500) -> str:
    """원문에서 토픽과 관련된 구간을 추출."""
    if not full_text:
        return ""

    keywords = re.sub(r"[()（）\[\]【】]", " ", topic)
    keywords = [k.strip() for k in keywords.split() if len(k.strip()) >= 2]

    for p in points[:3]:
        clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", p)
        words = [w for w in clean.split() if len(w) >= 3]
        keywords.extend(words[:2])

    best_pos = -1
    best_score = 0

    step = 200
    for i in range(0, max(1, len(full_text) - window), step):
        chunk = full_text[i:i + window]
        score = sum(1 for kw in keywords if kw in chunk)
        if score > best_score:
            best_score = score
            best_pos = i

    if best_pos >= 0 and best_score >= 2:
        return full_text[best_pos:best_pos + window].strip()

    return ""


def build_chunks(
    summary_path: str = DEFAULT_SUMMARY,
    texts_dir: str = DEFAULT_TEXTS_DIR,
) -> list[dict]:
    """summary.json + 원문 텍스트를 결합하여 청크 생성."""
    summary = _load_summary(summary_path)
    chunks = []
    text_cache: dict[str, str] = {}

    for sess in summary["sessions"]:
        session_num = sess["session"]
        date = sess.get("date", "")

        for part in sess["parts"]:
            part_num = part["part"]
            filename = part.get("filename", "")
            part_title = part.get("title", "")

            if filename and filename not in text_cache:
                text_cache[filename] = _load_text(texts_dir, filename)
            full_text = text_cache.get(filename, "")

            for t_idx, topic_data in enumerate(part["topics"]):
                topic = topic_data.get("topic", "")
                points = topic_data.get("points", [])
                subtopics = topic_data.get("subtopics", [])

                if not topic:
                    continue

                chunk_id = f"s{session_num:02d}_p{part_num}_t{t_idx:03d}"

                text_parts = [f"[{topic}]"]

                for p in points:
                    clean_p = re.sub(r"\*\*([^*]+)\*\*", r"\1", p)
                    text_parts.append(clean_p)

                for sub in subtopics:
                    sub_topic = sub.get("topic", "")
                    sub_points = sub.get("points", [])
                    if sub_topic:
                        text_parts.append(f"  [{sub_topic}]")
                    for sp in sub_points:
                        clean_sp = re.sub(r"\*\*([^*]+)\*\*", r"\1", sp)
                        text_parts.append(f"  {clean_sp}")

                passage = _find_relevant_passage(full_text, topic, points)
                if passage:
                    text_parts.append(f"[원문] {passage}")

                chunk_text = "\n".join(text_parts)

                metadata = {
                    "session": session_num,
                    "part": part_num,
                    "date": date,
                    "part_title": part_title,
                    "topic": topic,
                    "filename": filename,
                    "chunk_type": "topic",
                }

                if len(chunk_text) > 2000:
                    chunks.append({
                        "id": f"{chunk_id}_a",
                        "text": chunk_text[:2000],
                        "metadata": {**metadata, "chunk_type": "topic"},
                    })
                    chunks.append({
                        "id": f"{chunk_id}_b",
                        "text": chunk_text[1800:],
                        "metadata": {**metadata, "chunk_type": "topic_cont"},
                    })
                else:
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": metadata,
                    })

    return chunks


def build_index(
    summary_path: str = DEFAULT_SUMMARY,
    texts_dir: str = DEFAULT_TEXTS_DIR,
    db_dir: str = DEFAULT_DB_DIR,
) -> dict:
    """전체 인덱스 빌드 — 청킹 + 임베딩 + 저장.

    Returns:
        {"total_chunks": N, "db_dir": "...", "embedding_model": "..."}
    """
    from sentence_transformers import SentenceTransformer

    chunks = build_chunks(summary_path, texts_dir)

    if not chunks:
        return {"error": "No chunks generated", "total_chunks": 0}

    print(f"  청크 {len(chunks)}개 생성 완료. 임베딩 시작...")

    # 임베딩 생성
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    # numpy 배열로 변환 + L2 정규화 (코사인 유사도용)
    embeddings = np.array(embeddings, dtype=np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    embeddings = embeddings / norms

    # 저장
    os.makedirs(db_dir, exist_ok=True)
    index_path = os.path.join(db_dir, INDEX_FILE)

    index_data = {
        "chunks": chunks,
        "embeddings": embeddings,
        "model_name": EMBEDDING_MODEL,
        "total_chunks": len(chunks),
    }

    with open(index_path, "wb") as f:
        pickle.dump(index_data, f)

    size_mb = os.path.getsize(index_path) / (1024 * 1024)

    return {
        "total_chunks": len(chunks),
        "db_dir": db_dir,
        "index_file": index_path,
        "index_size_mb": round(size_mb, 1),
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": embeddings.shape[1],
    }
