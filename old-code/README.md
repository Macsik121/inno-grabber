# Innovation Campus Materials Downloader

Автоматическая загрузка материалов с платформы innovationcampus.ru через Selenium WebDriver.

## Описание

Скрипт открывает браузер Chrome, позволяет вручную авторизоваться на платформе, затем автоматически скачивает все PDF-материалы из списка URL.

## Требования

- Python 3.7+
- Google Chrome браузер
- Интернет-соединение

## Установка

1. Клонируйте или скачайте репозиторий

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

Selenium 4+ автоматически загружает ChromeDriver через Selenium Manager, поэтому дополнительная установка не требуется.

## Использование

1. Убедитесь, что файл `urls.txt` содержит список URL материалов (по одному на строку)

2. Запустите скрипт:
```bash
python downloader.py
```

3. В открывшемся браузере **авторизуйтесь вручную** на сайте innovationcampus.ru

4. После успешной авторизации скрипт автоматически:
   - Пройдёт по каждому URL из списка
   - Скачает PDF-файлы в папку `innovationcampus_materials/`
   - Отобразит прогресс в консоли

5. По завершении браузер закроется автоматически

## Структура проекта

```
.
├── downloader.py              # Основной скрипт
├── urls.txt                   # Список URL материалов
├── requirements.txt           # Python зависимости
├── innovationcampus_materials/ # Папка для загрузок (создаётся автоматически)
└── README.md                  # Эта инструкция
```

## Как это работает

1. **Настройка браузера**: Chrome настраивается на автоматическое скачивание PDF без открытия встроенного просмотрщика
2. **Авторизация**: Скрипт открывает страницу входа и ждёт (до 5 минут), пока вы авторизуетесь
3. **Загрузка**: Для каждого URL из `urls.txt` открывается страница материала, PDF автоматически скачивается
4. **Проверка**: Скрипт ждёт завершения каждой загрузки перед переходом к следующему материалу

## Возможные проблемы

### PDF открывается в просмотрщике вместо скачивания

Настройка `plugins.always_open_pdf_externally: True` должна решить эту проблему. Если проблема сохраняется, проверьте настройки Chrome вручную.

### ChromeDriver не найден

Selenium 4+ автоматически управляет ChromeDriver. Если возникают проблемы:
- Обновите Selenium: `pip install --upgrade selenium`
- Убедитесь, что Chrome установлен и обновлён

### Timeout при авторизации

Если авторизация занимает больше 5 минут, увеличьте таймаут в `downloader.py`:
```python
wait_for_login(driver, LOGIN_URL, timeout=600)  # 10 минут
```

### Некоторые материалы не скачиваются

Проверьте консоль на наличие ошибок. Скрипт продолжает работу даже если один из материалов недоступен.

## Альтернативный браузер (Firefox)

Если предпочитаете Firefox, замените функцию `setup_browser()` в `downloader.py`:

```python
from selenium.webdriver.firefox.options import Options

def setup_browser(download_dir):
    firefox_options = Options()
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.dir", os.path.abspath(download_dir))
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    firefox_options.set_preference("pdfjs.disabled", True)
    
    driver = webdriver.Firefox(options=firefox_options)
    return driver
```

## Лицензия

MIT

## Автор

Создано с помощью Claude Code
