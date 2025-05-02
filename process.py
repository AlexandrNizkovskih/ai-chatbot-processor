import os
import json
import time
import re
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Инициализация OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")  # установи в .env
)

# Путь к папке с транскриптами
TRANSCRIPTS_DIR = "transcripts"
RAW_OUTPUT_DIR = "raw_outputs"

#папка для результатов
os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)


def extract_video_id(filename):
    return filename.split("_")[1]


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
            model="deepseek/deepseek-prover-v2:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content

        # Сохраняем в txt файл
        output_name = os.path.splitext(os.path.basename(file_path))[0]
        out_path = os.path.join(RAW_OUTPUT_DIR, f"{output_name}.txt")

        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(content)

        return True

    except Exception as e:
        print(f"[ERROR] Не удалось обработать {file_path}: {e}")
        return False


def main():
    files = [f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith(".txt")]

    for file_name in tqdm(files):
        file_path = os.path.join(TRANSCRIPTS_DIR, file_name)
        video_id = extract_video_id(file_name)
        if not video_id:
            print(f"[WARN] Не удалось извлечь ID из {file_name}")
            continue

        print(f"[INFO] Обрабатывается: {file_name}")
        success = process_file(file_path, video_id)

        if success:
            time.sleep(2)  # Не спамим

if __name__ == "__main__":
    main()