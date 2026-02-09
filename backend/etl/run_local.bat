@echo off

REM ===== PROJECT ROOT =====
cd /d "C:\Users\Admin\Documents\Global finance project"

REM ===== PYTHON (PYTHON VENV) =====
set PYTHON_EXE="C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" ^
"C:\Users\Admin\Documents\Global finance project\backend\etl\run_local.py"

REM ===== LOG =====
set LOG_FILE="backend\etl\run_local.log"

echo =============================== >> %LOG_FILE%
echo Running local ETL at %DATE% %TIME% >> %LOG_FILE%

REM ===== RUN =====
%PYTHON_EXE% "backend\etl\run_local.py" >> %LOG_FILE% 2>&1

echo Finished at %DATE% %TIME% >> %LOG_FILE%