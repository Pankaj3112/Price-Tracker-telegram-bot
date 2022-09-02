from bs4 import BeautifulSoup
import requests

def fetch_price(url):
    try:
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/104.0.0.0 Safari/537.36"}

        page = requests.get(url,headers=headers)

        soup = BeautifulSoup(page.text,'html.parser')

    #fetching title
        title = soup.select_one('span#productTitle').get_text()
        title = title.strip()
    #fetching price and cleaning it
        price = soup.select_one('span.a-offscreen').get_text()
        price = price.replace(",","")
        price = price.replace("₹","")
        
        
        return(float(price),title)

    except:
        print("some error occured while fetching price")
