"""
카탈로그 페이지 이미지에서 제품별 썸네일을 추출하여 products_clean/ 에 저장.

전략:
  - 각 페이지를 "헤더를 제외한 제품 영역"으로 나눔
  - 페이지 위 N% = 헤더(브랜드명/제목), 아래 M% = 각주
  - 나머지를 N_products 등분 → 각 분할의 위 55%가 제품 사진 영역
  - 제품 순서는 IMG_MAP에 등장하는 순서(= 보통 페이지 내 위→아래, 좌→우)

레이아웃 설정 (brand, n_products) → (header_frac, footer_frac, grid_cols)
  * grid_cols=1 → 세로 등분
  * grid_cols>1 → 격자
"""

import re, os
from PIL import Image

# ── 브랜드별 헤더/푸터 비율 설정 ──────────────────────────────────────────
BRAND_CONFIG = {
    '자담선': {'header': 0.08, 'footer': 0.04},
    '코주부': {'header': 0.07, 'footer': 0.03},
    '단비':   {'header': 0.07, 'footer': 0.03},
    '맛샘':   {'header': 0.07, 'footer': 0.03},
}

# 페이지당 제품 수 → 격자(cols, rows) 추정
LAYOUT_COLS = {1:1, 2:1, 3:3, 4:2, 5:3, 6:3, 7:3, 8:3, 15:5}

def guess_layout(n_products):
    """제품 수에 따른 격자 cols 반환"""
    if n_products in LAYOUT_COLS:
        return LAYOUT_COLS[n_products]
    return 3  # 기본값

def crop_product(img, idx, total, header_frac, footer_frac, photo_frac=0.55):
    """
    img      : PIL Image (카탈로그 페이지)
    idx      : 이 페이지에서 몇 번째 제품인지 (0-based)
    total    : 이 페이지의 총 제품 수
    header_frac  : 상단 헤더 비율
    footer_frac  : 하단 각주 비율
    photo_frac   : 각 셀에서 제품 사진이 차지하는 비율 (위→아래)
    """
    W, H = img.size
    y_start = int(H * header_frac)
    y_end   = int(H * (1 - footer_frac))
    usable_h = y_end - y_start

    cols = guess_layout(total)
    rows = (total + cols - 1) // cols

    row = idx // cols
    col = idx % cols

    # 마지막 행의 실제 열 수(잔여 제품 수)
    last_row_count = total - (rows - 1) * cols
    actual_cols_in_row = last_row_count if row == (rows - 1) else cols

    cell_h = usable_h // rows
    cell_w = W // actual_cols_in_row

    x1 = col * cell_w
    x2 = (col + 1) * cell_w
    y1 = y_start + row * cell_h
    y2 = y1 + int(cell_h * photo_frac)   # 셀의 위 55%만 (제품 사진 영역)

    cropped = img.crop((x1, y1, x2, y2))

    # 400px 기준 리사이즈 (비율 유지)
    w, h = cropped.size
    if w > h:
        new_w, new_h = 400, int(400 * h / w)
    else:
        new_w, new_h = int(400 * w / h), 400
    return cropped.resize((new_w, new_h), Image.LANCZOS)


def parse_imgmap(html_path):
    """
    검색기.html의 IMG_MAP에서 {id: 이미지경로} 딕셔너리 반환.
    이미지 경로는 'images/브랜드명/images/page_XX.jpg' 형태.
    """
    with open(html_path, encoding='utf-8') as f:
        content = f.read()

    # 브랜드 변수명 → 실제 경로 추출
    # const JD = BASE + '자담선/images/';
    var_to_path = {}
    for m in re.finditer(r"const\s+([A-Z]+)\s*=\s*BASE\s*\+\s*'([^']+)'", content):
        var_to_path[m.group(1)] = 'images/' + m.group(2)

    # IMG_MAP 블록 추출
    imgmap_start = content.find('const IMG_MAP = {')
    imgmap_end   = content.find('};', imgmap_start) + 2
    imgmap_text  = content[imgmap_start:imgmap_end]

    id_to_path = {}
    # 패턴: 1219: JD + 'page_11.jpg',
    for m in re.finditer(r"(\d+)\s*:\s*([A-Z]+)\s*\+\s*['\"]([^'\"]+)['\"]", imgmap_text):
        pid      = int(m.group(1))
        var      = m.group(2)
        filename = m.group(3)
        if var in var_to_path:
            id_to_path[pid] = var_to_path[var] + filename
    return id_to_path


def build_page_to_ids(id_to_path, brand_folder):
    """
    특정 브랜드의 페이지 경로 → [제품 ID 목록] 딕셔너리 생성 (등장 순서 유지).
    """
    page_to_ids = {}
    for pid, path in sorted(id_to_path.items()):
        if f'/{brand_folder}/' in path or f'/{brand_folder}/' in path.replace('\\', '/'):
            page_to_ids.setdefault(path, []).append(pid)
    return page_to_ids


def extract_brand(brand_name, brand_folder, html_path, base_dir, out_dir, dry_run=False):
    print(f"\n{'='*50}")
    print(f"브랜드: {brand_name}  (폴더: {brand_folder})")
    print(f"{'='*50}")

    cfg = BRAND_CONFIG.get(brand_name, {'header': 0.07, 'footer': 0.03})
    id_to_path = parse_imgmap(html_path)
    page_to_ids = build_page_to_ids(id_to_path, brand_folder)

    saved = []

    for page_rel_path, ids in sorted(page_to_ids.items()):
        img_abs = os.path.join(base_dir, page_rel_path.replace('/', os.sep))
        if not os.path.exists(img_abs):
            print(f"  [없음] {page_rel_path}")
            continue

        img = Image.open(img_abs).convert('RGB')
        n = len(ids)

        for idx, pid in enumerate(ids):
            out_path = os.path.join(out_dir, f'{pid}.jpg')
            if os.path.exists(out_path):
                print(f"  [SKIP] {pid}.jpg 이미 존재")
                continue

            thumb = crop_product(img, idx, n, cfg['header'], cfg['footer'])
            if not dry_run:
                thumb.save(out_path, 'JPEG', quality=88)
            saved.append(pid)
            print(f"  [OK] {pid}.jpg  ← {os.path.basename(page_rel_path)} "
                  f"({idx+1}/{n}개, {thumb.size[0]}x{thumb.size[1]})")

    print(f"\n  → {len(saved)}개 저장 완료")
    return saved


def update_photo_ids(html_path, new_ids):
    """검색기.html의 PHOTO_IDS Set에 새 ID를 추가."""
    if not new_ids:
        return

    with open(html_path, encoding='utf-8') as f:
        content = f.read()

    # 현재 PHOTO_IDS 파싱
    m = re.search(r'const PHOTO_IDS = new Set\(\[([^\]]+)\]\)', content)
    if not m:
        print("PHOTO_IDS를 찾을 수 없습니다.")
        return

    existing = set(int(x) for x in re.findall(r'\d+', m.group(1)))
    added = [x for x in new_ids if x not in existing]
    if not added:
        print("PHOTO_IDS: 추가할 ID 없음 (이미 포함)")
        return

    all_ids = sorted(existing | set(added))
    new_set_str = ','.join(str(x) for x in all_ids)
    new_content = content[:m.start(1)] + new_set_str + content[m.end(1):]

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"\nPHOTO_IDS 갱신: {len(added)}개 추가 (총 {len(all_ids)}개)")


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    HTML     = os.path.join(BASE_DIR, '검색기.html')
    OUT_DIR  = os.path.join(BASE_DIR, 'products_clean')

    # 처리할 브랜드 목록: (브랜드명, 이미지 폴더명)
    BRANDS = [
        ('자담선', '자담선'),
        ('코주부', '코주부'),
        ('단비',   '단비'),
        ('맛샘',   '맛샘'),
    ]

    all_saved = []
    for brand_name, brand_folder in BRANDS:
        saved = extract_brand(brand_name, brand_folder, HTML, BASE_DIR, OUT_DIR)
        all_saved.extend(saved)

    update_photo_ids(HTML, all_saved)
    print(f"\n전체 {len(all_saved)}개 제품 사진 추출 완료!")
