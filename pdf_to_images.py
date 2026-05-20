import os
import sys
import subprocess
import shutil

# =============================================
# 브랜드별 폴더명 매핑
# PDF 파일명에 아래 키워드가 포함되면 해당 폴더에 저장
# =============================================
BRAND_MAP = {
    '올바른': '올바른',
    '냠냐미': '냠냐미',
    '안심찬': '안심찬',
    '아워밀': '아워밀(설빙)',
    '설빙':   '아워밀(설빙)',
}

def find_pdf_files(base_dir):
    """현재 폴더에서 PDF 파일 찾기"""
    pdfs = []
    for f in os.listdir(base_dir):
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(base_dir, f))
    return pdfs

def detect_brand(filename):
    """파일명으로 브랜드 감지"""
    for keyword, folder in BRAND_MAP.items():
        if keyword in filename:
            return folder
    return None

def convert_pdf(pdf_path, output_folder):
    """PDF를 JPG 이미지로 변환"""
    # 기존 이미지 삭제
    if os.path.exists(output_folder):
        for f in os.listdir(output_folder):
            if f.lower().endswith(('.jpg', '.png')):
                os.remove(os.path.join(output_folder, f))
        print(f"  기존 이미지 삭제 완료")
    else:
        os.makedirs(output_folder)
        print(f"  폴더 생성: {output_folder}")

    # pdftoppm으로 변환 시도
    prefix = os.path.join(output_folder, 'page')
    try:
        result = subprocess.run(
            ['pdftoppm', '-jpeg', '-r', '150', pdf_path, prefix],
            capture_output=True, text=True
        )
        # 파일 확인
        images = [f for f in os.listdir(output_folder) if f.endswith('.jpg')]
        if images:
            # page-01.jpg → page_01.jpg 형식으로 rename
            for img in images:
                if '-' in img:
                    new_name = img.replace('page-', 'page_')
                    os.rename(
                        os.path.join(output_folder, img),
                        os.path.join(output_folder, new_name)
                    )
            images = sorted([f for f in os.listdir(output_folder) if f.endswith('.jpg')])
            print(f"  변환 완료: {len(images)}페이지")
            return len(images)
    except FileNotFoundError:
        pass

    # pdf2image (pillow) 시도
    try:
        from pdf2image import convert_from_path
        print("  pdf2image로 변환 중...")
        pages = convert_from_path(pdf_path, dpi=150)
        for i, page in enumerate(pages, 1):
            out_path = os.path.join(output_folder, f'page_{i:02d}.jpg')
            page.save(out_path, 'JPEG', quality=85)
        print(f"  변환 완료: {len(pages)}페이지")
        return len(pages)
    except ImportError:
        pass

    print("  ❌ 변환 실패: pdftoppm 또는 pdf2image가 필요합니다.")
    print("  pip install pdf2image 를 실행해보세요.")
    return 0

def main():
    # 스크립트가 있는 폴더 = kklotte_homepage
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, 'images')

    print("=" * 50)
    print("경기롯데 PDF → 이미지 변환기")
    print("=" * 50)

    pdf_files = find_pdf_files(base_dir)

    if not pdf_files:
        print("\n❌ PDF 파일을 찾을 수 없습니다.")
        print(f"   이 폴더에 PDF를 넣어주세요: {base_dir}")
        input("\n엔터를 누르면 종료됩니다...")
        return

    print(f"\n📄 PDF 파일 {len(pdf_files)}개 발견:")
    for pdf in pdf_files:
        print(f"   - {os.path.basename(pdf)}")

    print()
    success = 0
    skipped = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        brand_folder = detect_brand(filename)

        if not brand_folder:
            print(f"⚠️  [{filename}] 브랜드를 인식할 수 없습니다. 건너뜁니다.")
            print(f"   파일명에 브랜드명을 포함해주세요: 올바른, 냠냐미, 안심찬, 아워밀, 설빙")
            skipped += 1
            continue

        output_folder = os.path.join(images_dir, brand_folder)
        print(f"🔄 [{filename}]")
        print(f"   브랜드: {brand_folder} → images/{brand_folder}/")

        count = convert_pdf(pdf_path, output_folder)
        if count > 0:
            success += 1
            # 변환 완료된 PDF는 done 폴더로 이동
            done_dir = os.path.join(base_dir, 'PDF_완료')
            os.makedirs(done_dir, exist_ok=True)
            shutil.move(pdf_path, os.path.join(done_dir, filename))
            print(f"  📁 PDF는 'PDF_완료' 폴더로 이동됨")
        print()

    print("=" * 50)
    print(f"완료: {success}개 성공 / {skipped}개 건너뜀")
    if success > 0:
        print("\n✅ 이미지 변환 완료!")
        print("   검색기.html을 열면 새 홍보지가 바로 보입니다.")
    print("=" * 50)
    input("\n엔터를 누르면 종료됩니다...")

if __name__ == '__main__':
    main()
