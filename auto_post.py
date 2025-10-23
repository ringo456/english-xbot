import os
import re
import openai
import tweepy
from datetime import datetime
from dotenv import load_dotenv

# --- 環境変数をロード ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- X API クライアント ---
client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
)
upload = tweepy.API(auth=tweepy.OAuth1UserHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_TOKEN_SECRET")
))

# --- 難解英単語を生成し、画像つきでポスト ---
def generate_word_post():
    # GPTに英単語フォーマットを生成させる
    prompt = """
    You are an English linguist who writes educational X posts. And your audience are mainly learners of IELTS, TOEIC, Eiken Grade1 - top level learners who really love the most difficult part of English.
    Generate ONE difficult English word and format it in this style.
    Do NOT include hashtags or emojis except those shown in the format.

    ---
    [word]
    /IPA/ (品詞) = 日本語訳

    📘 例: 英文
    🇯🇵 和訳: 日本語訳

    ✅ ポイント: 語義や文脈を簡潔に説明（1～2文）

    🧠語源メモ: 語源・派生語を1段落で。

    ✒️コロケーション:
    ・英語句 = 日本語訳（5行以内）

    📘類義語:
    ・英単語（3〜4語以内）
    ---

    Example: vicariously
    """

    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    text = res.choices[0].message.content.strip()

    # 例文部分を抽出
    match = re.search(r"📘 例:\s*(.+)", text)
    example_sentence = match.group(1) if match else "A beautiful abstract scene."

    # --- 画像生成 ---
    image_prompt = f"Create a cinematic, realistic illustration representing this sentence: {example_sentence}"
    image = openai.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1024x1024"
    )
    image_url = image.data[0].url

    # 画像を一時保存
    import requests
    img_data = requests.get(image_url).content
    filename = "temp.jpg"
    with open(filename, "wb") as f:
        f.write(img_data)

    # --- 投稿本文を作成 ---
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    tweet_text = f"🕒 {now}\n\n{text}"

    # --- 画像付きで投稿 ---
    media = upload.media_upload(filename)
    client.create_tweet(text=tweet_text, media_ids=[media.media_id])
    print("✅ Posted successfully with image:\n", tweet_text)

    # --- 画像削除（整理） ---
    os.remove(filename)


if __name__ == "__main__":
    generate_word_post()
