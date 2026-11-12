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
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"Failed to load page, status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text()
        
        target_phrase = "گرم ۱۸ عیار"
        pos = text_content.find(target_phrase)
        
        if pos != -1:
            snippet = text_content[pos:pos+70]
            print(f"Found snippet: {snippet}")
            
            words = snippet.split()
            for word in words:
                clean_word = "".join([c for c in word if c.isdigit()])
                if len(clean_word) > 5:  # پیدا کردن قیمت واقعی
                    # حذف کامل کلمات اضافی از عدد
                    price_cleaned = word.replace('عیار', '').replace('سکه‌بهار‌آزادی', '').strip()
                    return price_cleaned
                    
    except Exception as e:
        print(f"Error scraping price: {e}")
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
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
        # استفاده از فضای خالی (Space) به تعداد دلخواه برای فاصله گرفتن قیمت جدید
        spaces = "          "  # ۱۰ فاصله خالی
        message = f"🚨 قیمت طلا (گرم ۱۸ عیار) تغییر کرد!\n\nقیمت جدید:{spaces}*{current_price}*"
        send_telegram_message(message)
        
        # به‌روزرسانی فایل آخرین قیمت
        with open('last_price.txt', 'w', encoding='utf-8') as f:
            f.write(current_price)
    else:
        print("Price has not changed.")

if __name__ == "__main__":
    main()
