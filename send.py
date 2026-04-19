import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import re

from configparser import ConfigParser
import configparser


import mail_msg_config_db

global mail_server

config = ConfigParser()
config.read('app_config.ini', encoding='UTF8')


# *************************Mail config**************************************



def mail_config():
    global mail_server
    data = []
    mail_data = mail_msg_config_db.get_sms_details()
    for m in mail_data:
        data.append(m)
    api_key = data[1]['api_key']
    mail_server = data[1]['mail_server']    
    return [api_key, mail_server]

# ************************send notes***************************************



def send_to_mail(noteDetails):
    print('mail sending------------------------------------')
    print(config['Sendgrid']['FROM_MAIL'])
    message = Mail(
        from_email= config['Sendgrid']['FROM_MAIL'],
        to_emails= To(
            email= 'sraj81791.sm@gmail.com',  # update with your email - noteDetails['mail']
            name=noteDetails['mailer_name'],
            # substitutions={
            #     '-link-': 'https://www.google.com/',
            #     '-event-': 'Note added'
            # }
        ),
        subject= config['Sendgrid']['NOTE_SUB'] ,
        html_content="note added for PO# "+ noteDetails['retailer_po_no'] +" by " + noteDetails['sender'] + "<br>click here for " + "<a href = '"+config['Sendgrid']['ORDER_URL']+noteDetails['retailer_po_no']+"'>"+"Order Summary"+ "</a>" )
    try:
        mail_info = mail_config()
        sg = SendGridAPIClient(mail_info[0])
        mail_server = mail_info[1]
        response = sg.send(message)
    except Exception as e:
        print(str(e))
    else:
        print(response.status_code)
    return 

# ************************send to Amarr**************************************

def send_to_amarr(sendData):
    message = Mail(
         from_email=config['Sendgrid']['FROM_MAIL'],
        to_emails=sendData['mail'],
        subject= config['Sendgrid']['ORDER_SUBMITTED'] ,
        html_content='order submitted for '+ sendData['po_no'] + ' at ' + sendData['time'] )
    try:
        mail_info = mail_config()
        sg = SendGridAPIClient(mail_info[0])
        mail_server = mail_info[1]

        response = sg.send(message)
        print('-------------'+response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(str(e))
    else:
        print(str(response.status_code))
    return 

# ************************Send to Consumer************************************

def send_to_consumer(sendData):
    message = Mail(
        from_email=config['Sendgrid']['FROM_MAIL'],
        to_emails=sendData['mail'],
        subject= sendData['sub'] ,
        html_content= sendData['msg']

        )
    try:
        mail_info = mail_config()
        sg = SendGridAPIClient(mail_info[0])
        response = sg.send(message)
        
    except Exception as e:
        print(str(e))
    else:
        print(str(response.status_code))
    return 

# **************************Send to DC****************************************

def send_to_dc(sendData):
    message = Mail(
        from_email=config['Sendgrid']['FROM_MAIL'],
        to_emails=sendData['dc_mail'],
        subject= sendData['sub'] ,
        html_content= sendData['msg']

        )
    try:
        mail_info = mail_config()
        sg = SendGridAPIClient(mail_info[0])
        response = sg.send(message)
        
    except Exception as e:
        print(str(e))
    else:
        print(str(response.status_code))
    return 

# **********************Send to Contractor*********************************

def send_to_contractor(sendData):
    message = Mail(
        from_email=config['Sendgrid']['FROM_MAIL'],
        to_emails=sendData['con_mail'],
        subject= sendData['sub'] ,
        html_content= sendData['msg']

        )
    try:
        mail_info = mail_config()
        sg = SendGridAPIClient(mail_info[0])
        response = sg.send(message)
        
    except Exception as e:
        print(str(e))
    else:
        print(str(response.status_code))
    return 