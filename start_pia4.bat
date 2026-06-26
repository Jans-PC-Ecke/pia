@echo off
cd /d "%~dp0"
call .\pia4_venv\Scripts\activate
python pia4.py
pause