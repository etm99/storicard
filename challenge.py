"""
Developer: Eduardo Torres Mar
Description: This script read a file, process the information then
create a csv with this information and send an email
Last update: September 7 2021
"""

import pandas
import os
import sqlite3
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def process(file_name, account):
    print("Processing data")
    #dynamic path
    full_path = str(os.path.dirname(os.path.realpath(__file__))) + r"//" + file_name
    data = pandas.read_csv(full_path, sep = ',', dtype = str)
    data['dt'] = pandas.to_datetime(data['Date'], format = '%m/%d')
    data['Month'] = data['dt'].dt.strftime('%B')
    data['Day'] = data['dt'].dt.strftime('%d')
    data['Credit_Type'] = data['Transaction'].apply(lambda x: 'Credit' if float(x) > 0 else 'Debit')
    data['Account'] = account
    #delete columns
    del data['dt']
    del data['Date']
    #create a csv with data
    output_file = 'data.csv'
    data.to_csv(output_file, index=False)
    #Connecting into DB
    db_conn = sqlite3.connect('db_storicard')
    db_cursor = db_conn.cursor()
    condition_account = f"""WHERE "Account" == '{account}'"""
    db_cursor.execute("""CREATE TABLE IF NOT EXISTS "transactions"
    ("Id" number, "Transaction" number, "Month" text, "Day" number, "Credit_Type" text, "Account" text)""")
    db_conn.commit()
    ## NOTE: change the replace dependig of the requirement
    data.to_sql('transactions', db_conn, if_exists='replace', index = False)
    #Creating queries
    db_cursor.execute('SELECT SUM("Transaction") FROM "transactions" ' + condition_account)
    total_transaction = db_cursor.fetchall()

    db_cursor.execute(f"""SELECT "Month",count("Credit_Type") FROM "transactions" {condition_account} GROUP BY "Month" """)
    list_month_ctype = db_cursor.fetchall()

    db_cursor.execute(f"""SELECT AVG("Transaction") FROM "transactions" {condition_account} AND "Credit_Type" = 'Debit'""")
    avg_debit = db_cursor.fetchall()

    db_cursor.execute(f"""SELECT AVG("Transaction") FROM "transactions" {condition_account} AND "Credit_Type" = 'Credit'""")
    avg_credit = db_cursor.fetchall()
    text_body_email = """<body><img src="stori_logo.png">
        <p>Hello attached is the detailed data for your transactions and
        below is your transaction summary.</p>"""

    text_body_email = text_body_email + f"<p>Total balance is {total_transaction[0][0]}</p>"
    for n_month in list_month_ctype:
        text_body_email = text_body_email + f"<p>Number of transaction in {n_month[0]}: {n_month[1]}</p>"
    text_body_email = text_body_email + f"<p>Average debit amount: {avg_debit[0][0]}</p>"
    text_body_email = text_body_email + f"<p>Average credit amount: {avg_credit[0][0]}</p>"
    text_body_email = text_body_email + "</body>"
    #send_email(account, text_body_email, output_file)

def send_email(account, body_html, output_file):
    print("Sending email")
    msg = MIMEMultipart()
    msg['Subject'] = "Transactions summary"
    body = MIMEText(body_html, 'html')
    msg.attach(body)
    #Add file
    full_path = str(os.path.dirname(os.path.realpath(__file__))) + r"//" + output_file
    file_to_attach = MIMEApplication(open(full_path,"rb").read())
    file_to_attach.add_header('Content-Distribution','attachment', filename = output_file)
    msg.attach(file_to_attach)
    server_port = 587 #This is an example
    server = smtplib.SMTP("smtp.storicard.com", server_port)
    server.ehlo()
    server.strtls()
    server.login("tools_storicard", "ToolsPassword@123")
    server.sendmail("tools_storicard@storicard.com", account, msg.as_string())
    server.quit()

account = 'etm1995@hotmail.com'
file_name = "txns.csv"
process(file_name, account)
