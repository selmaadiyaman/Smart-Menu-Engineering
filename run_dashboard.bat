@echo off
cd /d "C:\Users\lenovo\OneDrive\Masaüstü\SmartMenuEng"

:: Dash scripti başlat
start "" python dashboard1.py

:: Varsayılan tarayıcıda Dash URL'sini aç
start "" http://127.0.0.1:8050/

pause
