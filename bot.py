import os
import json
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = "-1004461570949"

URL_AYAAR = 'https://ayaar.ir'
URL_ALANCHAND = 'https://alanchand.com/en'

CACHE_FILE = 'prices.json'

def load_previous_prices():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_current_prices(prices_dict):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(prices_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving prices: {e}")

def convert_to_english_digits(text):
    english_digits = '0123456789'
    for p, e in zip('۰۱۲۳۴۵۶۷۸۹', english_digits):
        text = text.replace(p, e)
    for a, e in zip('٠١ي٢٣٤٥٦٧٨٩', english_digits):
        text = text.replace(a, e)
    return text

def get_ayaar_gold():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(URL_AYAAR, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        target_phrase = "گرم ۱۸ عیار"
        pos = text_content.find(target_phrase)
        if pos != -1:
            snippet = text_content[pos:pos+70]
            words = snippet.split()
            for word in words:
                clean_word = "".join([c for c in word if c.isdigit()])
                if len(clean_word) > 5:
                    raw_price = word.replace('عیار', '').replace('سکه‌بهار‌آزادی', '').strip()
                    return convert_to_english_digits(raw_price)
    except Exception as e:
        print(f"Error scraping Ayaar: {e}")
    return None

def get_alanchand_data():
    gold_18k = None
    usd_price = None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(URL_ALANCHAND, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            for keyword in ["18K gold", "18K Gold per G"]:
                pos_gold = text_content.find(keyword)
                if pos_gold != -1:
                    snippet = text_content[pos_gold:pos_gold+80]
                    for word in snippet.split():
                        clean_word = "".join([c for c in word if c.isdigit()])
                        if len(clean_word) >= 8:
                            val_eng = convert_to_english_digits(word.strip().replace(',', ''))
                            if val_eng.isdigit():
                                adjusted_val = val_eng[:-1] if len(val_eng) > 1 else val_eng
                                gold_18k = f"{int(adjusted_val):,}"
                            break
                    if gold_18k is not None:
                        break
            pos_usd = text_content.find("US dollar")
            if pos_usd == -1:
                pos_usd = text_content.find("US Dollar")
            if pos_usd != -1:
                snippet_usd = text_content[pos_usd:pos_usd+80]
                for word in snippet_usd.split():
                    clean_word = "".join([c for c in word if c.isdigit()])
                    if len(clean_word) >= 7:
                        val_eng = convert_to_english_digits(word.strip().replace(',', ''))
                        if val_eng.isdigit():
                            adjusted_val = val_eng[:-1] if len(val_eng) > 1 else val_eng
                            usd_price = f"{int(adjusted_val):,}"
                        break
    except Exception as e:
        print(f"Error scraping Alanchand: {e}")
    return gold_18k, usd_price

def format_price_with_trend(price_str, cache_key, previous_prices):
    if not price_str or price_str == "نامشخص":
        return "نامشخص"
    try:
        current_val = int(price_str.replace(',', ''))
    except ValueError:
        return price_str
        
    old_val = previous_prices.get(cache_key)
    
    if old_val is None:
        return f"{price_str}"
        
    if current_val > old_val:
        return f"{price_str} 🟢 ⬆️"
    elif current_val < old_val:
        return f"{price_str} 🔴 ⬇️"
    else:
        return f"{price_str}"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def main():
    price_ayaar = get_ayaar_gold()
    price_alanchand_gold, price_dollar = get_alanchand_data()
    
    current_combined = f"{price_ayaar}_{price_alanchand_gold}_{price_dollar}"
    
    previous_prices = load_previous_prices()
    
    new_prices_cache = {}
    if price_ayaar:
        try: new_prices_cache['ayaar'] = int(price_ayaar.replace(',', ''))
        except: pass
    if price_alanchand_gold:
        try: new_prices_cache['alan_gold'] = int(price_alanchand_gold.replace(',', ''))
        except: pass
    if price_dollar:
        try: new_prices_cache['dollar'] = int(price_dollar.replace(',', ''))
        except: pass

    github_event = os.environ.get('GITHUB_EVENT_NAME', '')
    is_manual_trigger = (github_event == 'workflow_dispatch')

    last_combined = ""
    if os.path.exists('last_price.txt'):
        with open('last_price.txt', 'r', encoding='utf-8') as f:
            last_combined = f.read().strip()

    if current_combined != last_combined or is_manual_trigger:
        f_ayaar = format_price_with_trend(price_ayaar, 'ayaar', previous_prices)
        f_alan_gold = format_price_with_trend(price_alanchand_gold, 'alan_gold', previous_prices)
        f_dollar = format_price_with_trend(price_dollar, 'dollar', previous_prices)

        message = (
            f"🚨 *گزارش تغییرات بازار طلا و ارز*\n\n"
            f"🔹 *طلای ۱۸ عیار (سایت عیار):*\n`{f_ayaar}`\n\n"
            f"🔸 *طلای ۱۸ عیار (الان‌چند):*\n`{f_alan_gold}`\n\n"
            f"💵 *قیمت دلار (الان‌چند):*\n`{f_dollar}`"
        )
        
        send_telegram_message(message)
        
        save_current_prices(new_prices_cache)
        
        with open('last_price.txt', 'w', encoding='utf-8') as f:
            f.write(current_combined)
    else:
        print("Prices have not changed.")

if __name__ == "__main__":
    main()
