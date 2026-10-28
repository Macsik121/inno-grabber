"""
Скрипт для автоматического скачивания PDF материалов с innovationcampus.ru
Требует ручного входа в систему, затем автоматически скачивает PDF файлы
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Настройки
DOWNLOAD_DIR = os.path.join(os.getcwd(), "innovationcampus_materials")
LOGIN_URL = "https://innovationcampus.ru/lms/login/index.php"
LINKS_FILE = "course_links.txt"


def setup_driver():
    """Настройка Chrome драйвера с параметрами скачивания"""

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    chrome_options = Options()

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Запускаем драйвер с автоматической установкой ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    return driver


def load_course_links(filename):
    """Загружает список ссылок из текстового файла"""

    if not os.path.exists(filename):
        print(f"\n❌ Файл {filename} не найден!")
        print(f"📝 Создайте файл {filename} и добавьте в него ссылки на курсы")
        print("   (по одной ссылке на строку)\n")
        return []

    links = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                links.append(line)

    return links


def manual_login(driver):
    """Открывает страницу входа и ждет, пока пользователь войдет вручную"""

    print(f"\n{'='*60}")
    print("ШАГ 1: ВХОД В СИСТЕМУ")
    print(f"{'='*60}")
    print("\n🌐 Открываю страницу входа...")

    driver.get(LOGIN_URL)

    print("\n⏳ ПОЖАЛУЙСТА, ВОЙДИТЕ В СИСТЕМУ ВРУЧНУЮ")
    print("   Введите логин и пароль в открывшемся окне браузера")
    print("   После успешного входа скрипт продолжит работу автоматически\n")

    wait = WebDriverWait(driver, 300)

    try:
        wait.until(lambda d: d.current_url != LOGIN_URL)
        print("\n✅ Вход выполнен успешно!\n")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"\n❌ Ошибка: Время ожидания входа истекло")
        return False


def get_pdf_links(driver):
    """Находит все ссылки на PDF файлы на текущей странице"""

    pdf_links = []

    try:
        all_links = driver.find_elements(By.TAG_NAME, "a")

        for link in all_links:
            href = link.get_attribute("href")
            if href and ".pdf" in href.lower():
                pdf_links.append({
                    "url": href,
                    "text": link.text.strip() or "Без названия"
                })

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                frame_links = driver.find_elements(By.TAG_NAME, "a")
                for link in frame_links:
                    href = link.get_attribute("href")
                    if href and ".pdf" in href.lower():
                        pdf_links.append({
                            "url": href,
                            "text": link.text.strip() or "Без названия"
                        })
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue

    except Exception as e:
        print(f"⚠️  Предупреждение при поиске PDF: {e}")

    return pdf_links


def download_materials(driver, course_url):
    """Переходит на страницу курса и скачивает все PDF материалы"""

    print(f"\n{'='*60}")
    print(f"📚 Обработка курса: {course_url}")
    print(f"{'='*60}\n")

    try:
        print("🌐 Загружаю страницу курса...")
        driver.get(course_url)
        time.sleep(3)

        try:
            course_title = driver.find_element(By.TAG_NAME, "h1").text
            print(f"📖 Курс: {course_title}\n")
        except:
            course_title = "Курс без названия"

        print("🔍 Ищу PDF материалы...")
        pdf_links = get_pdf_links(driver)

        if not pdf_links:
            print("⚠️  PDF файлы не найдены на этой странице")
            return 0

        print(f"✅ Найдено PDF файлов: {len(pdf_links)}\n")

        downloaded = 0
        for idx, pdf in enumerate(pdf_links, 1):
            try:
                print(f"  [{idx}/{len(pdf_links)}] Скачиваю: {pdf['text'][:50]}...")
                driver.get(pdf['url'])
                time.sleep(2)
                downloaded += 1
                print(f"      ✅ Готово")
            except Exception as e:
                print(f"      ❌ Ошибка: {e}")

        print(f"\n✅ Скачано файлов: {downloaded}/{len(pdf_links)}")
        return downloaded

    except Exception as e:
        print(f"❌ Ошибка при обработке курса: {e}")
        return 0


def main():
    """Основная функция"""

    print("\n" + "="*60)
    print("СКАЧИВАТЕЛЬ МАТЕРИАЛОВ INNOVATIONCAMPUS.RU")
    print("="*60 + "\n")

    course_urls = load_course_links(LINKS_FILE)

    if not course_urls:
        print("⚠️  Список курсов пуст!")
        print(f"\n📝 Создайте файл '{LINKS_FILE}' и добавьте ссылки на курсы")
        print("   (по одной ссылке на строку)\n")
        print("Пример содержимого:")
        print("https://innovationcampus.ru/lms/course/view.php?id=123")
        print("https://innovationcampus.ru/lms/course/view.php?id=456\n")
        return

    driver = None

    try:
        print("🚀 Запускаю Chrome...")
        driver = setup_driver()

        if not manual_login(driver):
            print("\n❌ Не удалось войти в систему. Завершение работы.")
            return

        total_downloaded = 0
        print(f"\n{'='*60}")
        print(f"НАЧИНАЮ СКАЧИВАНИЕ ({len(course_urls)} курсов)")
        print(f"{'='*60}")

        for idx, url in enumerate(course_urls, 1):
            print(f"\n\n[{idx}/{len(course_urls)}] Курс: {url}")
            downloaded = download_materials(driver, url)
            total_downloaded += downloaded
            time.sleep(2)

        print(f"\n\n{'='*60}")
        print("ЗАВЕРШЕНО!")
        print(f"{'='*60}")
        print(f"\n📊 Всего скачано файлов: {total_downloaded}")
        print(f"📁 Папка с материалами: {DOWNLOAD_DIR}\n")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

    finally:
        if driver:
            print("\n⏳ Закрываю браузер через 5 секунд...")
            time.sleep(5)
            driver.quit()


if __name__ == "__main__":
    main()
