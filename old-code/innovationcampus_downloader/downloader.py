"""
Автоматическая загрузка материалов с innovationcampus.ru через Selenium.
Скрипт открывает браузер, ждёт ручной авторизации, затем скачивает PDF из списка URL.
"""

import os
import time
import re
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from structurer import organize_by_sections

def setup_browser(download_dir):
    """
    Настройка Chrome для автоматического скачивания PDF.
    PDF не открывается в просмотрщике браузера, а сразу сохраняется в указанную папку.
    """
    chrome_options = Options()

    abs_download_dir = os.path.abspath(download_dir)

    prefs = {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def wait_for_login(driver, login_url, timeout=300):
    """
    Открывает страницу входа и ждёт, пока пользователь авторизуется вручную.
    Фиксирует успешный вход по изменению URL (уход со страницы /login/index.php).
    """
    print("Открываю страницу авторизации...")
    driver.get(login_url)

    print("\n" + "="*60)
    print("АВТОРИЗУЙТЕСЬ В БРАУЗЕРЕ ВРУЧНУЮ")
    print("Скрипт продолжит работу после успешного входа")
    print("="*60 + "\n")

    start_time = time.time()
    while time.time() - start_time < timeout:
        current_url = driver.current_url

        if "/login/index.php" not in current_url:
            print("✓ Авторизация успешна!")
            time.sleep(2)
            return True

        time.sleep(1)

    print("✗ Время ожидания авторизации истекло")
    return False


def wait_for_download_complete(download_dir, timeout=30):
    """
    Ждёт, пока в папке исчезнут файлы .crdownload (незавершённые загрузки Chrome).
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        crdownload_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]

        if not crdownload_files:
            return True

        time.sleep(0.5)

    print("  ⚠ Предупреждение: файл всё ещё загружается")
    return False


def download_materials(driver, urls, download_dir):
    """
    Для каждого URL открывает страницу материала, находит ссылку на PDF
    в div.resourceworkaround и кликает на неё для скачивания.
    """
    total = len(urls)

    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{total}] Открываю: {url}")

        try:
            driver.get(url)

            wait = WebDriverWait(driver, 10)
            div = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "resourceworkaround")))

            link = div.find_element(By.TAG_NAME, "a")
            link.click()

            print(f"  → Кликнул на ссылку для скачивания")

            wait_for_download_complete(download_dir, timeout=30)

            print(f"  ✓ Материал #{idx} скачан")

        except Exception as e:
            print(f"  ✗ Ошибка при загрузке материала #{idx}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"Завершено! Скачано материалов: {total}")
    print(f"Папка загрузки: {download_dir}")


def extract_section_prefix(filename):
    """
    Извлекает префикс раздела из имени файла.

    Примеры:
        "1.1.filename.pdf" → "1.1."
        "3.4.1.filename.pdf" → "3.4." (первые два уровня)
        "filename.pdf" → None
    """
    # Пробуем извлечь формат X.Y.
    match = re.match(r'^(\d+\.\d+\.)', filename)
    if match:
        return match.group(1)

    # Пробуем извлечь формат X.
    match = re.match(r'^(\d+\.)', filename)
    if match:
        return match.group(1)

    return None


def organize_by_sections(download_dir):
    """
    Организует файлы в папки по префиксам разделов.

    - Сканирует файлы в download_dir
    - Группирует по префиксам разделов
    - Для каждого префикса запрашивает название раздела у пользователя
    - Создаёт папки и перемещает файлы
    """
    print(f"\n{'='*60}")
    print("СТРУКТУРИРОВАНИЕ ФАЙЛОВ ПО РАЗДЕЛАМ")
    print(f"{'='*60}\n")

    # Собираем все файлы
    if not os.path.exists(download_dir):
        print(f"Папка {download_dir} не найдена")
        return

    files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]

    if not files:
        print("Нет файлов для организации")
        return

    # Группируем по префиксам
    sections = defaultdict(list)
    for filename in files:
        prefix = extract_section_prefix(filename)
        if prefix:
            sections[prefix].append(filename)

    if not sections:
        print("Не найдено файлов с префиксами разделов")
        return

    # Сортируем префиксы численно
    def parse_prefix(prefix):
        """Преобразует '1.2.' в кортеж (1, 2) для сортировки"""
        numbers = [int(n) for n in prefix.rstrip('.').split('.')]
        return tuple(numbers)

    sorted_prefixes = sorted(sections.keys(), key=parse_prefix)

    # Обрабатываем каждый раздел
    for prefix in sorted_prefixes:
        files_in_section = sections[prefix]

        print(f"\n{'='*60}")
        print(f"Раздел с префиксом: {prefix}")
        print(f"Найдено файлов: {len(files_in_section)}")
        print(f"\nПримеры файлов:")

        for filename in files_in_section[:3]:
            print(f"  - {filename}")

        if len(files_in_section) > 3:
            print(f"  ... и ещё {len(files_in_section) - 3}")

        section_name = input(f"\nВведите название раздела (Enter — пропустить): ").strip()

        if not section_name:
            print(f"Раздел {prefix} пропущен")
            continue

        # Создаём папку для раздела
        section_dir = os.path.join(download_dir, section_name)
        os.makedirs(section_dir, exist_ok=True)

        # Перемещаем файлы
        moved_count = 0
        for filename in files_in_section:
            src = os.path.join(download_dir, filename)
            dst = os.path.join(section_dir, filename)
            try:
                os.rename(src, dst)
                moved_count += 1
            except Exception as e:
                print(f"  ✗ Ошибка при перемещении {filename}: {e}")

        print(f"✓ Перемещено файлов в '{section_name}': {moved_count}")

    print(f"\n{'='*60}")
    print("Структурирование завершено!")
    print(f"{'='*60}")


def main():
    BASE_URL = "https://www.innovationcampus.ru"
    LOGIN_URL = f"{BASE_URL}/lms/login/index.php"
    URLS_FILE = "urls.txt"

    # Запрос названия курса
    course_name = input("Введите название курса: ").strip()
    if not course_name:
        course_name = "Без названия"

    # Создание папки для скачивания с названием курса
    DOWNLOAD_DIR = os.path.join("innovationcampus_materials", course_name)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print("Загружаю список материалов...")
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f"Найдено материалов: {len(urls)}")

    driver = setup_browser(DOWNLOAD_DIR)

    try:
        if not wait_for_login(driver, LOGIN_URL, timeout=300):
            print("Не удалось авторизоваться. Завершение.")
            return

        download_materials(driver, urls, DOWNLOAD_DIR)

    finally:
        print("\nЗакрываю браузер...")
        driver.quit()

        # Запрос на структурирование файлов
        organize = input("\nСтруктурировать файлы по разделам? (y/n): ").strip().lower()
        if organize == 'y':
            organize_by_sections(DOWNLOAD_DIR)
        else:
            print(f"\nФайлы остались в папке: {DOWNLOAD_DIR}")


if __name__ == "__main__":
    main()
