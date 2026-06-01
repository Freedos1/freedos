@echo off
echo.
echo  ====================================
echo   FREEDOS - Transport et Logistique
echo  ====================================
echo.
echo  Demarrage du serveur...
echo  Ouvrez votre navigateur sur : http://localhost:8000
echo.
cd /d "%~dp0backend"
C:\Users\fredk\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
