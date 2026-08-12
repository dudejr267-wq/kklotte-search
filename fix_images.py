"""
잘못된 제품 이미지(가격표/문구 표시) 정리 스크립트:
1. 잘못된 이미지 파일 삭제 (products_clean/)
2. PHOTO_IDS에서 해당 IDs 제거
"""

import re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML     = os.path.join(BASE_DIR, '검색기.html')
OUT_DIR  = os.path.join(BASE_DIR, 'products_clean')

# 가격표/문구를 보여주는 잘못된 이미지 IDs
WRONG_IDS = [
    # 냠냐미 (IMG_MAP 업데이트 후 재추출 예정)
    4, 8, 16, 24, 46, 52, 56, 60, 65, 66, 76, 81, 85, 87, 89, 90,
    # 올바른 (가격표 표시)
    128, 131, 132, 133, 138, 139,
    # 아워밀/설빙 (가격표 표시)
    213, 214, 216, 220, 221, 232, 257,
]

# ── 1. 파일 삭제 ────────────────────────────────────────────────
print("=== 잘못된 이미지 파일 삭제 ===")
deleted = []
for pid in WRONG_IDS:
    path = os.path.join(OUT_DIR, f'{pid}.jpg')
    if os.path.exists(path):
        os.remove(path)
        deleted.append(pid)
        print(f"  [삭제] {pid}.jpg")
    else:
        print(f"  [없음] {pid}.jpg")
print(f"\n  → {len(deleted)}개 삭제 완료")

# ── 2. PHOTO_IDS 갱신 ───────────────────────────────────────────
print("\n=== PHOTO_IDS 갱신 ===")
with open(HTML, encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const PHOTO_IDS = new Set\(\[([^\]]+)\]\)', content)
if not m:
    print("PHOTO_IDS를 찾을 수 없습니다.")
    raise SystemExit(1)

existing  = set(int(x) for x in re.findall(r'\d+', m.group(1)))
to_remove = set(WRONG_IDS)
remaining = sorted(existing - to_remove)

new_set_str = ','.join(str(x) for x in remaining)
new_content = content[:m.start(1)] + new_set_str + content[m.end(1):]

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"  {len(existing & to_remove)}개 ID 제거 완료")
print(f"  PHOTO_IDS 총 {len(remaining)}개 → {len(remaining)}개")
print("\n완료!")
print("다음 단계: extract_nyam.py 실행하여 냠냐미 이미지 재추출")
