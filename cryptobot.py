from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from datetime import datetime, timezone
from pytz import timezone
import ccxt


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я ваш криптобот. Я буду надсилати оновлення в канал кожні 10 секунд.")


# Отримання індексу страху та жадібності
def get_fear_greed_index():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url)
        data = response.json()

        # Переклад значень індексу страху та жадібності
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
def get_crypto_data():
    try:
        exchange = ccxt.binance()

        # Отримання даних про BTC і ETH
        btc = exchange.fetch_ticker('BTC/USDT')
        eth = exchange.fetch_ticker('ETH/USDT')

        # Отримання даних про капіталізацію
        market_data = requests.get('https://api.coingecko.com/api/v3/global').json()

        # Отримання топ зростання і падіння тільки для пар з USDT
        tickers = exchange.fetch_tickers()
        changes = [
            (symbol, ticker['last'], ticker['percentage'])
            for symbol, ticker in tickers.items()
            if ticker.get('percentage') is not None and symbol.endswith('/USDT')  # Фільтр для пар з USDT
        ]

        top_gainers = sorted(changes, key=lambda x: x[2], reverse=True)[:3]
        top_losers = sorted(changes, key=lambda x: x[2])[:3]

        return {
            'btc_price': btc['last'],
            'btc_change': btc['percentage'],
            'eth_price': eth['last'],
            'eth_change': eth['percentage'],
            'btc_market_cap': market_data['data']['total_market_cap']['btc'],
            'eth_market_cap': market_data['data']['total_market_cap']['eth'],
            'btc_dominance': market_data['data']['market_cap_percentage']['btc'],
            'eth_dominance': market_data['data']['market_cap_percentage']['eth'],
            'total_market_cap': market_data['data']['total_market_cap']['usd'],
            'total_volume': market_data['data']['total_volume']['usd'],
            'top_gainers': top_gainers,
            'top_losers': top_losers
        }
    except Exception as e:
        print(f"Помилка при отриманні даних: {e}")
        return {}

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
            return f"{value:.2f}"  # Залишити без змін для менших чисел
    except Exception as e:
        print(f"Помилка форматування числа: {e}")
        return "N/A"

# Форматування повідомлення
def format_message():
    data = get_crypto_data()
    fear_greed = get_fear_greed_index()

    # Використання київського часу
    kyiv_tz = timezone('Europe/Kiev')
    current_time = datetime.now(kyiv_tz).strftime('%Y-%m-%d %H:%M:%S')

    message = (
        f"Дата та час (Київ): {current_time}\n\n"
        f"💲 Ціна BTC: ~${data['btc_price']:.2f} ({data['btc_change']}%)\n"
        f"💲 Ціна ETH: ~${data['eth_price']:.2f} ({data['eth_change']}%)\n\n"
        f"💪 Домінація BTC: {data['btc_dominance']:.2f}%\n"
        f"💪 Домінація ETH: {data['eth_dominance']:.2f}%\n\n"
        f"😨 Індекс страху та жадібності: {fear_greed['value']} ({fear_greed['value_classification']})\n\n"
        f"📈 Топ 3 зростання за добу:\n"
    )

    for gainer in data['top_gainers']:
        message += f"🚀 {gainer[0]}   ~${gainer[1]:.2f}   [+{gainer[2]:.2f}%]\n"

    message += "\n📉 Топ 3 зниження за добу:\n"
    for loser in data['top_losers']:
        message += f"🔻 {loser[0]}   ~${loser[1]:.2f}   [{loser[2]:.2f}%]\n"

    message += (
        f"\n💰 Загальна капітализація ринку: {format_number(data['total_market_cap'])}\n"
        f"📊 Загальний об'єм за 24 години: {format_number(data['total_volume'])}\n"
    )

    return message


# Відправка оновлення в канал
async def send_update(context: ContextTypes.DEFAULT_TYPE):
    chat_id = '-1002620853264'  # ID вашого каналу
    message = format_message()
    await context.bot.send_message(chat_id=chat_id, text=message)


# Основна функція
def main():
    # Створіть об'єкт Application
    application = Application.builder().token("7739046482:AAEvEHReu3m-ttT3-UsD-7N-D0whSjRvnkU").build()

    # Додайте обробник команд
    application.add_handler(CommandHandler("start", start))

    # Налаштуйте JobQueue для періодичних оновлень
    job_queue = application.job_queue
    job_queue.run_repeating(send_update, interval=10, first=0)  # Інтервал 10 секунд

    # Запустіть бота
    application.run_polling()


if __name__ == "__main__":
    main()