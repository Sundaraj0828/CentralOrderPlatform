import os
from twilio.rest import Client
from configparser import ConfigParser
import configparser

import mail_msg_config_db

config = ConfigParser()
config.read('app_config.ini', encoding="utf8")



# *************************Msg config**************************************

def msg_config():
    global mail_server
    data = []
    account_sid = ''
    auth_token = ''
    
    mail_data = mail_msg_config_db.get_sms_details()
    for m in mail_data:
        data.append(m)
    if data[0]['account_name'] == 'Twilio':
        account_sid = data[0]['account_sid_no']
        auth_token = data[0]['auth_token']    
    return [account_sid, auth_token]


# *************************************************************************


#add the function send_mail(sms_info)
def send_msg(password,phone):	
	msg_info = msg_config()
	account_sid = msg_info[0]
	auth_token = msg_info[1]
	client = Client(account_sid, auth_token)
	message='Your new password is: ' + password
	prefix = '+91'
	num=prefix + phone
	message = client.messages.create(
	                              body=message,
	                              from_=config['sms']['FROM'],
	                              to=num
	                              )
	return




def send_to_cons(sendData):
	msg_info = msg_config()
	account_sid = msg_info[0]
	auth_token = msg_info[1]
	client = Client(account_sid, auth_token)
	message= sendData['msg']
	prefix = '+1'
	num=prefix + sendData['number']
	print(num)
	message = client.messages.create(
	                              body=message,
	                              from_=config['sms']['FROM'],
	                              to=num
	                          )
	return



def send_to_dc(sendData):
	msg_info = msg_config()
	account_sid = msg_info[0]
	auth_token = msg_info[1]
	client = Client(account_sid, auth_token)
	message= sendData['msg']
	prefix = '+1'
	num=prefix + sendData['dc_number']
	message = client.messages.create(
	                              body=message,
	                              from_=config['sms']['FROM'],
	                              to=num
	                          )
	return

def send_to_contractor(sendData):
	msg_info = msg_config()
	account_sid = msg_info[0]
	auth_token = msg_info[1]
	client = Client(account_sid, auth_token)
	message= sendData['msg']
	prefix = '+1'
	num=prefix + sendData['con_number']
	message = client.messages.create(
	                              body=message,
	                              from_=config['sms']['FROM'],
	                              to=num
	                          )
	return







