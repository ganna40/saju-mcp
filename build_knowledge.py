"""명리학 지식 베이스 빌드 스크립트.

Usage:
    python build_knowledge.py
    python build_knowledge.py --summary path/to/summary.json --texts path/to/texts/
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.knowledge.indexer import build_index, build_chunks


def main():
    import argparse
    parser = argparse.ArgumentParser(description="명리학 지식 베이스 빌드")
    parser.add_argument("--summary", default=None, help="summary.json 경로")
    parser.add_argument("--texts", default=None, help="텍스트 파일 디렉토리")
    parser.add_argument("--db", default=None, help="ChromaDB 저장 경로")
    parser.add_argument("--dry-run", action="store_true", help="청킹만 하고 임베딩 안 함")
    args = parser.parse_args()

    kwargs = {}
    if args.summary:
        kwargs["summary_path"] = args.summary
    if args.texts:
        kwargs["texts_dir"] = args.texts
    if args.db:
        kwargs["db_dir"] = args.db

    if args.dry_run:
        print("=== Dry Run: 청킹만 수행 ===")
        chunks = build_chunks(**{k: v for k, v in kwargs.items() if k != "db_dir"})
        print(f"총 청크 수: {len(chunks)}")
        for c in chunks[:5]:
            print(f"  [{c['id']}] {c['metadata']['topic'][:50]} ({len(c['text'])}자)")
        print(f"  ... 외 {len(chunks) - 5}개")
        return

    print("=== 명리학 지식 베이스 빌드 시작 ===")
    print("(임베딩 모델 로드 + 벡터 생성에 1~3분 소요)")
    print()

    start = time.time()
    result = build_index(**kwargs)
    elapsed = time.time() - start

    print()
    print(f"=== 빌드 완료 ({elapsed:.1f}초) ===")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
