import os
import requests
from bs4 import BeautifulSoup

# دریافت اطلاعات از Secrets گیت‌هاب
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# آدرس وب‌سایت
URL = 'https://ayaar.ir'

def get_gold_price():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.encoding = 'utf-8' # برای خوانایی بهتر متن‌های فارسی
        
        if response.status_code != 200:
            print(f"Failed to load page, status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # جستجو در کل متن صفحه برای پیدا کردن عبارت «گرم ۱۸ عیار»
        text_content = soup.get_text()
        
        # پیدا کردن موقعیت عبارت در متن صفحه
        target_phrase = "گرم ۱۸ عیار"
        pos = text_content.find(target_phrase)
        
        if pos != -1:
            # استخراج تکه‌ای از متن بعد از عبارت مورد نظر برای پیدا کردن قیمت
            snippet = text_content[pos:pos+50] # 50 کاراکتر بعد از عبارت
            print(f"Found snippet: {snippet}")
            
            # جدا کردن کلمات و اعداد استخراج شده
            words = snippet.split()
            # معمولاً عدد قیمت بلافاصله بعد از «گرم ۱۸ عیار» قرار می‌گیرد
            for word in words:
                # بررسی اینکه آیا کلمه شامل رقم است یا خیر
                if any(char.isdigit() for char in word):
                    return word
                    
    except Exception as e:
        print(f"Error scraping price: {e}")
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, json=payload)

def main():
    current_price = get_gold_price()
    if not current_price:
        print("Could not fetch price.")
        return

    # خواندن آخرین قیمت ذخیره شده
    last_price = ""
    if os.path.exists('last_price.txt'):
        with open('last_price.txt', 'r', encoding='utf-8') as f:
            last_price = f.read().strip()

    print(f"Current Price: {current_price} | Last Price: {last_price}")

    # مقایسه قیمت جدید با قیمت قبلی
    if current_price != last_price:
        message = f"🚨 قیمت طلا (گرم ۱۸ عیار) تغییر کرد!\n\nقیمت جدید: {current_price}"
        send_telegram_message(message)
        
        # به‌روزرسانی فایل آخرین قیمت
        with open('last_price.txt', 'w', encoding='utf-8') as f:
            f.write(current_price)
    else:
        print("Price has not changed.")

if __name__ == "__main__":
    main()
