"""
경기도 학교 급식사진 + 메뉴 수집기 (v2)
school_photos_top100.csv → school_meal_photos.json

파싱 전략:
  - <thead> <th>에서 컬럼별 날짜 추출 (일~토 7개)
  - <tbody> <tr>/<td>에서 컬럼 순서로 날짜 매핑
  - 메뉴명: 한글 반찬명 (알레르기 번호 . 포함) 추출 후 번호 제거
  - 사진: /upload/common/fm/images/ 경로만 수집
"""

import csv, json, re, datetime, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
})

WEEKS_BACK = 8
# 메뉴에서 제외할 패턴
SKIP_WORDS = re.compile(
    r'상세보기|원산지|닫기|이전|다음|구분|급식일|식단|캘린더|알레르기|표기|게시|주간|신청|선택'
    r'|에너지|단백질|칼슘|나트륨|탄수화물|지방|열량|kcal|mg'
    r'|위탁식단|참고|운영|학교명|소계'
)
# 알레르기 번호 제거: "현미밥5.6.18" → "현미밥"
ALLER_NUM = re.compile(r'[\d\s.,()\[\]①-⑲]+$')


def clean_menu(text):
    """알레르기 번호 등 불필요 부분 제거 후 반찬명만 반환"""
    text = text.strip()
    # 앞쪽 글머리표 제거: ㆍ · • ▶ ▷ - 등
    text = re.sub(r'^[ㆍ·•▶▷\-\*\s]+', '', text)
    # 괄호 안 숫자 (알레르기): "(5.6.13)" 또는 "(JS)" 형태
    text = re.sub(r'\([^가-힣a-zA-Z]*[\d.]+[^가-힣a-zA-Z]*\)', '', text)
    # 뒤쪽 숫자+점 조합: "현미밥5.6.18", "깍두기9", "후리가케밥5." → 제거
    text = re.sub(r'[\d][.\d]*\s*$', '', text).strip()
    # (JS) 같은 괄호 영문도 제거
    text = re.sub(r'\([A-Z]{1,5}\)', '', text).strip()
    # 특수기호 제거
    text = re.sub(r'[★☆◆◇●○□■ㆍ·•]', '', text).strip()
    return text


def parse_week(html, base_url):
    """
    주간 급식 페이지 → [{date, menus, photos}] 반환
    """
    origin = re.match(r'https?://[^/]+', base_url)
    origin = origin.group(0) if origin else ''

    # ── 1. 컬럼 날짜 순서 추출 (일~토) ──
    col_dates = re.findall(
        r'<th[^>]*scope=["\']col["\'][^>]*>.*?<br[^/]*/?>(\d{4}-\d{2}-\d{2})',
        html, re.DOTALL | re.IGNORECASE
    )
    if not col_dates:
        # fallback: span.txt_p에서 주 범위 → 월요일만
        wk = re.search(r'(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})', html)
        if wk:
            start = datetime.date.fromisoformat(wk.group(1))
            col_dates = [(start + datetime.timedelta(days=i)).isoformat() for i in range(7)]

    if not col_dates:
        return []

    n_cols = len(col_dates)

    # ── 2. tbody 파싱 ──
    tbody_m = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL | re.IGNORECASE)
    if not tbody_m:
        return []
    tbody = tbody_m.group(1)

    # <tr> 분리
    rows = re.split(r'<tr[^>]*>', tbody)

    # 날짜별 누적 (같은 날짜에 여러 row 가능 → 병합)
    date_data = {}  # date → {menus: set, photos: list}

    col_idx = 0  # 컬럼 인덱스 (tbody 전체 기준)

    for row in rows:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
        if not tds:
            continue

        for td in tds:
            if n_cols > 0:
                date = col_dates[col_idx % n_cols]
            else:
                continue

            # 사진
            photos = re.findall(
                r'/upload/common/fm/images/[^\s"\'<>]+\.(?:jpg|jpeg|png)',
                td, re.IGNORECASE
            )

            # 메뉴명: <td> 내부 텍스트 줄별로
            text_raw = re.sub(r'<[^>]+>', '\n', td)
            menus = []
            for line in text_raw.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if SKIP_WORDS.search(line):
                    continue
                cleaned = clean_menu(line)
                if len(cleaned) < 2:
                    continue
                if not re.search('[가-힣]{2,}', cleaned):
                    continue
                if len(cleaned) > 25:
                    continue
                menus.append(cleaned)

            if date not in date_data:
                date_data[date] = {'menus': [], 'photos': [], 'menu_set': set()}

            for m in menus:
                if m not in date_data[date]['menu_set']:
                    date_data[date]['menu_set'].add(m)
                    date_data[date]['menus'].append(m)

            for p in photos:
                full = origin + p if not p.startswith('http') else p
                if full not in date_data[date]['photos']:
                    date_data[date]['photos'].append(full)

            col_idx += 1

    # ── 3. 결과 정리 ──
    results = []
    for date, d in date_data.items():
        if not d['photos'] and not d['menus']:
            continue
        try:
            dt = datetime.date.fromisoformat(date)
            # 주말 제외 (선택사항 - 제거하면 주말도 포함)
            # if dt.weekday() >= 5: continue
            # 2023 이전은 너무 오래됨
            if dt.year < 2024:
                continue
        except ValueError:
            continue
        results.append({
            'date': date,
            'menus': d['menus'][:12],
            'photos': d['photos'][:5],
        })

    return results


def fetch_html(url, date=None):
    try:
        if date:
            ds = date.isoformat()
            r = SESSION.post(url, data={'schFrYmd': ds, 'schToYmd': ds}, timeout=12)
        else:
            r = SESSION.get(url, timeout=12)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ''


def scrape_school(row):
    food_url = (row.get('food_photo_url') or '').strip()
    base_url = (row.get('homepage') or '').strip().rstrip('/')
    if not food_url:
        return None

    all_entries = {}

    for weeks_ago in range(WEEKS_BACK):
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday(), weeks=weeks_ago)
        html = fetch_html(food_url, monday)
        if not html:
            continue

        entries = parse_week(html, base_url)
        for e in entries:
            key = e['date']
            if key not in all_entries:
                all_entries[key] = e
            else:
                # 병합
                existing = all_entries[key]
                for m in e['menus']:
                    if m not in existing['menus']:
                        existing['menus'].append(m)
                for p in e['photos']:
                    if p not in existing['photos']:
                        existing['photos'].append(p)

    if not all_entries:
        return None

    # 사진 있는 날만 (메뉴만 있는 날은 제외)
    photo_entries = [e for e in all_entries.values() if e['photos']]
    if not photo_entries:
        return None

    photo_entries.sort(key=lambda x: x['date'], reverse=True)

    return {
        'school_name': row.get('school_name', ''),
        'school_type': row.get('school_type', ''),
        'location': row.get('location', ''),
        'homepage': base_url,
        'food_photo_url': food_url,
        'rank': int(row.get('rank', 0)),
        'entries': photo_entries,
    }


def main():
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base, 'school_photos_top100.csv')
    out_path = os.path.join(base, 'school_meal_photos.json')

    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    print(f'[1] {len(rows)}개교 로드')

    results = []
    done = 0

    with ThreadPoolExecutor(max_workers=15) as exe:
        futures = {exe.submit(scrape_school, r): r for r in rows}
        for fut in as_completed(futures):
            done += 1
            res = fut.result()
            if res:
                results.append(res)
            if done % 10 == 0:
                print(f'  {done}/{len(rows)} ... 사진 보유: {len(results)}교')

    results.sort(key=lambda x: x['rank'])

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_photos = sum(len(e['photos']) for s in results for e in s['entries'])
    total_entries = sum(len(s['entries']) for s in results)
    print(f'\n[완료] {len(results)}개교, {total_entries}일, 사진 {total_photos}장')
    print(f'저장: {out_path}')

    print('\n=== 샘플 ===')
    for school in results[:3]:
        print(f"\n{school['school_name']} ({school['school_type']})")
        for e in school['entries'][:2]:
            print(f"  {e['date']}: 사진 {len(e['photos'])}장, 메뉴 {len(e['menus'])}개")
            if e['photos']:
                print(f"    사진: {e['photos'][0]}")
            if e['menus']:
                print(f"    메뉴: {', '.join(e['menus'][:5])}")


if __name__ == '__main__':
    main()
