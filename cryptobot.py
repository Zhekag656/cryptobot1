from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from datetime import datetime
from pytz import timezone


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я ваш криптобот. Я буду надсилати оновлення в канал кожні 10 секунд.")


# Отримання індексу страху та жадібності
def get_fear_greed_index():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url)
        data = response.json()

        translations = {
            "Extreme Fear": "Екстремальний страх",
            "Fear": "Страх",
            "Neutral": "Нейтрально",
            "Greed": "Жадібність",
            "Extreme Greed": "Екстремальна жадібність"
        }

        value_classification = data['data'][0]['value_classification']
        translated_classification = translations.get(value_classification, value_classification)

        return {
            'value': data['data'][0]['value'],
            'value_classification': translated_classification,
            'timestamp': data['data'][0]['timestamp']
        }
    except Exception as e:
        print(f"Помилка при отриманні індексу страху та жадібності: {e}")
        return {'value': 'N/A', 'value_classification': 'N/A', 'timestamp': 'N/A'}


# Отримання даних про криптовалюти
import requests

import requests

def get_crypto_data():
    try:
        # Ваш API-ключ CoinMarketCap
        API_KEY = "a9ab8f08-9d28-4835-bbcd-6afb1868254c"  # Замініть на ваш API-ключ

        # Заголовки для запиту
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": API_KEY,
        }

        # Отримання даних про криптовалюти
        url_cryptos = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
        params_cryptos = {
            "start": "1",  # Починаємо з першої криптовалюти
            "limit": "250",  # Максимальна кількість криптовалют
            "convert": "USD",  # Валюта для конвертації
        }
        response_cryptos = requests.get(url_cryptos, headers=headers, params=params_cryptos)
        cryptos_data = response_cryptos.json()

        # Отримання загальної інформації про ринок
        url_global = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
        response_global = requests.get(url_global, headers=headers)
        global_data = response_global.json()

        # Перевірка, чи API повернуло дані
        if "data" not in cryptos_data or "data" not in global_data:
            print("Помилка: API не повернуло дані.")
            return {}

        # Знаходження BTC і ETH
        btc_data = next((coin for coin in cryptos_data["data"] if coin["symbol"] == "BTC"), None)
        eth_data = next((coin for coin in cryptos_data["data"] if coin["symbol"] == "ETH"), None)

        if not btc_data or not eth_data:
            print("Помилка: Дані про BTC або ETH відсутні.")
            return {}

        # Сортування для топ зростання і падіння
        changes = [
            {
                "symbol": coin["symbol"],
                "price": coin["quote"]["USD"]["price"],
                "change": coin["quote"]["USD"]["percent_change_24h"],
            }
            for coin in cryptos_data["data"]
            if coin["quote"]["USD"]["percent_change_24h"] is not None
        ]

        # Топ 3 зростання і падіння
        top_gainers = sorted(changes, key=lambda x: x["change"], reverse=True)[:3]
        top_losers = sorted(changes, key=lambda x: x["change"])[:3]

        # Повернення даних
        return {
            "btc_price": btc_data["quote"]["USD"]["price"],
            "btc_change": btc_data["quote"]["USD"]["percent_change_24h"],
            "eth_price": eth_data["quote"]["USD"]["price"],
            "eth_change": eth_data["quote"]["USD"]["percent_change_24h"],
            "btc_dominance": global_data["data"]["btc_dominance"],
            "eth_dominance": global_data["data"]["eth_dominance"],
            "total_market_cap": format_number(global_data["data"]["quote"]["USD"]["total_market_cap"]),
            "total_volume": format_number(global_data["data"]["quote"]["USD"]["total_volume_24h"]),
            "top_gainers": top_gainers,
            "top_losers": top_losers,
        }
    except Exception as e:
        print(f"Помилка при отриманні даних: {e}")
        return {}


# Форматування великих чисел
def format_number(value):
    """
    Форматує великі числа у скороченому вигляді (млн, млрд, трлн).
    """
    try:
        value = float(value)
        if value >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}T"  # Трильйони
        elif value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"  # Мільярди
        elif value >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"  # Мільйони
        else:
            return f"{value:,.2f}"  # Залишити без змін для менших чисел
    except Exception as e:
        print(f"Помилка форматування числа: {e}")
        return "N/A"

def format_price(price):
    """
    Форматує ціну з відповідною кількістю десяткових знаків:
    - Якщо ціна >= 1: два десяткових знаки
    - Якщо 0.01 <= ціна < 1: чотири десяткових знаки
    - Якщо ціна < 0.01: вісім десяткових знаків
    """
    if price >= 1:
        return f"{price:.2f}"
    elif price >= 0.01:
        return f"{price:.4f}"
    else:
        return f"{price:.8f}"

# Форматування повідомлення
def format_message():
    data = get_crypto_data()

    if not data:
        return "Помилка: Дані про криптовалюти недоступні. Спробуйте пізніше."

    # Форматування топ зростання і падіння
    top_gainers = "\n".join(
        [f"🚀 {coin['symbol']}/USDT ~${format_price(coin['price'])} [+{coin['change']:.2f}%]"
         for coin in data["top_gainers"]]
    )
    top_losers = "\n".join(
        [f"🔻 {coin['symbol']}/USDT ~${format_price(coin['price'])} [{coin['change']:.2f}%]"
         for coin in data["top_losers"]]
    )

    return (
        f"Дата та час (Київ): 2025-03-18 14:38:45\n\n"
        f"💲 Ціна BTC: ~${format_price(data['btc_price'])} ({data['btc_change']:.2f}%)\n"
        f"💲 Ціна ETH: ~${format_price(data['eth_price'])} ({data['eth_change']:.2f}%)\n\n"
        f"💪 Домінація BTC: {data['btc_dominance']:.2f}%\n"
        f"💪 Домінація ETH: {data['eth_dominance']:.2f}%\n\n"
        f"📈 Топ 3 зростання за добу:\n{top_gainers}\n\n"
        f"📉 Топ 3 зниження за добу:\n{top_losers}\n\n"
        f"💰 Загальна капітализація ринку: ${data['total_market_cap']}\n"
        f"📊 Загальний об'єм за 24 години: ${data['total_volume']}\n"
    )

    return message


# Відправка оновлення в канал
async def send_update(context: ContextTypes.DEFAULT_TYPE):
    chat_id = '-1002620853264'  # ID вашого каналу
    message = format_message()
    await context.bot.send_message(chat_id=chat_id, text=message)


# Основна функція
def main():
    application = Application.builder().token("7739046482:AAEvEHReu3m-ttT3-UsD-7N-D0whSjRvnkU").build()
    application.add_handler(CommandHandler("start", start))

    job_queue = application.job_queue
    job_queue.run_repeating(send_update, interval=10, first=0)

    application.run_polling()


if __name__ == "__main__":
    main()