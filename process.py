import os
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка переменных окружения
load_dotenv()

# Инициализация клиента OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Пути
TRANSCRIPTS_DIR = "transcripts"
RAW_OUTPUT_DIR = "raw_outputs"
LOGS_DIR = "logs"

# Создание необходимых директорий
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def extract_video_id(filename):
    """Извлекает ID видео из имени файла."""
    prefix = "transcript_"
    if filename.startswith(prefix):
        return filename[len(prefix):len(prefix)+11]
    raise ValueError(f"Имя не начинается с '{prefix}': {filename}")

def build_prompt(text, video_id):
    return f"""Ты — помощник, который преобразует транскрибированный текст из видео в смысловые блоки.

У тебя есть один текстовый файл, содержащий весь транскрипт видео. Он не содержит ссылок, только речь с таймкодами вроде [01:27] Текст.

Твоя задача:

1. Прочитать весь транскрипт.
2. Выделить основные темы или вопросы, которые поднимаются в видео.
3. Для каждой темы:
   - Сформулировать `topic` — короткий заголовок.
   - Добавить `keywords` — список из 5–8 ключевых слов.
   - Составить `summary` — 1–2 предложения, кратко раскрывающие суть темы.
   - Составить `text` — чистый, связный текст, раскрывающий тему (без воды, повторов, обращения к видео).
   - Добавить `fragments`: список ключевых моментов с таймкодом, пояснением и ссылкой на YouTube в формате `https://youtube.com/watch?v={video_id}#t=ммmссs`.

Верни результат **строкой JSON-массива**, например:
[
  {{
    "topic": "...",
    "keywords": ["...", "..."],
    "summary": "...",
    "text": "...",
    "fragments": [
      {{
        "timestamp": "00:12",
        "highlight": "...",
        "youtube_url": "https://youtube.com/watch?v={video_id}#t=00m12s"
      }}
    ]
  }}
]

Никаких пояснений вне JSON — только массив в виде строки одной JSON!

Вот транскрипт:
{text}
"""

def process_file(file_path, video_id):
    with open(file_path, "r", encoding="utf-8") as f:
        txt = f.read()

    prompt = build_prompt(txt, video_id)

    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        if not response or not hasattr(response, "choices") or not response.choices:
            raise ValueError(f"Неверный ответ от API: {response}")

        choice = response.choices[0]
        if not hasattr(choice, "message") or not choice.message or not choice.message.content:
            raise ValueError("Пустой message.content в ответе")

        content = choice.message.content

        output_name = os.path.splitext(os.path.basename(file_path))[0]
        out_path = os.path.join(RAW_OUTPUT_DIR, f"{output_name}.txt")

        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(content)

        with open(os.path.join(LOGS_DIR, "success.txt"), "a", encoding="utf-8") as log_ok:
            log_ok.write(f"{os.path.basename(file_path)}\n")

        return True

    except Exception as e:
        print(f"[ERROR] Не удалось обработать {file_path}: {e}")

        try:
            with open(os.path.join(LOGS_DIR, "response_debug.txt"), "a", encoding="utf-8") as debug_log:
                debug_log.write(f"=== {file_path} ===\n")
                debug_log.write(str(response) + "\n\n")
        except Exception:
            pass

        with open(os.path.join(LOGS_DIR, "failed.txt"), "a", encoding="utf-8") as log_err:
            log_err.write(f"{os.path.basename(file_path)} — {str(e)}\n")

        return False

def process_all_files():
    files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".txt")]
    for file_name in tqdm(files):
        file_path = os.path.join(TRANSCRIPTS_DIR, file_name)
        try:
            video_id = extract_video_id(file_name)
        except ValueError as e:
            print(f"[WARN] {e}")
            continue

        print(f"[INFO] Обрабатывается: {file_name}")
        success = process_file(file_path, video_id)
        if success:
            time.sleep(20)  # Не спамим API

def main():
    process_all_files()