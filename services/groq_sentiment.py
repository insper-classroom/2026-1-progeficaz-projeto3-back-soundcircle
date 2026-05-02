import requests
from config import Config

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"


def analyze_sentiment(comments_text_list):
    """
    Envia comentários para a Groq e recebe um score de sentimento entre -1 e 1.
    Retorna float ou None em caso de erro.
    """
    if not comments_text_list:
        return None

    prompt = (
        "Analise o sentimento geral dos seguintes comentários sobre uma música. "
        "Responda APENAS com um número entre -1 e 1, onde -1 é muito negativo, "
        "0 é neutro e 1 é muito positivo. Não inclua texto extra.\n\n"
        + "\n".join(f"- {c}" for c in comments_text_list)
    )

    headers = {
        "Authorization": f"Bearer {Config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Você é um analisador de sentimento. Responda apenas com um número entre -1 e 1."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 10,
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        score = float(content)
        return max(-1.0, min(1.0, score))
    except Exception as e:
        print(f"[Groq Sentiment] Erro: {e}")
        return None
