import re

with open("검색기.html", encoding="utf-8") as f:
    content = f.read()

# Find PRODUCTS array
prod_start = content.find("const PRODUCTS = [")
prod_end = content.find("];", prod_start) + 2
products_text = content[prod_start:prod_end]

# Count 자담선 brands
jadamsun_count = products_text.count('brand:"자담선"')
print(f"자담선 brand 항목 수: {jadamsun_count}")

# Check all brand names
brand_pattern = re.compile(r'brand:"([^"]+)"')
brands = {}
for m in brand_pattern.finditer(products_text):
    b = m.group(1)
    brands[b] = brands.get(b, 0) + 1

print("\n=== 브랜드별 제품 수 ===")
for brand, count in sorted(brands.items(), key=lambda x: -x[1]):
    print(f"  {brand}: {count}개")

# Check 자담선 ID range
id_pattern = re.compile(r'\{ id:(\d+).*?brand:"자담선"')
jadamsun_ids = [int(m.group(1)) for m in id_pattern.finditer(products_text)]
if jadamsun_ids:
    print(f"\n자담선 ID 범위: {min(jadamsun_ids)} ~ {max(jadamsun_ids)}")
    print(f"자담선 ID 목록 (처음 10개): {jadamsun_ids[:10]}")
    print(f"자담선 ID 목록 (마지막 10개): {jadamsun_ids[-10:]}")
