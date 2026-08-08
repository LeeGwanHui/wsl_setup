#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이트 코스 → 공유용 HTML 카드 생성기 (표준 라이브러리만 사용).

확정된 코스(JSON)를 세로 타임라인 HTML 한 장으로 렌더한다. 결과 파일은
SendUserFile(display: render)로 사용자에게 보여주거나 그대로 저장/공유할 수 있다.
※ claude.ai Artifact가 아니라 로컬 HTML 파일이다(카카오 지도 JS는 Artifact CSP에 막히므로).

입력 JSON 스키마:
{
  "title": "성수동 오후 데이트",
  "meta":  "오후 2시 · 약 4시간 · 감성 카페",     // 선택
  "courses": [
    {
      "name": "A안 · 감성 카페 데이트",
      "concept": "여유롭게 걷고 대화 중심",          // 선택
      "cost": "1인 약 3~4만 원",                    // 선택
      "route_summary": "○○ → ○○ → ○○ (총 도보 20분)", // 선택
      "plan_b": "비 오면 △△ 실내 전시로 대체",        // 선택
      "tips": ["📵 폰 내려놓고 몰입하기 좋은 코스", "📸 피날레에서 한 컷"], // 선택
      "factors": ["peak-end", "novelty", "mood"],    // 선택(공유 PWA에서 심리 근거 칩으로 표시. slug은 date_course_selection/build_web_data.py 참조)
      "outfit": {                                    // 선택(fashion 연동. 조정 후 최종 구성)
        "formula": "A-2 (여름 데이트)",              // 선택(기반 공식 라벨)
        "items": ["흰 반팔", "베이지 치노", "흰 독일군"], // items만 필수
        "swaps": ["4km 보행 — 로퍼 대신 스니커즈"],   // 선택
        "why": "밝은 톤 상하 + 브라운 소품 검증 조합", // 선택(체형 근거 금지)
        "checks": ["넣어 입기"]                       // 선택
      },
      "stops": [
        {
          "time": "14:00", "name": "가게 이름",
          "reason": "추천 이유 한 줄",               // 선택
          "stay": "약 1시간",                        // 선택
          "move": "도보 8분",                        // 다음 장소로 이동(마지막 stop은 생략)
          "place_url": "http://place.map.kakao.com/…", // 선택(카카오맵 링크)
          "badge": "peak" | "finale",                // 선택(🎯 피크 / 🏁 피날레)
          "x": "127.05", "y": "37.54"                 // 선택(지도용 좌표)
        }
      ]
    }
  ]
}

사용법:
  python3 render_course.py course.json -o course.html
  echo '<JSON>' | python3 render_course.py --stdin -o course.html
  python3 render_course.py course.json -o course.html --js-key <KAKAO_JS_KEY>   # 실제 지도 임베드(선택)

지도(--js-key): 카카오 JS 키가 있으면 각 코스에 마커+경로 지도를 넣는다. 없으면 각 장소의
'카카오맵에서 열기' 링크만 넣는다(키 불필요, 기본값). JS 키는 --js-key 인자 또는
스킬 폴더의 .kakao_js_key 파일에서 읽는다. (JS 키는 developers.kakao.com의 JavaScript 키이며
REST 키와 다르고, 사용 도메인 등록이 필요할 수 있다.)
"""
import argparse
import html
import json
import os
import sys

BADGE = {
    "peak": ("🎯", "피크"),
    "finale": ("🏁", "피날레"),
}


def esc(s):
    return html.escape("" if s is None else str(s))


def load_js_key(cli_key):
    if cli_key:
        return cli_key.strip()
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kakao_js_key")
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            k = f.read().strip()
            if k:
                return k
    return None


def render_outfit(course):
    o = course.get("outfit")
    if not o or not o.get("items"):
        return ""
    head = "👔 복장" + (f" · {esc(o['formula'])}" if o.get("formula") else "")
    bits = [f'<div class="outfit-head">{head}</div>']
    bits.append(f'<div class="outfit-items">{esc(" + ".join(o["items"]))}</div>')
    for sw in o.get("swaps", []) or []:
        bits.append(f'<div class="outfit-swap">⚠️ {esc(sw)}</div>')
    if o.get("why"):
        bits.append(f'<div class="outfit-why">↳ {esc(o["why"])}</div>')
    if o.get("checks"):
        bits.append(f'<div class="outfit-check">✓ {esc(" · ".join(o["checks"]))}</div>')
    return f'<div class="outfit">{"".join(bits)}</div>'


def render_stop(stop):
    badge_html = ""
    if stop.get("badge") in BADGE:
        emoji, label = BADGE[stop["badge"]]
        badge_html = f'<span class="badge {esc(stop["badge"])}">{emoji} {label}</span>'
    name = esc(stop.get("name", ""))
    if stop.get("place_url"):
        name = f'<a href="{esc(stop["place_url"])}" target="_blank" rel="noopener">{name} ↗</a>'
    meta_bits = []
    if stop.get("stay"):
        meta_bits.append(f'체류 {esc(stop["stay"])}')
    meta_line = f'<div class="stop-meta">{" · ".join(meta_bits)}</div>' if meta_bits else ""
    reason = f'<div class="stop-reason">{esc(stop["reason"])}</div>' if stop.get("reason") else ""
    move = (
        f'<div class="move"><span>🚶 {esc(stop["move"])}</span></div>'
        if stop.get("move") else ""
    )
    return f"""      <li class="stop">
        <div class="dot"></div>
        <div class="stop-body">
          <div class="stop-head"><span class="time">{esc(stop.get("time",""))}</span> {badge_html}</div>
          <div class="stop-name">{name}</div>
          {reason}
          {meta_line}
        </div>
      </li>
      {f'<li class="move-row">{move}</li>' if move else ''}"""


def render_map(course, idx, js_key):
    """js_key가 있을 때만 카카오 지도(마커+경로) div/스크립트를 만든다."""
    pts = [s for s in course.get("stops", []) if s.get("x") and s.get("y")]
    if not js_key or len(pts) < 1:
        return "", ""
    markers = json.dumps(
        [{"x": float(s["x"]), "y": float(s["y"]), "name": s.get("name", "")} for s in pts],
        ensure_ascii=False,
    )
    div = f'<div id="map-{idx}" class="map"></div>'
    script = f"""
    (function() {{
      var pts = {markers};
      var map = new kakao.maps.Map(document.getElementById('map-{idx}'), {{
        center: new kakao.maps.LatLng(pts[0].y, pts[0].x), level: 5
      }});
      var path = [], bounds = new kakao.maps.LatLngBounds();
      pts.forEach(function(p, i) {{
        var pos = new kakao.maps.LatLng(p.y, p.x);
        path.push(pos); bounds.extend(pos);
        new kakao.maps.Marker({{ map: map, position: pos, title: (i+1)+'. '+p.name }});
      }});
      if (path.length > 1) new kakao.maps.Polyline({{
        map: map, path: path, strokeWeight: 4, strokeColor: '#e85d75',
        strokeOpacity: 0.85, strokeStyle: 'solid'
      }});
      map.setBounds(bounds);
    }})();"""
    return div, script


def render_course(course, idx, js_key):
    header_bits = []
    if course.get("concept"):
        header_bits.append(f'<p class="concept">{esc(course["concept"])}</p>')
    facts = []
    if course.get("route_summary"):
        facts.append(f'<span>🗺️ {esc(course["route_summary"])}</span>')
    if course.get("cost"):
        facts.append(f'<span>💰 {esc(course["cost"])}</span>')
    facts_html = f'<div class="facts">{"".join(facts)}</div>' if facts else ""

    stops_html = "\n".join(render_stop(s) for s in course.get("stops", []))
    map_div, map_script = render_map(course, idx, js_key)

    footer_bits = []
    if course.get("plan_b"):
        footer_bits.append(f'<div class="note">☔ <b>Plan B</b> — {esc(course["plan_b"])}</div>')
    for tip in course.get("tips", []) or []:
        footer_bits.append(f'<div class="note">{esc(tip)}</div>')
    footer_html = "".join(footer_bits)
    outfit_html = render_outfit(course)

    return f"""  <section class="course">
    <h2>{esc(course.get("name", f"코스 {idx+1}"))}</h2>
    {"".join(header_bits)}
    {facts_html}
    {map_div}
    <ul class="timeline">
{stops_html}
    </ul>
    {footer_html}
    {outfit_html}
  </section>""", map_script


def build_html(data, js_key):
    title = esc(data.get("title", "데이트 코스"))
    meta = f'<p class="subtitle">{esc(data["meta"])}</p>' if data.get("meta") else ""
    sections, scripts = [], []
    for i, course in enumerate(data.get("courses", [])):
        sec, scr = render_course(course, i, js_key)
        sections.append(sec)
        if scr:
            scripts.append(scr)

    map_sdk = ""
    if js_key and scripts:
        joined = "\n".join(scripts)
        map_sdk = f"""
  <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={esc(js_key)}&autoload=false"></script>
  <script>kakao.maps.load(function() {{{joined}
  }});</script>"""

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  :root {{
    --bg: #fbf7f5; --card: #ffffff; --ink: #2b2431; --muted: #7a6f78;
    --line: #ecdfe2; --accent: #e85d75; --peak: #f0a202; --finale: #9b5de5;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#1a161c; --card:#241f28; --ink:#f2ecf0; --muted:#a99fa8;
             --line:#3a3340; --accent:#ff7a90; }}
  }}
  :root[data-theme="light"] {{ --bg:#fbf7f5; --card:#fff; --ink:#2b2431; --muted:#7a6f78; --line:#ecdfe2; }}
  :root[data-theme="dark"]  {{ --bg:#1a161c; --card:#241f28; --ink:#f2ecf0; --muted:#a99fa8; --line:#3a3340; --accent:#ff7a90; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:24px 16px 48px; background:var(--bg); color:var(--ink);
    font-family: -apple-system, "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
    line-height:1.55; }}
  .wrap {{ max-width: 640px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
  .subtitle {{ color: var(--muted); margin: 0 0 24px; }}
  .course {{ background: var(--card); border:1px solid var(--line); border-radius:16px;
    padding: 20px 20px 16px; margin-bottom: 22px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }}
  .course h2 {{ font-size: 1.2rem; margin: 0 0 2px; }}
  .concept {{ color: var(--muted); margin: 0 0 12px; font-size:.95rem; }}
  .facts {{ display:flex; flex-wrap:wrap; gap:6px 14px; font-size:.85rem; color:var(--muted); margin-bottom:14px; }}
  .map {{ width:100%; height:260px; border-radius:12px; margin: 4px 0 16px; border:1px solid var(--line); }}
  .timeline {{ list-style:none; margin:0; padding:0; position:relative; }}
  .timeline::before {{ content:""; position:absolute; left:7px; top:6px; bottom:6px;
    width:2px; background:var(--line); }}
  .stop {{ position:relative; padding: 0 0 4px 30px; }}
  .dot {{ position:absolute; left:0; top:5px; width:16px; height:16px; border-radius:50%;
    background:var(--card); border:3px solid var(--accent); }}
  .stop-head {{ display:flex; align-items:center; gap:8px; }}
  .time {{ font-weight:700; color:var(--accent); font-variant-numeric: tabular-nums; }}
  .stop-name {{ font-weight:600; font-size:1.02rem; margin-top:1px; }}
  .stop-name a {{ color:inherit; text-decoration:none; border-bottom:1px solid var(--line); }}
  .stop-reason {{ color:var(--ink); opacity:.85; font-size:.92rem; margin-top:2px; }}
  .stop-meta {{ color:var(--muted); font-size:.82rem; margin-top:2px; }}
  .move-row {{ list-style:none; }}
  .move {{ padding: 6px 0 6px 30px; color:var(--muted); font-size:.82rem; }}
  .badge {{ font-size:.72rem; font-weight:700; padding:2px 8px; border-radius:999px; color:#fff; }}
  .badge.peak {{ background: var(--peak); }}
  .badge.finale {{ background: var(--finale); }}
  .note {{ margin-top:10px; padding:10px 12px; background:var(--bg); border-radius:10px;
    font-size:.88rem; color:var(--ink); opacity:.92; }}
  .outfit {{ margin-top:10px; padding:10px 12px; background:var(--bg); border-radius:10px;
    font-size:.88rem; color:var(--ink); }}
  .outfit-head {{ font-weight:700; }}
  .outfit-items {{ margin-top:4px; }}
  .outfit-swap {{ margin-top:4px; color:var(--finale); }}
  .outfit-why {{ margin-top:4px; color:var(--muted); }}
  .outfit-check {{ margin-top:4px; color:var(--muted); font-size:.82rem; }}
  a {{ color: var(--accent); }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>{title}</h1>
    {meta}
{chr(10).join(sections)}
  </div>{map_sdk}
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(description="데이트 코스 → HTML 카드")
    ap.add_argument("input", nargs="?", help="코스 JSON 파일 경로 (또는 --stdin)")
    ap.add_argument("--stdin", action="store_true", help="stdin에서 JSON 읽기")
    ap.add_argument("-o", "--out", required=True, help="출력 HTML 경로")
    ap.add_argument("--js-key", help="카카오 JavaScript 키(지도 임베드). 없으면 링크만.")
    args = ap.parse_args()

    if args.stdin:
        data = json.load(sys.stdin)
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        sys.exit("ERROR: JSON 입력 파일 경로나 --stdin 중 하나가 필요합니다.")

    js_key = load_js_key(args.js_key)
    html_out = build_html(data, js_key)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)
    n = len(data.get("courses", []))
    print(f"[OK] HTML written: {args.out}  (코스 {n}개, 지도 {'ON' if js_key else 'OFF(링크만)'})")


if __name__ == "__main__":
    main()
