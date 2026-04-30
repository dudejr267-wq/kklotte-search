@echo off
chcp 65001 >nul
title 경기롯데 PDF 변환기

echo.
echo  PyMuPDF 설치 확인 중...
python -c "import fitz" 2>nul
if errorlevel 1 (
    echo  PyMuPDF 설치 중... 잠깐만요!
    pip install pymupdf -q
)

echo.
python "%~dp0pdf_to_images.py"
