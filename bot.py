import os
import requests
from bs4 import BeautifulSoup

# دریافت اطلاعات از Secrets گیت‌هاب
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# آدرس وب‌سایت‌ها
URL_AYAAR = 'https://ayaar.ir'
URL_ALANCHAND = 'https://alanchand.com/en'

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
                    return word.replace('عیار', '').replace('سکه‌بهار‌آزادی', '').strip()
    except Exception as e:
        print(f"Error scraping Ayaar: {e}")
    return "نامشخص"

def get_alanchand_data():
    gold_18k = "نامشخص"
    usd_price = "نامشخص"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(URL_ALANCHAND, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            # استخراج طلای ۱۸ عیار از سایت الان‌چند
            pos_gold = text_content.find("18K Gold")
            if pos_gold != -1:
                snippet_gold = text_content[pos_gold:pos_gold+50]
                for word in snippet_gold.split():
                    clean_word = "".join([c for c in word if c.isdigit()])
                    if len(clean_word) > 5:
                        gold_18k = word.strip()
                        break
            
            # استخراج قیمت دلار از سایت الان‌چند
            pos_usd = text_content.find("US Dollar")
            if pos_usd != -1:
                snippet_usd = text_content[pos_usd:pos_usd+50]
                for word in snippet_usd.split():
                    clean_word = "".join([c for c in word if c.isdigit()])
                    if len(clean_word) > 5:
                        usd_price = word.strip()
                        break
                        
    except Exception as e:
        print(f"Error scraping Alanchand: {e}")
        
    return gold_18k, usd_price

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
    
    # ترکیب مقادیر برای سنجش تغییرات
    current_combined = f"{price_ayaar}_{price_alanchand_gold}_{price_dollar}"

    # خواندن آخرین وضعیت ذخیره شده
    last_combined = ""
    if os.path.exists('last_price.txt'):
        with open('last_price.txt', 'r', encoding='utf-8') as f:
            last_combined = f.read().strip()

    print(f"Current -> Ayaar: {price_ayaar} | Alan 18K: {price_alanchand_gold} | USD: {price_dollar}")

    # اگر تغییری در هر کدام از قیمت‌ها ایجاد شده باشد
    if current_combined != last_combined:
        spaces = "          "  # ۱۰ فاصله خالی برای تفکیک قیمت‌ها
        message = (
            f"🚨 **گزارش تغییرات بازار طلا و ارز**\n\n"
            f"🔹 طلای ۱۸ عیار (سایت عیار):{spaces}*{price_ayaar}*\n"
            f"🔸 طلای ۱۸ عیار (الان‌چند):{spaces}*{price_alanchand_gold}*\n"
            f"💵 قیمت دلار (الان‌چند):{spaces}*{price_dollar}*"
        )
        send_telegram_message(message)
        
        # به‌روزرسانی فایل ذخیره قیمت‌ها
        with open('last_price.txt', 'w', encoding='utf-8') as f:
            f.write(current_combined)
    else:
        print("Prices have not changed.")

if __name__ == "__main__":
    main()
