import pymongo
from Pricescrape import fetch_price
from Myemail import sendemail
import telebot
import time
import creds

myclient = pymongo.MongoClient("mongodb+srv://pankaj3112:shivaniisbad@cluster0.6tkvnt5.mongodb.net/test")
mydb = myclient["telebot"]
mycollection = mydb["userinfo"]

bot = telebot.TeleBot(creds.API_KEY_alert)

print("Alert bot started")

#-----------------running a while loop to compare the prices every 12 hours---------------------------

while True:
    for document in mycollection.find({},{"_id":1,"name":1,"email":1,"choice":1,"urls":1}):
        doc_id = document["_id"]
        urls = document["urls"]
        choice = document["choice"]
        email = document["email"]
        name = document["name"]


        for item in urls:
            for link , target_price in item.items():
                latest_price = fetch_price(link)[0]

                if latest_price <= float(target_price):
                    item_title = fetch_price(link)[1]
                    alert = f"Alert!!!\nHello {name} price dropped for\n{item_title}\nCurrent Price: {latest_price}"

                    if choice == "telegram":
                        bot.send_message(int(doc_id),alert)

                        for i in range(len(urls)):
                            urls[:] = [d for d in urls if d.get(link) != target_price]
                                
                            mycollection.replace_one({"_id":doc_id},document)
                

                    elif choice == "email":
                        sendemail(email,alert)

                        for i in range(len(urls)):
                            urls[:] = [d for d in urls if d.get(link) != target_price]
                                
                            mycollection.replace_one({"_id":doc_id},document)
                
                else:
                    continue
            
    time.sleep(60*60*12) #You can change sleep duration as your prefrence

#Pymongo $pull was not working for some reason so i saved the whole document in a variable.
#Then updated that variable and replaced the whole document with this variable.