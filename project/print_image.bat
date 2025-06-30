@echo off
echo Hello

:: Use Windows Photo Viewer to print image (legacy)
rundll32.exe %SystemRoot%\System32\shimgvw.dll,ImageView_PrintTo "1.jpg" "Microsoft Print to PDF"

pause
