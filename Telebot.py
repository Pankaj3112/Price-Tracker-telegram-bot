from telebot import types
import telebot
from Pricescrape import fetch_price
import re
import pymongo
from Myemail import sendemail
import creds


bot = telebot.TeleBot(creds.API_KEY_telebot)

#create empty dictionary to store all the info from user
user_dict = {"urls":{}}

#accesing the database
myclient = pymongo.MongoClient("mongodb+srv://pankaj3112:shivaniisbad@cluster0.6tkvnt5.mongodb.net/test")
mydb = myclient["telebot"]
mycollection = mydb["userinfo"]

print('Bot started')


#function to check if data for this user exists
def check_id_exist(id):
    if mycollection.count_documents({"_id":id}) > 0:
        print("check id working")
        return True

    else:
        return False


#-----------------handling Start,Help----------------------
@bot.message_handler(commands=['start','help'])
def welcome_message(message):
    id = message.from_user.id
    name = message.from_user.first_name
    bot.reply_to(message,f'Hi {name}, I am Price Tracker Bot.\n\
You can simply send a amazon link to start tracking a product.\n\n\
You can control me by sending these commands:\n\n\
/show_alert_list - to get list of products you have set alert for\n\
/del_alert - to choose an item that you dont want alerts now\n\
/alert_prefrence - to change where to receive alerts')

#-------------------handling alert_list----------------------
@bot.message_handler(commands=['show_alert_list'])
def list(message):
    id = message.from_user.id

    if check_id_exist(id) == True:
        document = mycollection.find_one({"_id":id})
        urls = document["urls"]

        if len(urls) > 0:
            index = 1
            for i in urls:
                for title,price in i.items():
                    bot.send_message(id,f"{index}.){title}\nAlert price: {price}")
                    index += 1

        else:
            bot.send_message(id,f"Nothing to show here.\nPlease send amazon link of the product to start tracking.")

    else:
        bot.send_message(id,f"Sorry we have no data for you.\nPlease send amazon link of the product to start tracking.")


#----------------------handling del_from list--------------------
@bot.message_handler(commands=['del_alert'])
def list(message):
    id = message.from_user.id
    document = mycollection.find_one({"_id":id})
    urls = document["urls"]

    if check_id_exist(id) == True and len(urls) > 0:
        document = mycollection.find_one({"_id":id})
        urls = document["urls"]
        
        index = 1
        for i in urls:
            for title,price in i.items():
                bot.send_message(id,f"{index}.){title}\nAlert price: {price}")
                index += 1

        msg = bot.send_message(id,f"Choose an item from above to delete alert for.\ni.e. 1 for first,2 for second item.")
        bot.register_next_step_handler(msg,delete_alert)


    else:
        bot.send_message(id,f"Sorry nothing to show here.\nPlease send amazon link of the product to start tracking.")


def delete_alert(message):
    choice = message.text
    id = message.from_user.id
    document = mycollection.find_one({"_id":id})
    urls = document["urls"]

    if choice.isdigit() and 0 < int(choice) <= len(urls):
        urls.pop(int(choice)-1)
        mycollection.replace_one({"_id":id},document)

        bot.send_message(id,f"Item deleted successfully.")

    else:
        msg = bot.reply_to(message,f'Choice should be an number b\w 1 and {len(urls)}')
        bot.register_next_step_handler(msg,delete_alert)
        return

#------------------------handling alert prefrence---------------------------
@bot.message_handler(commands=["alert_prefrence"])
def choose_alert_prefrence(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Telegram','Email')
    msg = bot.reply_to(message,"Please tell me if you want to get updates on your Email or Telegram.",reply_markup=markup)

    bot.register_next_step_handler(msg,set_alert_choice)


def set_alert_choice(message):
    choice = message.text
    id = message.from_user.id

    if check_id_exist(id) == True:

        if choice == u"Telegram":
            mycollection.update_one({"_id":id},{"$set":{"choice":"telegram"}})

            bot.reply_to(message,'Okay,I will send you alert for price drops on Telegram')
            bot.send_message(id,'Note:\nYou need to send atleast one message to Alert bot (t.me/AmazonAlertByPankajBot)\nTo receive alerts on telegram\n\nIgnore if already done.')


        elif choice == u"Email":
            document = mycollection.find_one({"_id":id})
            if document["email"] != "None":
                mycollection.update_one({"_id":id},{"$set":{"choice":"email"}})

                bot.reply_to(message, f'okay,I will send you alert for price drops on your email {document["email"]}')
                
                
            else:
                msg = bot.reply_to(message, "Please input your Email address")
                bot.register_next_step_handler(msg,set_email_manual)
        
        else:
            msg = bot.reply_to(message,'Please type Telegram or Email.')
            bot.register_next_step_handler(msg,set_alert_choice)

    else:
        bot.send_message(id,"Sorry we have no data for you.\n\nPlease send amazon link to start tracking products.")

def set_email_manual(message):
    email = message.text
    id = message.from_user.id

    if sendemail(email,"This email is just to check if your email is able to receive alerts.") == True:
        mycollection.update_one({"_id":id},{"$set":{"email":email}})

        bot.reply_to(message, f'okay,I will send you alert for price drops on your email {email}')

    else:
        msg = bot.reply_to(message,'Please type a valid email address.')
        bot.register_next_step_handler(msg,set_email)

    

#---------------Checking if message contains amazon link and fetching data for it-----------------
def check_amazon_link(message):
    request = message.text
    if 'www.amazon.in' in request or '://amzn.' in request:
        return True
    else:
        return False

@bot.message_handler(func= check_amazon_link)
def get_product_info(message):
    global url
    global name
    global price_details

    bot.send_message(message.chat.id,f"Retrieving product information...")

    links = re.findall(r'(https?://\S+)',message.text)
    url = links[0]
    name = message.from_user.first_name

    price_details = fetch_price(url)
    #telling the current price to the user
    bot.send_message(message.chat.id,f"{price_details[1]}\n\nCurrent Price: {price_details[0]}")
    #asking for the target price
    msg = bot.reply_to(message,"Please tell me the price,you want to be notified for.")
    bot.register_next_step_handler(msg,asking_target_price)


#--------------------------getting the alert price from the user------------------------
def asking_target_price(message):
    global target_price
    target_price = message.text
    if not target_price.isdigit():
        msg = bot.reply_to(message,'Price should be an integer value/number.')
        bot.register_next_step_handler(msg,asking_target_price)
        return
    

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Telegram','Email')
    msg = bot.reply_to(message,"Please tell me if you want to get updates on your Email or Telegram.",reply_markup=markup)

    bot.register_next_step_handler(msg,alert_choice)


#-----------------user chooses the preffred alert choice --------------------
def alert_choice(message):
    global id
    choice = message.text
    id = message.from_user.id

    if choice == u'Telegram':
        bot.reply_to(message,'Okay,I will send you alert for price drops on Telegram')
        bot.send_message(id,'Note:\nYou need to send atleast one message to Alert bot (t.me/AmazonAlertByPankajBot)\nTo receive alerts on telegram\n\nIgnore if already done.')

        if check_id_exist(id) == True:
            link_price = {"$push":{"urls":{url:target_price}}}
            mycollection.update_one({"_id":id},link_price)
            mycollection.update_one({"_id":id},{"$set":{"choice":"telegram"}})

        else:
             mycollection.insert_one({
            "_id":id,
            "name":name,
            "email":"None",
            "urls":[{url:target_price}],
            "choice":"telegram"
        })



    elif choice == u'Email':
        document = mycollection.find_one({"_id":id})

        if check_id_exist(id) == True and document["email"] != "None":
                link_price = {"$push":{"urls":{url:target_price}}}
                mycollection.update_one({"_id":id},link_price)
                mycollection.update_one({"_id":id},{"$set":{"choice":"email"}})

                bot.reply_to(message, f'okay,I will send you alert for price drops on your email {document["email"]}')
                
                

        else:
            msg = bot.reply_to(message, "Please input your Email address")
            bot.register_next_step_handler(msg,set_email)
            
    else:
        msg = bot.reply_to(message,'Please type a valid Option')
        bot.register_next_step_handler(msg,alert_choice)

#---------------------fuction to set email if it not in the database--------------
def set_email(message):
    global email
    email = message.text

    if sendemail(email,"This email is just to check if your email is able to receive alerts.") == True:
        bot.reply_to(message, f'okay,I will send you alert for price drops on your email {email}')
        

    else:
        msg = bot.reply_to(message,'Please type a valid email address.')
        bot.register_next_step_handler(msg,set_email)

    add_to_db()


#------------------adding user details and prefrence to the database----------------
def add_to_db():
    document = {
            "_id":id,
            "name":name,
            "email":email,
            "urls":[{url:target_price}],
            "choice":"email"
        }

    if check_id_exist(id) == False:
        mycollection.insert_one(document)
       
    
    else:
        mycollection.replace_one({"_id":id},document)
        

bot.enable_save_next_step_handlers(delay=2)    
bot.load_next_step_handlers  

bot.infinity_polling()