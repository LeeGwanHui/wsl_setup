#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이트 코스 동선 계산기 — 정류지 좌표로 구간 도보시간·총 동선을 추정한다.

카카오 길찾기 유료 API 없이, 좌표(경도,위도)만으로 haversine 직선거리를 구하고
현실 보행에 맞춰 보정한다. "감으로 도보 8분" 대신 계산값으로 동선을 검증하는 용도.

가정:
  - 보행 속도 ~80 m/분(4.8 km/h), 도심 우회계수 1.3(직선거리 → 실제 도보거리)
  - 한 구간이 임계(기본 1.2 km) 초과면 "대중교통 권장" 플래그

사용법:
  python3 route_util.py "127.0557,37.5445" "127.0631,37.5471" "127.0668,37.5443"
  python3 route_util.py --walk-threshold 1000 "경도,위도" "경도,위도" ...
  echo '[[127.05,37.54],[127.06,37.55]]' | python3 route_util.py --stdin   # JSON [[lng,lat],...]
  (--json 으로 기계용 결과 출력)

좌표는 카카오 검색 결과의 x(경도), y(위도)를 그대로 "x,y" 로 넣는다.
"""
import argparse
import json
import math
import sys

WALK_M_PER_MIN = 80.0   # 보행 속도(m/분)
DETOUR_FACTOR = 1.3     # 직선거리 → 실제 도보거리 보정
DEFAULT_WALK_THRESHOLD_M = 1200  # 이 이상이면 대중교통 권장
TRANSIT_BASE_MIN = 10.0   # 대중교통 오버헤드(역까지 도보·대기·승하차)
TRANSIT_M_PER_MIN = 500.0  # 시내 대중교통 체감 속도(정차 포함, ≈30km/h)


def haversine_m(lng1, lat1, lng2, lat2):
    """두 좌표(경도,위도, 도 단위) 사이 대권거리(m)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def walk_minutes(distance_m):
    return distance_m / WALK_M_PER_MIN


def leg(a, b, threshold_m):
    """정류지 a→b 한 구간 계산."""
    straight = haversine_m(a[0], a[1], b[0], b[1])
    walk_m = straight * DETOUR_FACTOR
    transit = walk_m > threshold_m
    d = {
        "straight_m": round(straight),
        "walk_m": round(walk_m),
        "walk_min": round(walk_minutes(walk_m)),
        "mode": "대중교통 권장" if transit else "도보",
    }
    if transit:
        # 지하철/버스 추정치 — 실제 노선·환승은 웹으로 확인할 것
        d["transit_min"] = round(TRANSIT_BASE_MIN + straight / TRANSIT_M_PER_MIN)
    return d


def compute(points, threshold_m=DEFAULT_WALK_THRESHOLD_M):
    legs = [leg(points[i], points[i + 1], threshold_m) for i in range(len(points) - 1)]
    walk_m = sum(l["walk_m"] for l in legs if l["mode"] == "도보")
    transit_min = sum(l.get("transit_min", 0) for l in legs)
    # 분 합산은 마지막에 한 번만 반올림 (구간별 반올림 누적 방지)
    total_walk_min = round(walk_m / WALK_M_PER_MIN)
    return {
        "legs": legs,
        "n_stops": len(points),
        "total_walk_m": walk_m,
        "total_walk_min": total_walk_min,
        "total_transit_min": transit_min,
        "total_move_min": total_walk_min + transit_min,
        "transit_legs": sum(1 for l in legs if l["mode"] != "도보"),
    }


def parse_point(s):
    """'경도,위도' → (lng, lat) float 튜플."""
    parts = s.replace(" ", "").split(",")
    if len(parts) != 2:
        sys.exit(f"ERROR: 좌표 형식은 '경도,위도' 여야 합니다: {s!r}")
    try:
        return (float(parts[0]), float(parts[1]))
    except ValueError:
        sys.exit(f"ERROR: 좌표를 숫자로 해석할 수 없습니다: {s!r}")


def fmt(result):
    lines = [f"# 동선 검증 — 정류지 {result['n_stops']}곳"]
    for i, l in enumerate(result["legs"], 1):
        flag = (
            f"  🚇 대중교통 권장 (약 {l['transit_min']}분 추정)"
            if l["mode"] != "도보" else ""
        )
        lines.append(
            f"  {i}→{i+1}: 도보 약 {l['walk_min']}분 "
            f"(≈{l['walk_m']}m, 직선 {l['straight_m']}m){flag}"
        )
    total = f"\n총 이동: 약 {result['total_move_min']}분"
    if result["transit_legs"]:
        total += (
            f" = 도보 {result['total_walk_min']}분({result['total_walk_m']}m)"
            f" + 대중교통 약 {result['total_transit_min']}분"
            f" ({result['transit_legs']}개 구간, 추정 — 실제 노선은 웹 확인 권장)"
        )
    else:
        total += f" (전 구간 도보, {result['total_walk_m']}m)"
    lines.append(total)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="데이트 코스 동선(도보시간) 계산기")
    ap.add_argument("points", nargs="*", help="정류지 좌표들 '경도,위도' (순서대로)")
    ap.add_argument("--stdin", action="store_true", help="stdin에서 JSON [[lng,lat],...] 읽기")
    ap.add_argument("--walk-threshold", type=int, default=DEFAULT_WALK_THRESHOLD_M,
                    help=f"도보 임계(m). 초과 시 대중교통 권장 (기본 {DEFAULT_WALK_THRESHOLD_M})")
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    args = ap.parse_args()

    if args.stdin:
        raw = json.load(sys.stdin)
        points = [(float(p[0]), float(p[1])) for p in raw]
    else:
        points = [parse_point(s) for s in args.points]

    if len(points) < 2:
        sys.exit("ERROR: 정류지 좌표가 최소 2개 필요합니다.")

    result = compute(points, threshold_m=args.walk_threshold)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(fmt(result))


if __name__ == "__main__":
    main()
