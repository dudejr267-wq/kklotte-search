import re

with open("검색기.html", encoding="utf-8") as f:
    content = f.read()

# Extract IMG_MAP entries
imgmap_start = content.find("const IMG_MAP = {")
imgmap_end = content.find("};", imgmap_start) + 2
imgmap_text = content[imgmap_start:imgmap_end]

# Find all numeric key: value pairs
mapped_ids = set()
for m in re.finditer(r'(\d+)\s*:', imgmap_text):
    mapped_ids.add(int(m.group(1)))

# Find all 자담선 product IDs from PRODUCTS array
prod_start = content.find("const PRODUCTS = [")
prod_end = content.find("];", prod_start) + 2
products_text = content[prod_start:prod_end]

jadamsun_ids = []
for m in re.finditer(r'\{ id:(\d+)[^}]*brand:"자담선"', products_text):
    jadamsun_ids.append(int(m.group(1)))

jadamsun_ids.sort()
print(f"자담선 제품 수: {len(jadamsun_ids)}개")
print(f"자담선 ID 범위: {min(jadamsun_ids)} ~ {max(jadamsun_ids)}")

# Check which ones have IMG_MAP entry
with_img = [id for id in jadamsun_ids if id in mapped_ids]
without_img = [id for id in jadamsun_ids if id not in mapped_ids]

print(f"\nIMG_MAP 있는 자담선 제품: {len(with_img)}개")
print(f"IMG_MAP 없는 자담선 제품: {len(without_img)}개")
if without_img:
    print(f"  없는 ID들: {without_img}")
else:
    print("  ✅ 자담선 전체 IMG_MAP 연결 완료!")

# Also check PHOTO_IDS
photo_start = content.find("const PHOTO_IDS = new Set([")
photo_end = content.find("]);", photo_start) + 3
photo_text = content[photo_start:photo_end]
photo_ids = set(int(x) for x in re.findall(r'\d+', photo_text))

with_photo = [id for id in jadamsun_ids if id in photo_ids]
print(f"\nPHOTO_IDS(개별 사진) 있는 자담선: {len(with_photo)}개")
if not with_photo:
    print("  ⚠️  자담선 개별 제품 사진 없음 (이모지로만 표시됨)")
