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
