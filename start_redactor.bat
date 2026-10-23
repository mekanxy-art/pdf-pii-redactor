@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 goto folder_error

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" start_redactor.py %*
  goto finished
)
py -3.12 -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if not errorlevel 1 (
  py -3.12 start_redactor.py %*
  goto finished
)
python -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if not errorlevel 1 (
  python start_redactor.py %*
  goto finished
)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
  "%LocalAppData%\Programs\Python\Python312\python.exe" start_redactor.py %*
  goto finished
)
echo Python 3.12 wurde nicht gefunden.
echo Bitte Python 3.12 installieren und danach diese Datei erneut starten.
echo Das gesamte ZIP muss vorher entpackt sein.
pause
exit /b 1

:folder_error
echo Der Projektordner konnte nicht geoeffnet werden.
echo Bitte das gesamte ZIP zuerst entpacken.
pause
exit /b 1

:finished
set "REDACTOR_EXIT=%ERRORLEVEL%"
if not "%REDACTOR_EXIT%"=="0" (
  echo.
  echo Der Start ist fehlgeschlagen. Die genaue Meldung steht oben.
  pause
)
exit /b %REDACTOR_EXIT%
