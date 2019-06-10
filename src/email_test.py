import smtplib, ssl # Sends email securely
from email.message import EmailMessage

msg = EmailMessage()
msg.set_content("""Hey Syris,

It's just me, testing sending emails using Python. Let's see if you receive this!

Best, 
Yourself""")

sender_email = "dunno@"
receiver_email = "csgomarketrequests@gmail.com"

port = 465
password = input("Type your password and press enter: ")

# Create a secure SSL context
context = ssl.create_default_context()

with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login("csgomarketrequests@gmail.com", password)
    server.sendmail(sender_email, receiver_email, msg)
