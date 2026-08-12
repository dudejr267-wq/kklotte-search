"""
냠냐미 9~10월 카탈로그에서 제품 썸네일 재추출.
(IMG_MAP 업데이트 후 실행)
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract_product_photos import extract_brand, update_photo_ids

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML     = os.path.join(BASE_DIR, '검색기.html')
OUT_DIR  = os.path.join(BASE_DIR, 'products_clean')

# 냠냐미 헤더/푸터 비율 (기본값: header=0.07, footer=0.03)
# 새 카탈로그 레이아웃 맞게 조정
import extract_product_photos as ep
ep.BRAND_CONFIG['냠냐미'] = {'header': 0.10, 'footer': 0.03}

saved = extract_brand('냠냐미', '냠냐미', HTML, BASE_DIR, OUT_DIR)
update_photo_ids(HTML, saved)

print(f"\n냠냐미 재추출 완료: {len(saved)}개")
