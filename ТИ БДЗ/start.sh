#!/bin/bash

echo "================================================"
echo "  Запуск приложений LZ77 и RSA"
echo "================================================"
echo

# Проверка Python
echo "[1/4] Проверка Python..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo
    echo "[ОШИБКА] Python не установлен!"
    echo "Установите его командой:"
    echo "  sudo apt install python3 python3-pip   (Ubuntu/Debian)"
    echo "  brew install python                    (macOS)"
    echo
    exit 1
fi
echo "Python найден."
echo

# Обновление pip
echo "[2/4] Обновление pip..."
$PYTHON_CMD -m pip install --upgrade pip >/dev/null 2>&1
echo "Готово."
echo

# Установка зависимостей
echo "[3/4] Установка библиотек (streamlit, pandas)..."
$PYTHON_CMD -m pip install streamlit pandas
if [ $? -ne 0 ]; then
    echo
    echo "[ОШИБКА] Не удалось установить библиотеки!"
    exit 1
fi
echo "Готово."
echo

# Запуск приложений
echo "[4/4] Запуск приложений..."
echo
echo "Приложение LZ77 будет доступно по адресу: http://localhost:8501"
echo "Приложение RSA  будет доступно по адресу: http://localhost:8502"
echo

$PYTHON_CMD -m streamlit run app1.py --server.port 8501 &
APP1_PID=$!
sleep 3

$PYTHON_CMD -m streamlit run app2.py --server.port 8502 &
APP2_PID=$!
sleep 5

# Открытие браузера
if command -v xdg-open &>/dev/null; then
    xdg-open http://localhost:8501
    sleep 2
    xdg-open http://localhost:8502
elif command -v open &>/dev/null; then
    open http://localhost:8501
    sleep 2
    open http://localhost:8502
fi

echo
echo "================================================"
echo "  Приложения запущены!"
echo "================================================"
echo
echo "Для остановки нажмите Ctrl+C"
echo

# Ожидание завершения
wait $APP1_PID $APP2_PID