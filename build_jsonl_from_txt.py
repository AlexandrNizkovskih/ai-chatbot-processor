import os
import json
from datetime import datetime

input_folder = 'raw_outputs'
output_file = 'base_array.jsonl'
log_file = 'logs/build_jsonl_from_txt.log'

files_processed = 0
lines_written = 0
files_skipped = 0
files_failed = []

def log(message):
    print(message)
    with open(log_file, 'a', encoding='utf-8') as logf:
        logf.write(f"{datetime.now().isoformat()} — {message}\n")

def extract_json_array(text: str) -> str:
    start = text.find('[')
    if start == -1:
        return ''
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return ''

def clean_text(text: str) -> str:
    return extract_json_array(text)

def process_file(filepath: str, fout) -> None:
    global files_processed, lines_written, files_skipped, files_failed

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    cleaned_text = clean_text(raw_text)

    if not cleaned_text:
        log(f"[SKIP] Пустой или нераспознанный формат: {os.path.basename(filepath)}")
        files_skipped += 1
        return

    try:
        parsed = json.loads(cleaned_text)
        if isinstance(parsed, dict):
            fout.write(json.dumps(parsed, ensure_ascii=False) + '\n')
            lines_written += 1
        elif isinstance(parsed, list):
            for item in parsed:
                fout.write(json.dumps(item, ensure_ascii=False) + '\n')
                lines_written += 1
        else:
            log(f"[SKIP] Неизвестный тип JSON в файле: {os.path.basename(filepath)}")
            files_skipped += 1
            return

        files_processed += 1
        log(f"[OK] Обработан файл: {os.path.basename(filepath)}")

    except json.JSONDecodeError as e:
        files_failed.append(os.path.basename(filepath))
        log(f"[FAIL] {os.path.basename(filepath)} — ошибка парсинга JSON: {e}")

def process_all_files():
    os.makedirs("logs", exist_ok=True)

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"[LOG STARTED] {datetime.now().isoformat()}\n\n")

    with open(output_file, 'w', encoding='utf-8') as fout:
        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                process_file(os.path.join(input_folder, filename), fout)

def log_summary():
    log("\n--- ИТОГ ---")
    log(f"✅ Обработано файлов: {files_processed}")
    log(f"✍️  Записано строк в JSONL: {lines_written}")
    log(f"⛔ Пропущено: {files_skipped}")
    log(f"❌ Ошибки: {len(files_failed)}")

    if files_failed:
        log("Список файлов с ошибками:")
        for f in files_failed:
            log(f" - {f}")

def main():
    process_all_files()
    log_summary()