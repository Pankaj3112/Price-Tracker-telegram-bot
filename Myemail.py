import ssl
import smtplib
from email.message import EmailMessage
import creds 

def sendemail(receiver,body):
    emailsender = 'pankajbeniwal3112@gmail.com'
    #This password is not your actual email pw,
    # you need to enable 2factor authentication and make a app password from google site
    emailpw = creds.emailpassword
    email_receiever = receiver
    subject = "Alert from Telegram Amazon tracker"
    

    em = EmailMessage()
    em['From'] = emailsender
    em['To'] = email_receiever
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
        smtp.login(emailsender,emailpw)
        smtp.sendmail(emailsender,email_receiever,em.as_string())
    
    return True

