import os
import requests
from bs4 import BeautifulSoup

# دریافت اطلاعات از Secrets گیت‌هاب
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# آدرس وب‌سایت مد نظر شما
URL = 'https://example.com/gold-price' # آدرس سایت خود را اینجا وارد کنید

def get_gold_price():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TODO: سلول یا المان دقیق قیمت را با CSS Selector سایت خودتان تنظیم کنید
        price_element = soup.select_one('.gold-price-class') 
        
        if price_element:
            return price_element.text.strip()
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
        message = f"🚨 قیمت طلا تغییر کرد!\n\nقیمت جدید: {current_price}"
        send_telegram_message(message)
        
        # به‌روزرسانی فایل آخرین قیمت
        with open('last_price.txt', 'w', encoding='utf-8') as f:
            f.write(current_price)
    else:
        print("Price has not changed.")

if __name__ == "__main__":
    main()
