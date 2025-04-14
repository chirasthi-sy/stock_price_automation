from config import app_password

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import os


def get_data():
    url = 'https://finance.yahoo.com/quote/AAPL/?p=AAPL'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)
    print(response)

    soup = BeautifulSoup(response.text, 'html.parser')

    # current data
    data1 = soup.find('span', {'data-testid': 'qsp-price'})
    current_price = float(data1.text)

    data2 = datetime.now()
    current_date = pd.to_datetime(data2)

    data3 = soup.find('h3', string=re.compile(r'Statistics: '))
    ticker_list = data3.text.split(sep=': ')
    ticker = ticker_list[1]

    path = "C:/Users/HP/Downloads/EY/stock_data.csv"
    row = {'Date': current_date, 'Company': ticker, 'Price': current_price}

    if os.path.exists(path):
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df[df['Company'] == ticker]
        if not df.empty:
            latest_row = df[df['Date'] == df['Date'].max()].iloc[0]
            previous_price = latest_row['Price']
            price_difference = current_price - previous_price
            percentage_change = price_difference / previous_price
        else:
            previous_price = price_difference = percentage_change = None
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
        previous_price = price_difference = percentage_change = None

    df.to_csv(path, index=False)
    return current_price, current_date, ticker, price_difference, percentage_change


current_price, current_date, ticker, price_difference, percentage_change = get_data()

threshold = 0.05

if percentage_change is not None and abs(percentage_change) >= threshold:
    sender_email = "chirasthi.sy@gmail.com"
    receiver_email = "amarasinghacu.20@uom.lk"
    app_password = app_password

    subject = f"AAPL Price Alert - {current_date.strftime('%Y-%m-%d')}"

    body = f"""
    Hello,

    The update for Apple (AAPL) stock is as follows:

    Date: {current_date.strftime('%Y-%m-%d')}
    Current Price: ${current_price:.2f}
    Price Change: ${price_difference:.2f}
    Percentage Change: {percentage_change * 100:.2f}%

    This price change has exceeded your threshold of ${threshold}.

    Regards,

    Stock Price Alert
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
else:
    print("Price change below threshold. No email sent.")
