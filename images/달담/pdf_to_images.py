import os
import sys
import subprocess
import shutil

BRAND_MAP = {
    '올바른': '올바른',
    '냠냐미': '냠냐미',
    '안심찬': '안심찬',
    '아워밀': '아워밀(설빙)',
    '설빙':   '아워밀(설빙)',
    '맛샘':   '맛샘',
    '식탁요정': '식탁요정',
}

POPPLER_PATHS = [
    r'C:\poppler\Library\bin',
    r'C:\poppler\bin',
    r'C:\Program Files\poppler\bin',
    r'C:\Program Files (x86)\poppler\bin',
]

def get_poppler_path():
    for path in POPPLER_PATHS:
        if os.path.exists(path):
            return path
    return None

def install_pdf2image():
    print("  pdf2image 설치 중...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pdf2image', 'pillow'],
                   capture_output=True)

def find_pdf_files(base_dir):
    pdfs = []
    for f in os.listdir(base_dir):
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(base_dir, f))
    return pdfs

def detect_brand(filename):
    for keyword, folder in BRAND_MAP.items():
        if keyword in filename:
            return folder
    return None

def convert_pdf(pdf_path, output_folder, poppler_path):
    if os.path.exists(output_folder):
        for f in os.listdir(output_folder):
            if f.lower().endswith(('.jpg', '.png')):
                os.remove(os.path.join(output_folder, f))
        print("  기존 이미지 삭제 완료")
    else:
        os.makedirs(output_folder)
        print("  폴더 생성 완료")

    try:
        from pdf2image import convert_from_path
    except ImportError:
        install_pdf2image()
        try:
            from pdf2image import convert_from_path
        except ImportError:
            print("  pdf2image 설치 실패.")
            return 0

    try:
        print("  변환 중... (잠시 기다려주세요)")
        pages = convert_from_path(pdf_path, dpi=150, poppler_path=poppler_path)
        for i, page in enumerate(pages, 1):
            out_path = os.path.join(output_folder, f'page_{i:02d}.jpg')
            page.save(out_path, 'JPEG', quality=85)
        print(f"  변환 완료: {len(pages)}페이지")
        return len(pages)
    except Exception as e:
        print(f"  변환 오류: {e}")
        return 0

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, 'images')

    print("=" * 50)
    print("경기롯데 PDF → 이미지 변환기")
    print("=" * 50)

    poppler_path = get_poppler_path()
    if poppler_path:
        print(f"  poppler: {poppler_path}")
    else:
        print("\n  poppler를 찾을 수 없습니다.")
        input("엔터를 누르면 종료됩니다...")
        return

    pdf_files = find_pdf_files(base_dir)

    if not pdf_files:
        print("\n  PDF 파일을 찾을 수 없습니다.")
        input("\n엔터를 누르면 종료됩니다...")
        return

    print(f"\n  PDF 파일 {len(pdf_files)}개 발견:")
    for pdf in pdf_files:
        print(f"   - {os.path.basename(pdf)}")
    print()

    success = 0
    skipped = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        brand_folder = detect_brand(filename)

        # 브랜드 인식 못하면 직접 입력받기
        if not brand_folder:
            print(f"  [{filename}]")
            print(f"  브랜드를 자동으로 인식하지 못했습니다.")
            print(f"  현재 등록된 브랜드: {', '.join(BRAND_MAP.values())}")
            brand_input = input("  저장할 브랜드 폴더명을 입력하세요 (건너뛰려면 엔터): ").strip()
            if not brand_input:
                print("  건너뜁니다.\n")
                skipped += 1
                continue
            brand_folder = brand_input

        output_folder = os.path.join(images_dir, brand_folder, 'images')

        print(f"[{filename}]")
        print(f"  브랜드: {brand_folder}")
        print(f"  저장위치: images\\{brand_folder}\\images\\")

        count = convert_pdf(pdf_path, output_folder, poppler_path)
        if count > 0:
            success += 1
            done_dir = os.path.join(base_dir, 'PDF_완료')
            os.makedirs(done_dir, exist_ok=True)
            shutil.move(pdf_path, os.path.join(done_dir, filename))
            print(f"  PDF → 'PDF_완료' 폴더로 이동")
        print()

    print("=" * 50)
    print(f"완료: {success}개 성공 / {skipped}개 건너뜀")
    if success > 0:
        print("\n  변환 완료! 검색기.html을 열면 새 홍보지가 보입니다.")
    print("=" * 50)
    input("\n엔터를 누르면 종료됩니다...")

if __name__ == '__main__':
    main()
