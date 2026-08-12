"""
제품 이미지 감사 페이지 생성기
검색기.html에서 PRODUCTS와 PHOTO_IDS를 추출하여
모든 제품 사진을 브랜드별로 나열한 audit.html을 생성합니다.
"""

import re, json, os

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), '검색기.html')

with open(HTML, encoding='utf-8') as f:
    src = f.read()

# ── PRODUCTS 추출 ──────────────────────────────────────────────
products_start = src.find('const PRODUCTS = [') + len('const PRODUCTS = [')
# 닫는 ];를 찾기 위해 브라켓 카운팅
depth = 1
i = products_start
while i < len(src) and depth > 0:
    if src[i] == '[': depth += 1
    elif src[i] == ']': depth -= 1
    i += 1
products_raw = src[products_start:i-1]

# 각 객체를 파싱 (정규식으로 id와 name, brand 추출)
products = []
for m in re.finditer(
    r'\{\s*id\s*:\s*(\d+)\s*,\s*name\s*:\s*"([^"]+)"\s*,\s*brand\s*:\s*"([^"]+)"',
    products_raw
):
    products.append({
        'id': int(m.group(1)),
        'name': m.group(2),
        'brand': m.group(3),
    })

print(f"제품 수: {len(products)}")

# ── PHOTO_IDS 추출 ─────────────────────────────────────────────
m = re.search(r'const PHOTO_IDS = new Set\(\[([^\]]+)', src, re.DOTALL)
photo_ids = set(int(x) for x in re.findall(r'\d+', m.group(1))) if m else set()
print(f"PHOTO_IDS 수: {len(photo_ids)}")

# products_clean 폴더에 실제 있는 파일
clean_dir = os.path.join(os.path.dirname(HTML), 'products_clean')
actual_files = set(
    int(f.replace('.jpg',''))
    for f in os.listdir(clean_dir) if f.endswith('.jpg') and f.replace('.jpg','').isdigit()
)
print(f"실제 이미지 파일 수: {len(actual_files)}")

# 화이트리스트 & 실제 파일 모두 있는 것만
has_photo = photo_ids & actual_files

# ── 브랜드별 그룹화 ────────────────────────────────────────────
brands = {}
for p in products:
    if p['id'] in has_photo:
        brands.setdefault(p['brand'], []).append(p)

# ── HTML 생성 ──────────────────────────────────────────────────
cards_html = ''
for brand, items in brands.items():
    cards_html += f'<h2 class="brand-title">{brand} ({len(items)})</h2>\n<div class="grid">\n'
    for p in sorted(items, key=lambda x: x['id']):
        cards_html += f'''  <div class="card">
    <img src="products_clean/{p['id']}.jpg" loading="lazy" onerror="this.style.background='#f88'">
    <div class="info">
      <span class="id">#{p['id']}</span>
      <span class="name">{p['name']}</span>
    </div>
  </div>\n'''
    cards_html += '</div>\n'

html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>제품 사진 감사 | 경기롯데</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif; background:#f5f5f5; padding:20px; }}
h1 {{ font-size:22px; color:#333; margin-bottom:20px; }}
.brand-title {{ font-size:17px; font-weight:700; color:#D85A30; margin:28px 0 10px;
  border-left:4px solid #D85A30; padding-left:10px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:10px; }}
.card {{ background:#fff; border-radius:10px; overflow:hidden; border:1px solid #eee;
  box-shadow:0 1px 4px rgba(0,0,0,.08); }}
.card img {{ width:100%; height:120px; object-fit:cover; background:#eee; display:block; }}
.info {{ padding:8px; }}
.id {{ font-size:10px; color:#aaa; margin-right:4px; }}
.name {{ font-size:11px; color:#333; font-weight:600; line-height:1.4; }}
p.count {{ color:#666; font-size:13px; margin-bottom:8px; }}
</style>
</head>
<body>
<h1>📸 제품 사진 감사 — 총 {len(has_photo)}개</h1>
<p class="count">이름과 사진이 다른 카드를 찾아 ID를 알려주세요.</p>
{cards_html}
</body>
</html>"""

out = os.path.join(os.path.dirname(HTML), 'audit.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\naudit.html 생성 완료: {out}")
