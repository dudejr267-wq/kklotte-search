"""9~10월 신규 PDF를 이미지로 일괄 변환."""
import os
from pdf2image import convert_from_path

POPPLER = r'C:\poppler\Library\bin'
BASE    = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE, 'images')

# (브랜드폴더, PDF상대경로, 시작페이지번호)
# 시작페이지번호: 기존 이미지가 있으면 다음 번호부터 추가
PDFS = [
    ('달담',      '달담 9월행사지.pdf',                         1),
    ('맛샘',      r'PDF_완료\(맛샘)26년 9~10월 행사지.pdf',    1),
    ('면사랑',    '9월면사랑홍보지.pdf',                        1),
    ('세미원',    '세미원9행사지.pdf',                          1),
    ('슬로우메이드', '더슬로우메이드26년 9월 행사지.pdf',        1),
    ('식탁요정',  r'PDF_완료\식탁요정카달로그_2026.2학기.pdf',  1),
    ('아워밀(설빙)', r'PDF_완료\아워밀 9월 행사지(all).pdf',   1),
    ('어니스트',  '어니스트9월행사지.pdf',                      1),
    ('올바른',    r'PDF_완료\올바른 26년도 9월 홍보지 출력용.pdf', 1),
    ('웅진',      '웅진9월행사지.pdf',                          1),
]

total_ok = 0
for brand, rel_pdf, start_page in PDFS:
    pdf_path    = os.path.join(IMAGES_DIR, brand, rel_pdf)
    out_dir     = os.path.join(IMAGES_DIR, brand, 'images')
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(pdf_path):
        print(f'[SKIP] {brand}: PDF 없음 ({rel_pdf})')
        continue

    existing = [f for f in os.listdir(out_dir) if f.startswith('page_') and f.endswith('.jpg')]
    if existing:
        # 기존 이미지가 있으면 번호를 이어서 추가
        max_num = max(int(f[5:7]) for f in existing)
        start_page = max_num + 1

    print(f'\n[{brand}] 변환 중... (시작 페이지: {start_page})')
    try:
        pages = convert_from_path(pdf_path, dpi=150, poppler_path=POPPLER)
        for i, page in enumerate(pages, start_page):
            out_path = os.path.join(out_dir, f'page_{i:02d}.jpg')
            page.save(out_path, 'JPEG', quality=85)
        print(f'  -> {len(pages)}페이지 완료 (page_{start_page:02d}~page_{start_page+len(pages)-1:02d})')
        total_ok += 1
    except Exception as e:
        print(f'  [오류] {e}')

print(f'\n=== 완료: {total_ok}/{len(PDFS)}개 브랜드 변환 ===')
