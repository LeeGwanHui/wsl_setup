#!/usr/bin/env python3
"""
카카오 로컬(Local) 키워드 검색 — 데이트 코스 스킬용 실제 가게 검색 도구.

표준 라이브러리만 사용 (설치 불필요).

API 키 로딩 순서:
  1) 환경변수 KAKAO_REST_API_KEY
  2) 이 스크립트와 같은 폴더의 .kakao_key 파일 (공개 repo 커밋 금지 → .gitignore 처리)

사용법:
  python3 kakao_search.py "성수동 감성 카페" [--size 15] [--pages 3] [--category CE7]
                          [--x 127.05 --y 37.54 --radius 2000] [--sort accuracy|distance] [--json]

주요 카테고리 코드(--category): CE7 카페 · FD6 음식점 · AT4 관광명소 · CT1 문화시설 · AD5 숙박

출력(기본): 사람이 읽기 좋은 목록 (이름 · 카테고리 · 주소 · 전화 · 좌표 · 링크 · 거리)
--json     : 원본에 가까운 JSON 배열
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

# Windows 콘솔(cp949) 등에서도 한글이 깨지지 않도록 UTF-8 강제
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def load_api_key() -> str:
    key = os.environ.get("KAKAO_REST_API_KEY", "").strip()
    if key:
        return key
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kakao_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    sys.exit(
        "ERROR: 카카오 REST API 키를 찾을 수 없습니다.\n"
        "  - 환경변수 KAKAO_REST_API_KEY 를 설정하거나\n"
        f"  - {key_file} 파일에 키를 저장하세요.\n"
        "키 발급: https://developers.kakao.com → 내 애플리케이션 → 앱 키 → REST API 키"
    )


def search(query, size=15, x=None, y=None, radius=None, sort="accuracy", page=1, category=None):
    params = {"query": query, "size": size, "page": page, "sort": sort}
    if category:
        params["category_group_code"] = category
    if x is not None and y is not None:
        params["x"] = x
        params["y"] = y
        if radius is not None:
            params["radius"] = radius  # meters, 0~20000
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "KakaoAK " + load_api_key())
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        sys.exit(f"ERROR: 카카오 API HTTP {e.code}\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: 네트워크 오류 — {e.reason}")


def search_pages(query, want, x=None, y=None, radius=None, sort="accuracy", category=None):
    """여러 페이지를 모아 id 기준 중복 제거 후 want 건까지 반환. 카카오 keyword API는
    한 요청당 최대 15건이라, want>15 이면 page 를 늘려가며 채운다(최대 45페이지)."""
    seen, docs = set(), []
    page = 1
    while len(docs) < want and page <= 45:
        data = search(query, size=15, x=x, y=y, radius=radius,
                      sort=sort, page=page, category=category)
        batch = data.get("documents", [])
        for d in batch:
            did = d.get("id") or (d.get("place_name", ""), d.get("x", ""), d.get("y", ""))
            if did in seen:
                continue
            seen.add(did)
            docs.append(d)
        if data.get("meta", {}).get("is_end", True):
            break
        page += 1
    return docs[:want], data.get("meta", {}).get("total_count", len(docs))


def fmt(docs):
    if not docs:
        return "(검색 결과 없음)"
    lines = []
    for i, d in enumerate(docs, 1):
        cat = d.get("category_name", "")
        # 카테고리 뒤쪽만 (예: '음식점 > 카페 > 커피전문점' → '카페 > 커피전문점')
        cat_short = " > ".join(cat.split(" > ")[1:]) or cat
        addr = d.get("road_address_name") or d.get("address_name", "")
        phone = d.get("phone", "")
        dist = d.get("distance", "")  # 중심 좌표(--x/--y) 지정 시에만 채워짐
        lines.append(
            f"{i}. {d.get('place_name','')}"
            + (f"  [{cat_short}]" if cat_short else "")
            + (f"  · 거리 {dist}m" if dist else "")
        )
        lines.append(f"   📍 {addr}" + (f"  ☎ {phone}" if phone else ""))
        lines.append(
            f"   🔗 {d.get('place_url','')}   (x={d.get('x','')}, y={d.get('y','')})"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="카카오 로컬 키워드 검색")
    ap.add_argument("query", help="검색어 (예: '성수동 감성 카페')")
    ap.add_argument("--size", type=int, default=15, help="결과 개수 (기본 15). 15 초과면 여러 페이지를 모음")
    ap.add_argument("--pages", type=int, default=1, help="모을 페이지 수 (기본 1). 후보 풀 확대·중복 제거")
    ap.add_argument("--page", type=int, default=1, help="단일 페이지 지정 1~45 (--pages 미사용 시)")
    ap.add_argument("--category", help="카테고리 코드: CE7 카페·FD6 음식점·AT4 관광명소·CT1 문화시설·AD5 숙박")
    ap.add_argument("--x", help="중심 경도(longitude)")
    ap.add_argument("--y", help="중심 위도(latitude)")
    ap.add_argument("--radius", type=int, help="반경(m) 0~20000, --x/--y와 함께")
    ap.add_argument("--sort", choices=["accuracy", "distance"], default="accuracy")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args()

    # --pages 또는 size>15 이면 여러 페이지를 모아 dedupe, 아니면 단일 요청.
    if args.pages > 1 or args.size > 15:
        want = args.size if args.size > 15 else args.pages * 15
        docs, total = search_pages(
            args.query, want=want, x=args.x, y=args.y,
            radius=args.radius, sort=args.sort, category=args.category,
        )
    else:
        data = search(
            args.query,
            size=max(1, min(15, args.size)),
            x=args.x, y=args.y, radius=args.radius,
            sort=args.sort, page=args.page, category=args.category,
        )
        docs = data.get("documents", [])
        total = data.get("meta", {}).get("total_count", len(docs))

    if args.json:
        print(json.dumps(docs, ensure_ascii=False, indent=2))
    else:
        print(f"# '{args.query}' — 총 {total}건 중 {len(docs)}건\n")
        print(fmt(docs))


if __name__ == "__main__":
    main()
