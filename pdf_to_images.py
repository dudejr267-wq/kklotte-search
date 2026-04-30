"""
경기롯데 상품검색 - PDF 이미지 변환 스크립트
----------------------------------------------
사용법:
  1. 이 파일을 kklotte_homepage 폴더 안에 넣어두세요
  2. 변환할 PDF를 해당 브랜드 폴더에 넣으세요
  3. 이 스크립트를 더블클릭(또는 run_pdf_converter.bat 실행)하면 됩니다

폴더 구조 예시:
  kklotte_homepage/
    ├── 검색기.html
    ├── pdf_to_images.py        ← 이 파일
    ├── run_pdf_converter.bat   ← 더블클릭용
    └── images/
          ├── 아워밀설빙/
          │     └── 아워밀_68월_행사지all.pdf  ← PDF 여기에
          ├── 냠냐미/
          ├── 안심찬/
          └── 올바른/
"""

import os
import sys

def convert_pdf_to_images(pdf_path, output_folder, dpi=150):
    """PDF 각 페이지를 JPG로 변환"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("=" * 50)
        print("  PyMuPDF가 설치되어 있지 않습니다.")
        print("  아래 명령어를 실행해주세요:")
        print("  pip install pymupdf")
        print("=" * 50)
        input("\n엔터를 눌러 종료...")
        return False

    doc = fitz.open(pdf_path)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    save_folder = os.path.join(output_folder, pdf_name)
    os.makedirs(save_folder, exist_ok=True)

    total = len(doc)
    print(f"  📄 총 {total}페이지 변환 시작...")

    for i, page in enumerate(doc):
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        out_path = os.path.join(save_folder, f"page_{i+1:02d}.jpg")
        pix.save(out_path)
        kb = os.path.getsize(out_path) // 1024
        print(f"    ✅ page_{i+1:02d}.jpg ({kb}KB)")

    doc.close()
    print(f"  🎉 완료! '{save_folder}' 에 저장됨\n")
    return True


def main():
    # 스크립트 위치 기준으로 images 폴더 찾기
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "images")

    print("=" * 55)
    print("   경기롯데 PDF → 이미지 변환기")
    print("=" * 55)

    if not os.path.exists(images_dir):
        print(f"\n  ⚠️  images 폴더가 없습니다.")
        print(f"  아래 경로에 만들어주세요:\n  {images_dir}")
        input("\n엔터를 눌러 종료...")
        return

    # images 폴더 안의 모든 브랜드 폴더 순회
    found_pdfs = []
    for brand_folder in os.listdir(images_dir):
        brand_path = os.path.join(images_dir, brand_folder)
        if not os.path.isdir(brand_path):
            continue
        for file in os.listdir(brand_path):
            if file.lower().endswith(".pdf"):
                found_pdfs.append((brand_folder, os.path.join(brand_path, file), brand_path))

    if not found_pdfs:
        print("\n  ⚠️  변환할 PDF 파일을 찾지 못했습니다.")
        print("  images/브랜드폴더/ 안에 PDF를 넣어주세요.")
        print(f"\n  현재 images 폴더: {images_dir}")
        input("\n엔터를 눌러 종료...")
        return

    print(f"\n  📂 PDF {len(found_pdfs)}개 발견:\n")
    for brand, pdf_path, _ in found_pdfs:
        print(f"    [{brand}] {os.path.basename(pdf_path)}")

    print("\n  변환을 시작합니다...\n")

    for brand, pdf_path, brand_path in found_pdfs:
        print(f"▶ [{brand}] {os.path.basename(pdf_path)}")
        convert_pdf_to_images(pdf_path, brand_path, dpi=150)

    print("=" * 55)
    print("  ✅ 모든 변환 완료!")
    print("  이미지가 각 브랜드 폴더 안에 저장됐습니다.")
    print("=" * 55)
    input("\n엔터를 눌러 종료...")


if __name__ == "__main__":
    main()
