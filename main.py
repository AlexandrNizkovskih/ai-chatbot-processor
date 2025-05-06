import argparse
from process import main as process_main
from build_jsonl_from_txt import main as build_jsonl_main
from jsonlchek import main as check_jsonl_main

def run():
    parser = argparse.ArgumentParser(
        description="Утилита для обработки транскриптов, генерации базы и проверки JSONL"
    )

    parser.add_argument("--process", action="store_true", help="Обработать все транскрипты через LLM")
    parser.add_argument("--build-jsonl", action="store_true", help="Построить JSONL из обработанных файлов")
    parser.add_argument("--check-jsonl", action="store_true", help="Проверить валидность JSONL файла")

    args = parser.parse_args()

    if args.process:
        process_main()
    elif args.build_jsonl:
        build_jsonl_main()
    elif args.check_jsonl:
        check_jsonl_main()
    else:
        print("❗ Не указано действие. Используйте один из аргументов:")
        print("  --process       — обработать транскрипты")
        print("  --build-jsonl   — собрать базу JSONL")
        print("  --check-jsonl   — проверить валидность JSONL")

if __name__ == "__main__":
    run()
