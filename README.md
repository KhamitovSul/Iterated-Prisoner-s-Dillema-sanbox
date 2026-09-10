# Axelrod Lab

Локальное веб-приложение для экспериментов с повторяющейся дилеммой заключённого. Сервер на FastAPI запускает турниры и матчи с библиотекой `Axelrod-Python`, а интерфейс находится в `static/`. База данных и отдельный фронтенд-сборщик не требуются.

## Требования

- Python 3.10–3.13 с доступной в терминале командой `python`;
- PowerShell (инструкции ниже рассчитаны на Windows).

Проверить Python можно командой:

```powershell
python --version
```

Если команда не найдена, установите Python с [python.org](https://www.python.org/downloads/windows/) и включите опцию **Add Python to PATH**. Затем закройте и заново откройте PowerShell.

## Быстрый запуск

Из корневой папки проекта выполните:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Когда в терминале появится строка `Uvicorn running on http://127.0.0.1:8000`, откройте в браузере:

<http://127.0.0.1:8000>

Не открывайте `static/index.html` двойным щелчком: браузер не сможет корректно обратиться к API.

Чтобы остановить сервер, нажмите `Ctrl+C`. При следующем запуске достаточно активировать окружение и запустить сервер:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

## Если PowerShell блокирует активацию

Активация не обязательна. Выполните команды, явно используя Python из окружения:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

## Вариант с Live Server

Интерфейс также можно открыть через расширение Live Server по адресу `http://127.0.0.1:5500`: сервер разрешает этот источник. Но API FastAPI всё равно должен быть запущен на `http://127.0.0.1:8000`, потому что `static/app.js` обращается именно к этому адресу.

## Возможности

- каталог встроенных стратегий `Axelrod-Python` с поиском;
- круговой турнир между 2–8 стратегиями;
- настройка ходов (5–500), повторений (1–100) и шума (0–30 %);
- рейтинг по суммарному счёту и отдельный матч с историей раундов.

## Структура

```text
main.py          FastAPI-приложение и API симуляций
requirements.txt Зависимости Python
static/          HTML, CSS и JavaScript интерфейса
```
