import requests
import uuid
import time
from config import GIGACHAT_AUTH_KEY

GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
GIGACHAT_TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

_access_token = None
_token_expire = None


def _get_access_token() -> str:
    global _access_token, _token_expire

    if _access_token and _token_expire and time.time() < _token_expire - 60:
        return _access_token

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Bearer {GIGACHAT_AUTH_KEY}",
    }
    data = "scope=GIGACHAT_API_PERS"

    try:
        response = requests.post(
            GIGACHAT_TOKEN_URL,
            headers=headers,
            data=data,
            verify=False,
            timeout=30,
        )
        response.raise_for_status()
        token_data = response.json()
        _access_token = token_data.get("access_token", "")
        expires_in = token_data.get("expires_in", 0)
        _token_expire = time.time() + expires_in if expires_in else time.time() + 1800
        return _access_token
    except Exception as e:
        print(f"[LLM] Ошибка получения токена GigaChat: {e}")
        return ""


def generate_review_response(review_text: str, style: str) -> str:
    access_token = _get_access_token()
    if not access_token:
        return "Произошла ошибка при подключении к нейросети. Попробуйте позже."

    style_prompts = {
        "polite": "Отвечай максимально вежливо, спокойно и доброжелательно.",
        "confident": "Отвечай уверенно и профессионально, защищая репутацию бизнеса, но без агрессии.",
        "apologetic": "Отвечай с искренним извинением, признавай ошибку и предлагай компенсацию.",
        "neutral": "Отвечай нейтрально и по делу, без лишних эмоций.",
    }

    style_instruction = style_prompts.get(style, style_prompts["polite"])

    system_prompt = (
        f"Ты — профессиональный менеджер по работе с отзывами. "
        f"Напиши ответ на отзыв клиента от лица бизнеса. "
        f"{style_instruction} "
        f"Ответ должен быть коротким (2-5 предложений), на русском языке. "
        f"Не используй шаблонные фразы типа 'Спасибо за ваш отзыв'. "
        f"Обращайся к клиенту на 'вы'."
    )

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Отзыв клиента: {review_text}"},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = requests.post(
            GIGACHAT_API_URL,
            headers=headers,
            json=payload,
            verify=False,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        print(f"[LLM] Ошибка генерации: {e}")
        return "Произошла ошибка при генерации ответа. Попробуйте ещё раз."
