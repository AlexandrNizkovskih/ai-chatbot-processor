import json
import os
from datetime import datetime

input_file = 'base_array.jsonl'
log_file = 'logs/validate_jsonl.log'

required_fields = {"topic", "keywords", "summary", "text", "fragments"}
fragment_fields = {"timestamp", "highlight", "youtube_url"}

def log(message):
    print(message)
    with open(log_file, 'a', encoding='utf-8') as logf:
        logf.write(f"{datetime.now().isoformat()} — {message}\n")

def validate_line(data, line_num):
    if not required_fields.issubset(data):
        missing = required_fields - set(data)
        log(f"[MISSING FIELDS] Line {line_num}: {missing}")
        return False

    if not isinstance(data["fragments"], list):
        log(f"[INVALID FRAGMENTS] Line {line_num}: not a list")
        return False

    for j, frag in enumerate(data["fragments"]):
        if not isinstance(frag, dict):
            log(f"[INVALID FRAGMENT] Line {line_num}, fragment {j}: not a dict")
            return False
        if not fragment_fields.issubset(frag):
            missing = fragment_fields - set(frag)
            log(f"[MISSING FRAGMENT FIELDS] Line {line_num}, fragment {j}: {missing}")
            return False

    return True

def process_file():
    total = 0
    valid = 0
    invalid = 0

    os.makedirs("logs", exist_ok=True)

    with open(log_file, 'w', encoding='utf-8') as logf:
        logf.write(f"[LOG STARTED] {datetime.now().isoformat()}\n\n")

    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            total += 1
            try:
                data = json.loads(line)
                if validate_line(data, i):
                    valid += 1
                else:
                    invalid += 1
            except json.JSONDecodeError as e:
                log(f"[JSON ERROR] Line {i}: {e}")
                invalid += 1

    with open(log_file, 'a', encoding='utf-8') as logf:
        logf.write("\n--- SUMMARY ---\n")
        logf.write(f"✅ Valid: {valid}\n")
        logf.write(f"❌ Invalid: {invalid}\n")
        logf.write(f"📦 Total: {total}\n")

    print("🔍 Проверка завершена. Лог сохранён в:", log_file)

def main():
    process_file()