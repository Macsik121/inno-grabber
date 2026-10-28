"""
Скрипт для автоматического скачивания файлов с innovationcampus.ru
Использует Playwright для автоматизации браузера с существующей сессией
"""

import asyncio
import os
import re
import json
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import unquote
from datetime import datetime
from collections import defaultdict

# Список ссылок на ресурсы
RESOURCE_URLS = [
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2761',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2762', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2763',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2764',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2765',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2766',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2767',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2778',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2779', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2780', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2713', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2752', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2753', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2754', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2756', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2757', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2758', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2759', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2760', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2781', 
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2782',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2783',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2784',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2786',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2785',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2789',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2790',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2792',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2791',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2793',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2768',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2769',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2770',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2771',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2772',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2773',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2774',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2775',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2776',
    'https://www.innovationcampus.ru/lms/mod/resource/view.php?id=2777'
]


def get_course_name():
    """Запрашивает у пользователя название курса"""
    print("=" * 60)
    print("📚 Введите название курса")
    print("=" * 60)
    while True:
        course_name = input("\n👉 Название курса: ").strip()
        if course_name:
            return course_name
        print("⚠️  Название курса не может быть пустым. Попробуйте снова.")


def extract_prefix(filename):
    """
    Извлекает числовой префикс из имени файла (например, "1.1.", "2.3.", "1.")
    Возвращает (prefix_string, prefix_tuple) или (None, None)
    """
    match = re.match(r'^(\d+(?:\.\d+)*)\.\s*', filename)
    if match:
        prefix_str = match.group(1)
        # Преобразуем в кортеж чисел для правильной сортировки (1.1 < 1.2 < 1.10)
        prefix_tuple = tuple(int(x) for x in prefix_str.split('.'))
        return prefix_str, prefix_tuple
    return None, None


def group_files_by_prefix(directory):
    """
    Группирует файлы по префиксам и возвращает отсортированный словарь
    {prefix_string: [список файлов]}
    """
    files_by_prefix = defaultdict(list)

    # Сканируем все файлы в директории
    for file_path in directory.iterdir():
        if file_path.is_file():
            prefix_str, prefix_tuple = extract_prefix(file_path.name)
            if prefix_str and prefix_tuple:
                files_by_prefix[(prefix_str, prefix_tuple)].append(file_path)

    # Сортируем по версионному порядку префиксов
    sorted_groups = {}
    for (prefix_str, prefix_tuple), files in sorted(files_by_prefix.items(), key=lambda x: x[0][1]):
        sorted_groups[prefix_str] = sorted(files, key=lambda f: f.name)

    return sorted_groups


def structure_files(course_dir):
    """
    Предлагает пользователю структурировать файлы по папкам на основе префиксов
    """
    print("\n" + "=" * 60)
    print("📂 Структуризация файлов по разделам")
    print("=" * 60)

    # Группируем файлы
    files_by_prefix = group_files_by_prefix(course_dir)

    if not files_by_prefix:
        print("\n💡 Файлы с числовыми префиксами не найдены.")
        print("   Все файлы остаются в корневой папке курса.")
        return

    print(f"\n✅ Найдено {len(files_by_prefix)} групп(ы) файлов с префиксами")

    # Спрашиваем, хочет ли пользователь структурировать
    while True:
        response = input("\n👉 Хотите структурировать файлы по папкам? (да/нет): ").strip().lower()
        if response in ['да', 'д', 'yes', 'y']:
            break
        elif response in ['нет', 'н', 'no', 'n']:
            print("\n✅ Структуризация пропущена. Все файлы остаются на своих местах.")
            return
        else:
            print("⚠️  Пожалуйста, введите 'да' или 'нет'")

    # Обрабатываем каждый префикс
    moved_count = 0
    skipped_count = 0

    for prefix_str, files in files_by_prefix.items():
        print("\n" + "-" * 60)
        print(f"📌 Найдены файлы с префиксом '{prefix_str}.'")
        print(f"   Количество файлов: {len(files)}")
        print("\n   Примеры файлов:")

        # Показываем до 3 примеров
        for i, file_path in enumerate(files[:3], 1):
            print(f"   {i}. {file_path.name}")

        if len(files) > 3:
            print(f"   ... и ещё {len(files) - 3} файл(ов)")

        # Запрашиваем название раздела
        section_name = input(f"\n👉 Название раздела для '{prefix_str}.' (Enter - пропустить): ").strip()

        if not section_name:
            print(f"   ⏭️  Префикс '{prefix_str}.' пропущен")
            skipped_count += len(files)
            continue

        # Создаём папку и перемещаем файлы
        section_dir = course_dir / section_name
        try:
            section_dir.mkdir(exist_ok=True)

            for file_path in files:
                new_path = section_dir / file_path.name
                # Если файл уже существует в целевой папке, добавляем timestamp
                if new_path.exists():
                    stem = new_path.stem
                    suffix = new_path.suffix
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_name = f"{stem}_{timestamp}{suffix}"
                    new_path = section_dir / new_name

                file_path.rename(new_path)

            print(f"   ✅ Создана папка '{section_name}'")
            print(f"   ✅ Перемещено файлов: {len(files)}")
            moved_count += len(files)

        except Exception as e:
            print(f"   ❌ Ошибка при создании папки или перемещении: {e}")
            skipped_count += len(files)

    # Итоги структуризации
    print("\n" + "=" * 60)
    print("✨ Структуризация завершена")
    print(f"✅ Перемещено файлов: {moved_count}")
    if skipped_count > 0:
        print(f"⏭️  Пропущено файлов: {skipped_count}")
    print("=" * 60)


async def setup_chrome_preferences(profile_dir: Path, download_dir: Path):
    """Настраивает Chrome preferences для автоматического скачивания PDF"""
    prefs_dir = profile_dir / "Default"
    prefs_dir.mkdir(parents=True, exist_ok=True)

    prefs_file = prefs_dir / "Preferences"

    # Читаем существующие настройки или создаём новые
    if prefs_file.exists():
        with open(prefs_file, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
    else:
        prefs = {}

    # Настройки для автоматического скачивания PDF
    prefs.update({
        "download": {
            "default_directory": str(download_dir.absolute()),
            "prompt_for_download": False,
            "directory_upgrade": True
        },
        "plugins": {
            "always_open_pdf_externally": True
        }
    })

    # Сохраняем настройки
    with open(prefs_file, 'w', encoding='utf-8') as f:
        json.dump(prefs, f, indent=2)


async def main():
    """Основная функция"""
    # Запрашиваем название курса
    course_name = get_course_name()

    # Создаем директорию для курса
    course_dir = Path(course_name)
    course_dir.mkdir(exist_ok=True)
    print(f"\n📁 Директория для загрузок: {course_dir.absolute()}\n")

    # Настраиваем Chrome preferences для автоматического скачивания PDF
    profile_dir = Path("./browser_profile")
    await setup_chrome_preferences(profile_dir, course_dir)

    async with async_playwright() as p:
        # Запускаем Chrome с сохранением состояния пользователя
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./browser_profile",
            headless=False,
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )

        # Используем первую страницу (вкладку), которая открывается автоматически
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("🌐 Открываю первую ссылку для проверки авторизации...\n")

        # Переходим на первую ссылку для проверки авторизации
        await page.goto(RESOURCE_URLS[0])
        await page.wait_for_load_state("networkidle")

        # Проверяем, нужна ли авторизация
        if "login" in page.url.lower():
            print("🔐 Необходима авторизация!")
            print("👉 Пожалуйста, войдите в систему в открывшемся окне браузера")
            print("⏳ Ожидаю авторизации (максимум 5 минут)...\n")

            # Ждем, пока URL изменится (пользователь войдет)
            try:
                max_wait = 300  # 5 минут
                for i in range(max_wait):
                    await asyncio.sleep(1)
                    current_url = page.url
                    if "login" not in current_url.lower():
                        print("✅ Авторизация выполнена!\n")
                        break

                    # Выводим прогресс каждые 30 секунд
                    if (i + 1) % 30 == 0:
                        remaining = (max_wait - i - 1) // 60
                        print(f"   ⏳ Все еще жду авторизации... (~{remaining} мин осталось)")
                else:
                    # Время вышло
                    print("❌ Превышено время ожидания авторизации")
                    print("💡 Совет: войдите в систему и запустите скрипт снова\n")
                    await browser.close()
                    return

            except Exception as e:
                print(f"❌ Ошибка при ожидании авторизации: {e}\n")
                await browser.close()
                return
        else:
            print("✅ Авторизация активна!\n")

        # Счетчики
        downloaded = 0
        failed = 0

        # Обрабатываем каждую ссылку
        for i, url in enumerate(RESOURCE_URLS, 1):
            print(f"📄 [{i}/{len(RESOURCE_URLS)}] Обрабатываю: {url}")

            try:
                # Переходим на страницу ресурса
                await page.goto(url)
                await page.wait_for_load_state("networkidle", timeout=10000)

                # Ищем прямую ссылку на файл
                selectors = [
                    'a[href*="/pluginfile.php/"]',
                    '.resourceworkaround a',
                ]

                file_url = None
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            href = await element.get_attribute('href')
                            if href and '/pluginfile.php/' in href:
                                # Делаем URL абсолютным если нужно
                                if href.startswith('http'):
                                    file_url = href
                                else:
                                    file_url = f"https://www.innovationcampus.ru{href}"
                                break
                    except:
                        continue

                if not file_url:
                    # Пробуем найти через парсинг HTML
                    content = await page.content()
                    match = re.search(r'href="([^"]*?/pluginfile\.php/[^"]*?)"', content)
                    if match:
                        href = match.group(1)
                        file_url = href if href.startswith('http') else f"https://www.innovationcampus.ru{href}"
                    else:
                        raise Exception("Не найдена ссылка на файл")

                # Скачиваем файл напрямую через navigation вместо клика
                async with page.expect_download(timeout=60000) as download_info:
                    await page.goto(file_url)

                # Получаем объект загрузки
                download = await download_info.value

                # Получаем имя файла
                filename = download.suggested_filename
                filename = unquote(filename)

                # Если файл с таким именем существует, добавляем timestamp
                save_path = course_dir / filename
                if save_path.exists():
                    stem = save_path.stem
                    suffix = save_path.suffix
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{stem}_{timestamp}{suffix}"
                    save_path = course_dir / filename

                # Сохраняем файл
                await download.save_as(save_path)
                print(f"   ✅ Скачан: {filename}\n")
                downloaded += 1

            except Exception as e:
                print(f"   ❌ Ошибка: {e}\n")
                failed += 1

            # Небольшая пауза между запросами
            await asyncio.sleep(1)

        await browser.close()

        # Итоги скачивания
        print("=" * 60)
        print("✨ Скачивание завершено")
        print(f"✅ Скачано файлов: {downloaded}")
        print(f"❌ Ошибок: {failed}")
        print(f"📁 Файлы сохранены в: {course_dir.absolute()}")
        print("=" * 60)

        # Предлагаем структурировать файлы
        if downloaded > 0:
            structure_files(course_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("📚 Innovation Campus Downloader")
    print("=" * 60)
    print()
    asyncio.run(main())
