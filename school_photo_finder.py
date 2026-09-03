"""
경기도 학교 급식사진 활성도 탐색기
- NEIS API로 경기도 초중고 목록 수집
- 각 학교 main.do 페이지에서 급식사진 메뉴 URL 탐색
- 급식사진 게시물 수 확인 후 상위 100교 선별 → CSV 저장
"""

import requests
import re
import csv
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

NEIS_SCHOOL_URL = "https://open.neis.go.kr/hub/schoolInfo"
NEIS_KEY = "13fa1544e23c480cbb9325441d47b54b"
GYEONGGI_CODE = "J10"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; school-research-bot/1.0)"})


# ──────────────────────────────────────────
# 1. NEIS API: 경기도 전체 학교 목록
# ──────────────────────────────────────────
def get_gyeonggi_schools():
    schools = []
    page = 1
    while True:
        params = {
            "KEY": NEIS_KEY,
            "Type": "json",
            "pIndex": page,
            "pSize": 1000,
            "ATPT_OFCDC_SC_CODE": GYEONGGI_CODE,
        }
        try:
            r = SESSION.get(NEIS_SCHOOL_URL, params=params, timeout=15)
            data = r.json()
            info = data.get("schoolInfo", [])
            if len(info) < 2:
                break
            rows = info[1].get("row", [])
            if not rows:
                break
            schools.extend(rows)
            print(f"  {len(schools)}개 수집 중...", end="\r")
            if len(rows) < 1000:
                break
            page += 1
        except Exception as e:
            print(f"\n  NEIS 오류 (페이지 {page}): {e}")
            break
    return schools


# ──────────────────────────────────────────
# 2. 학교 코드 추출 (URL 서브디렉토리)
# ──────────────────────────────────────────
def extract_school_code(homepage):
    """
    케이스 1: https://baikyang-e.goegy.kr → subdomain = baikyang-e
    케이스 2: https://www.goesw.kr/gghs-m → path = gghs-m
    """
    hp = homepage.strip().rstrip('/')
    m = re.match(r'https?://([^./]+)\.goe\w+\.kr', hp)
    if m and m.group(1) != 'www':
        return m.group(1)
    # www 도메인: 경로에서 school code 추출
    m2 = re.search(r'goe\w+\.kr/([^/?#]+)', hp)
    if m2:
        return m2.group(1)
    return None


def get_main_url(homepage):
    """학교 코드로 main.do URL 조합"""
    code = extract_school_code(homepage)
    if not code:
        return None
    hp = homepage.strip().rstrip('/')
    m = re.match(r'(https?://[^/]+)', hp)
    if not m:
        return None
    base_domain = m.group(1)
    return f"{base_domain}/{code}/main.do"


# ──────────────────────────────────────────
# 3. 급식사진 URL 탐색 (main.do 네비게이션 파싱)
# ──────────────────────────────────────────
def find_food_photo_url(homepage):
    main_url = get_main_url(homepage)
    if not main_url:
        return None
    try:
        r = SESSION.get(main_url, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return None
        html = r.text
        base = homepage.strip().rstrip("/")

        # foodmenu 링크 탐색
        m = re.search(r'href="(/[^"]*foodmenu[^"]*mi=\d+[^"]*)"', html)
        if m:
            return urljoin(base, m.group(1))

        # 급식사진 텍스트 근처 href
        m = re.search(r'href="(/[^"]+)"\s*[^>]*>\s*(?:<[^>]+>)*\s*급식사진\s*', html)
        if m:
            return urljoin(base, m.group(1))

    except Exception:
        pass
    return None


# ──────────────────────────────────────────
# 4. 게시물 수 추정 (급식사진 페이지)
# ──────────────────────────────────────────
def count_food_photos(food_url):
    """
    급식사진 페이지는 주간 캘린더 형태.
    실제 업로드된 사진은 /upload/common/fm/ 경로로 나타남.
    현재 주 + 이전 주 확인해서 최근 활동 학교 선별.
    """
    try:
        r = SESSION.get(food_url, timeout=10)
        html = r.text
        # 실제 업로드된 급식 사진 경로
        uploads = re.findall(r'/upload/common/fm/images/[^"]+\.(?:jpg|jpeg|png)', html)
        current_week = len(uploads)

        if current_week > 0:
            return current_week

        # 현재 주 사진 없으면 이전 주 시도 (schFrYmd 파라미터)
        # form action에 날짜 추가
        import datetime
        today = datetime.date.today()
        prev_week = today - datetime.timedelta(weeks=1)
        prev_str = prev_week.strftime('%Y-%m-%d')

        r2 = SESSION.post(food_url, data={"schFrYmd": prev_str, "schToYmd": prev_str}, timeout=10)
        uploads2 = re.findall(r'/upload/common/fm/images/[^"]+\.(?:jpg|jpeg|png)', r2.text)
        return len(uploads2)

    except Exception:
        return 0


# ──────────────────────────────────────────
# 5. 단일 학교 처리
# ──────────────────────────────────────────
def process_school(school):
    homepage = school.get("HMPG_ADRES", "").strip()
    if not homepage or not re.search(r'goe\w+\.kr', homepage):
        return None

    food_url = find_food_photo_url(homepage)
    if not food_url:
        return None

    count = count_food_photos(food_url)
    if count == 0:
        return None

    return {
        "school_name": school.get("SCHUL_NM", ""),
        "school_code": school.get("SD_SCHUL_CODE", ""),
        "school_type": school.get("SCHUL_KND_SC_NM", ""),
        "location": school.get("ORG_RDNMA", ""),
        "homepage": homepage,
        "food_photo_url": food_url,
        "estimated_posts": count,
    }


# ──────────────────────────────────────────
# 6. 메인
# ──────────────────────────────────────────
def main():
    print("=== 경기도 학교 급식사진 탐색 ===\n")

    print("[1] NEIS API 학교 목록 수집...")
    schools = get_gyeonggi_schools()
    print(f"\n  → {len(schools)}개교 수집 완료\n")

    goe_schools = [s for s in schools if re.search(r'goe\w+\.kr', s.get("HMPG_ADRES") or "")]
    print(f"[2] goe*.kr 도메인 학교: {len(goe_schools)}개교")
    print(f"  급식사진 페이지 탐색 중 (병렬 20 workers)...\n")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=20) as exe:
        futures = {exe.submit(process_school, s): s for s in goe_schools}
        for f in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(goe_schools)} 처리... (발견: {len(results)}개교)")
            r = f.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: x["estimated_posts"], reverse=True)

    print(f"\n[3] 급식사진 게시 학교: {len(results)}개교\n")

    import os
    base = os.path.dirname(os.path.abspath(__file__))

    # 전체 저장
    output_all = os.path.join(base, "school_photos_all.csv")
    fields = ["rank", "school_name", "school_type", "location", "school_code", "homepage", "food_photo_url", "estimated_posts"]
    with open(output_all, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, s in enumerate(results, 1):
            w.writerow({"rank": i, **s})
    print(f"[완료] {output_all} ({len(results)}개교) 저장\n")

    # 상위 100교도 유지 (기존 호환)
    top100 = results[:100]
    output_top = os.path.join(base, "school_photos_top100.csv")
    with open(output_top, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, s in enumerate(top100, 1):
            w.writerow({"rank": i, **s})

    print("=== 상위 20개교 ===")
    for i, s in enumerate(top100[:20], 1):
        print(f"  {i:2}. {s['school_name']} ({s['school_type']}) — 추정 {s['estimated_posts']}건")

    return results


if __name__ == "__main__":
    main()
