import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtpObj  = smtplib.SMTP('smtp.gmail.com', 587)
smtpObj.starttls()

def send_email(to_addr, title, text):
    from_addr = "russianrise.supp@gmail.com"
    message = MIMEMultipart("alternative")
    message["Subject"] = title
    message["From"] = from_addr
    message["To"] = to_addr
    body = f"""
<!DOCTYPE html>
    <html>
        <body>
            <p>
                {text}
            </p>
        </body>
    </html>
    """
    message.attach(MIMEText(body, "html"))
    
    smtpObj.login('russianrise.supp@gmail.com','voshodroot7359')
    smtpObj.sendmail(from_addr, to_addr, message.as_string())