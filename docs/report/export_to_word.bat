@echo off
chcp 65001 > nul
echo ================================================
echo  Xuat Bao Cao Phan Tich Du Lieu sang Word (.docx)
echo ================================================
echo.

REM Chay Python script de xuat docx

echo [1/2] Dang chuyen doi Markdown sang Word bang Python script...
python docs\report\markdown_to_docx.py 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [2/2] Xuat thanh cong!
    echo Output: docs\report\Bao_Cao_Phan_Tich_Du_Lieu_Nhom2.docx
) else (
    echo [ERROR] Xuat that bai! Kiem tra moi truong python.
)

echo.
pause
