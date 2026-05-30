@echo off
chcp 65001 >nul
title Запуск приложений LZ77 и RSA

echo ================================================
echo   Запуск приложений LZ77 и RSA
echo ================================================
echo.

REM Проверка наличия Python
echo [1/4] Проверка Python...
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [ОШИБКА] Python не установлен!
        echo Скачайте его с сайта: https://www.python.org/downloads/
        echo При установке отметьте галочку "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py
)
echo Python найден.
echo.

REM Обновление pip
echo [2/4] Обновление pip...
%PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
echo Готово.
echo.

REM Установка зависимостей
echo [3/4] Установка библиотек (streamlit, pandas)...
%PYTHON_CMD% -m pip install streamlit pandas
if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось установить библиотеки!
    pause
    exit /b 1
)
echo Готово.
echo.

REM Запуск приложений
echo [4/4] Запуск приложений...
echo.
echo Приложение LZ77 будет доступно по адресу: http://localhost:8501
echo Приложение RSA  будет доступно по адресу: http://localhost:8502
echo.
echo Для остановки приложений закройте открывшиеся окна терминала.
echo.

start "LZ77 - http://localhost:8501" cmd /k "%PYTHON_CMD% -m streamlit run app1.py --server.port 8501"
timeout /t 3 /nobreak >nul
start "RSA - http://localhost:8502" cmd /k "%PYTHON_CMD% -m streamlit run app2.py --server.port 8502"

timeout /t 5 /nobreak >nul

REM Открытие браузера
start http://localhost:8501
timeout /t 2 /nobreak >nul
start http://localhost:8502

echo.
echo ================================================
echo   Приложения запущены!
echo ================================================
echo.
echo Это окно можно закрыть.
echo.
pause