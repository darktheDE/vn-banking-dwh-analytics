@echo off
chcp 65001 > nul
echo ================================================
echo  Xuat Bao Cao Phan Tich Du Lieu sang Word (.docx)
echo ================================================
echo.

REM Check pandoc
where pandoc > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pandoc chua duoc cai dat!
    echo Tai ve tai: https://pandoc.org/installing.html
    pause
    exit /b 1
)

echo [1/2] Dang chuyen doi Markdown sang Word...
pandoc ^
  docs\report\Bao_Cao_Phan_Tich_Du_Lieu_Nhom2.md ^
  --from markdown ^
  --to docx ^
  --output "docs\report\Bao_Cao_Phan_Tich_Du_Lieu_Nhom2.docx" ^
  --resource-path "docs\report" ^
  --standalone ^
  --toc ^
  --toc-depth=3 ^
  --number-sections ^
  -V lang=vi ^
  -V fontsize=13pt ^
  -V linestretch=1.5 ^
  2>&1

if %ERRORLEVEL% EQU 0 (
    echo [2/2] Xuat thanh cong!
    echo Output: docs\report\Bao_Cao_Phan_Tich_Du_Lieu_Nhom2.docx
) else (
    echo [ERROR] Xuat that bai! Xem log o tren.
)

echo.
pause
