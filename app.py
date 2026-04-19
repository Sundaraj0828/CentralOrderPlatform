from flask import Flask,render_template,redirect,request,session,flash,url_for,g
import datetime
import sys
import random
import time

# import os
from bson import ObjectId

from passlib.hash import sha256_crypt
from functools import wraps

import json
import string

import ASC_orderMgmt_db
import send
import sendSms
import mail_msg_config_db

from configparser import ConfigParser
import configparser

import pytz
import numpy as np

config = ConfigParser()
config.read('app_config.ini', encoding="utf8")

app = Flask(__name__)
app.config.update(SESSION_COOKIE_NAME = 'session_asc_order')

app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.config.from_object(__name__)
app.secret_key=config['SecretKey']['SECRET_KEY']



def generate_random_id(letters_count, digits_count):
    sample_str = ''.join((random.choice(string.ascii_letters) for i in range(letters_count)))
    sample_str += ''.join((random.choice(string.digits) for i in range(digits_count)))
    # Convert string to list 
    sample_list = list(sample_str)    
    final_string = ''.join(sample_list)
    return final_string

# Login required
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username_asc' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route("/logout/")
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/get_mail')
def get_retailer_mail():
	retailerRecords = []
	mail = ''

	rtlr_id = session['retailer_asc']
	retailerInfo = ASC_orderMgmt_db.get_retailer_info(rtlr_id)
	for r in retailerInfo:
		retailerRecords.append(r)
	
	mail = retailerRecords[0]['email_1']
	return mail

def generateCurrentDate():
	currentDT = datetime.datetime.now(pytz.timezone('US/Central'))
	date_time = currentDT.strftime("%Y %b %d %I:%M:%S%p")
	return date_time

def send_mail_to_cons(po_no, sendData):
	session['mail_to_cons'] = True
	send.send_to_consumer(sendData)
	changeLog(po_no)
	return

def send_mail_to_dc(po_no, sendData):
	session['mail_to_dc'] = True
	send.send_to_dc(sendData)
	changeLog(po_no)
	return

def send_mail_to_contractor(po_no, sendData):
	session['mail_to_cons'] = True
	send.send_to_contractor(sendData)
	changeLog(po_no)
	return

def send_msg_to_cons(po_no, sendData):
	session['msg_to_cons'] = True
	sendSms.send_to_cons(sendData)
	changeLog(po_no)
	return

def get_retailer():
	retailer_acc = []
	retailers = []
	all_retailers = ASC_orderMgmt_db.get_all_retailer_info()
	for r in all_retailers:
		retailer_acc.append(r)
	for ri in retailer_acc:
		retailers.append(ri)
	return retailers


def get_searchList():
	searchList = config['Search_by']['SEARCH_LIST'].split(', ')

@app.route('/')
@login_required
def index():
	return render_template('index.html', user = session['username_asc'])

@app.route('/retailer/<acc_id>')
@login_required
def retailer(acc_id):
	ret_info = []
	retailer_db = ''
	retailer_name = ''
	retailer_info = ASC_orderMgmt_db.get_retailer_info(acc_id)

	for r in retailer_info:
		ret_info.append(r)
	for r in ret_info:
		retailer_db = r['account']
		retailer_name = r['program_name']
	session['retailer_db_name_asc'] = retailer_db
	session['retailer_asc'] = acc_id
	session['retailer_name_asc'] = retailer_name


	return redirect(url_for('order', retailer = session['retailer_asc'], 
									user = session['username_asc']))


@app.route("/order")
@login_required
def order():	

	basicInfo_list = []
	log_File = []
	allNotes = []
	status = []
	allLog = []		
	status_diy_list = []
	status_fni_list = []
	dc_assigned_unique_list = {}
	dc_dict = {}

	search_code_page = ''
	search_term_page = ''	
	orderCreated = ''

	if session['search_results_activated_basicInfo']:
		basicInfo_list = session['records']
		search_code_page = session['search_code_page_number']
		search_term_page = session['search_term_page_number']
	else:
		r_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_basicinfo_details_paginated(int(session['defaultPage']), int(session['rPerPage']))
		for i in basic_info[0]:
			basicInfo_list.append(i)

		session['totalPages'] = int(basic_info[1])
		session['recordsPerPage'] = int(basic_info[2])
		session['orderCount'] = int(basic_info[3])	

		search_code_page = '0'
		search_term_page = 'all'	

	dc_list = ASC_orderMgmt_db.getDCBasicInfo()
	for b in dc_list:		
		dc_dict[b['dc_number']] = b['dc_name']
		


	notes = ASC_orderMgmt_db.get_all_notes()
	allLog = ASC_orderMgmt_db.get_all_log()
	getStatus = ASC_orderMgmt_db.get_all_status()

	status_diy_cursor = ASC_orderMgmt_db.get_diy_status_list()
	status_fni_cursor = ASC_orderMgmt_db.get_fni_status_list()

	for st in status_diy_cursor:
		status_diy_list.append(st)
	

	for st in status_fni_cursor:
		status_fni_list.append(st)
	

	for n in notes:
		allNotes.append(n)
	for s in getStatus:
		status.append(s)
	for l in allLog:
		log_File.append(l)

	# status list
	status_list = config['overAllStatus']['STATUSES'].split(', ')

	def est_date_count(est_date):
		if est_date:
			e_date = est_date
			eDate = datetime.datetime.strptime(e_date, '%Y-%m-%d')
			eDate = eDate.date()

			cDate = generateCurrentDate()
			c_date = datetime.datetime.strptime(cDate, '%Y %b %d %I:%M:%S%p')
			c_date_only = c_date.date()

			days_count = eDate - c_date_only
			r_days = days_count.days
		else:
			r_days = ''
		return r_days

	def elapsed_days_count(b):
		cDate = generateCurrentDate()
		c_date = datetime.datetime.strptime(cDate, '%Y %b %d %I:%M:%S%p')
		c_date_only = c_date.date()

		el_date = b['order_submitted_date']
		el_date = datetime.datetime.strptime(el_date, '%Y %b %d %I:%M:%S%p')
		el_date = el_date.date()

		el_days_count = c_date_only - el_date
		el_days = el_days_count.days
		return el_days
	
	for b in basicInfo_list:
		r_days = est_date_count(b['estimated_date'])
		elapsed_days = elapsed_days_count(b)
		b['r_days'] = r_days
		b['el_days'] = elapsed_days


		


	session['search_results_activated_basicInfo'] = False
	return render_template('order_form.html', 
							basicInfoList = basicInfo_list, 
							status = status, 
							logFile = log_File, 
							total_pages = session['totalPages'], 
							records_Per_Page = session['recordsPerPage'], 
							order_Count = session['orderCount'], 
							notes = allNotes, 
							searchTermPage = search_term_page, 
							searchCodePage = search_code_page, 
							user = session['username_asc'],
							retailer = session['retailer_asc'],
							org_name = session['org_asc'],
							ret_name = session['retailer_name_asc'],
							search_status_list = status_list,
							status_diy = status_diy_list,
							status_fni = status_fni_list,
							dc_assigned_unique_list = dc_dict,
							r_days = r_days )


@app.route("/order/<pageNum>/<pageResults>/<searchCodePage>/<searchTermPage>", methods=['POST'])
@login_required
def index_paginated(pageNum, pageResults, searchCodePage,searchTermPage):

	basicInfo_list = []
	log_File = []
	allNotes = []
	status = []
	search_code_page = ''
	search_term_page = ''
	basic_info = []	
	orderCreated = ''	

	if int(searchCodePage) == int(session['searchAll']) :
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_basicinfo_details_paginated(int(pageNum), int(pageResults))
		session['search_code_page_number'] = '0'
		session['search_term_page_number'] = 'all'
		session['search_results_activated_basicInfo'] = False
	elif int(searchCodePage) == int(session['searchPO']):
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_one_order_basicInfo(searchTermPage, int(pageNum), int(pageResults))
		session['records'] = basic_info
		session['search_code_page_number'] = '1'
		session['search_term_page_number'] = searchTermPage
		session['search_results_activated_basicInfo'] = True
	elif int(searchCodePage) == int(session['searchDC']):
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_one_order_by_dc(searchTermPage, int(pageNum), int(pageResults), retailer_id)
		session['records'] = basic_info
		session['search_code_page_number'] = '2'
		session['search_term_page_number'] = searchTermPage
		session['search_results_activated_basicInfo'] = True
	elif int(searchCodePage) == int(session['searchStatus']):
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_one_order_byStatus(searchTermPage, int(pageNum), int(pageResults))
		session['records'] = basic_info
		session['search_code_page_number'] = '3'
		session['search_term_page_number'] = searchTermPage
		session['search_results_activated_basicInfo'] = True

	elif int(searchCodePage) == int(session['searchDIY']):
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_order_by_diY_order(searchTermPage, int(pageNum), int(pageResults))
		session['records'] = basic_info
		session['search_code_page_number'] = '4'
		session['search_term_page_number'] = searchTermPage
		session['search_results_activated_basicInfo'] = True
	elif int(searchCodePage) == int(session['searchFNI']):
		retailer_id = session['retailer_asc']
		basic_info = ASC_orderMgmt_db.get_order_by_diY_order(searchTermPage, int(pageNum), int(pageResults))
		session['records'] = basic_info
		session['search_code_page_number'] = '5'
		session['search_term_page_number'] = searchTermPage
		session['search_results_activated_basicInfo'] = True

	search_code_page = session['search_code_page_number']
	search_term_page = session['search_term_page_number']	
		
	session['totalPages'] = int(basic_info[1])
	session['recordsPerPage'] = int(basic_info[2])
	session['orderCount'] = int(basic_info[3])
	
	for i in basic_info[0]:
		basicInfo_list.append(i)
		
	getStatus = ASC_orderMgmt_db.get_all_status()
	notes = ASC_orderMgmt_db.get_all_notes()
	allLog = ASC_orderMgmt_db.get_all_log()

	for l in allLog:
		log_File.append(l)
	for n in notes:
		allNotes.append(n)
	for s in getStatus:
		status.append(s)

	status_list = config['overAllStatus']['STATUSES'].split(', ')
	dc_list = sorted(list(dict.fromkeys(basicInfo_list['door_center_name'])))

	session['search_results_activated_basicInfo'] = False
	return render_template('order_form.html', 
							basicInfoList = basicInfo_list,
							status = status,
							logFile = log_File,
							total_pages = session['totalPages'],
							records_Per_Page = session['recordsPerPage'],
							order_Count = session['orderCount'],
							notes = allNotes,							
							searchTermPage = search_term_page,
							searchCodePage = search_code_page,
							user = session['username_asc'],
							org_name = session['org_asc'],
							ret_name = session['retailer_name_asc'],
							search_status_list = status_list)


@app.route('/search_orders/<search_code>', methods=['POST'])
@login_required
def searchRecords(search_code):

	basicInfo_list = []

	if int(search_code) == int(session['searchPO']):
		retailer_id = session['retailer_asc']
		session['po_num'] = request.form['searchByPONumber'].strip()
		basic_info = ASC_orderMgmt_db.get_one_order_basicInfo(session['po_num'], int(session['defaultPage']), int(session['rPerPage']))
		session['search_by_po'] = True
		session['search_code_page_number'] = '1'
		session['search_term_page_number'] = session['po_num']

	if int(search_code) == int(session['searchDC']):
		retailer_id = session['retailer_asc']
		session['dc_id'] = request.form['searchByDC'].strip()
		basic_info = ASC_orderMgmt_db.get_one_order_by_dc(session['dc_id'], int(session['defaultPage']), int(session['rPerPage']))
		session['search_by_dc'] = True
		session['search_code_page_number'] = '2'
		session['search_term_page_number'] = session['dc_id']

	if int(search_code) == int(session['searchStatus']):
		retailer_id = session['retailer_asc']
		session['check_status'] = request.form.get('searchByStatus')
		basic_info = ASC_orderMgmt_db.get_one_order_byStatus(session['check_status'], int(session['defaultPage']), int(session['rPerPage']))
		session['search_by_status'] = True
		session['search_code_page_number'] = '3'
		session['search_term_page_number'] = session['check_status']

	if int(search_code) == int(session['searchDIY']):
		retailer_id = session['retailer_asc']
		session['diy'] = request.form.get('searchByStatusDIY')
		basic_info = ASC_orderMgmt_db.get_order_by_diY_order(session['diy'], int(session['defaultPage']), int(session['rPerPage']))
		session['search_by_status'] = True
		session['search_code_page_number'] = '4'
		session['search_term_page_number'] = session['diy']

	if int(search_code) == int(session['searchFNI']):
		retailer_id = session['retailer_asc']
		session['fni'] = request.form.get('searchByStatusFNI')
		basic_info = ASC_orderMgmt_db.get_order_by_diY_order(session['fni'], int(session['defaultPage']), int(session['rPerPage']))
		session['search_by_status'] = True
		session['search_code_page_number'] = '5'
		session['search_term_page_number'] = session['fni']

	for o in basic_info[0]:
		basicInfo_list.append(o)

	session['records'] = basicInfo_list
	session['totalPages'] = int(basic_info[1])
	session['recordsPerPage'] = int(basic_info[2])
	session['orderCount'] = int(basic_info[3])

	session['search_results_activated_basicInfo'] = True
	return redirect(url_for('order'))


@app.route('/all', methods=['POST'])
@login_required
def viewAll():
	return redirect(url_for('order'))


def sha_encryption(un_encrypted_password):
	encrypted_password = sha256_crypt.encrypt(un_encrypted_password)
	return encrypted_password

def send_to_sms(password,phone):
	sendSms.send_msg(password,phone)
	return 

@app.route('/reset_password', methods=['POST'])
def reset_password():
	checkForMail = []
	incorrect_credentials_flag = False
	email = request.form['email']
	phone = request.form['phone']
	check_for_pw = ASC_orderMgmt_db.check_password(email)

	for c in check_for_pw:
		checkForMail.append(c)
	if checkForMail :
		if checkForMail[0]['user_contact'] == phone:
			newPass = generate_random_id(4, 2)
			newPass_en = sha_encryption(newPass)
			for check in checkForMail:
				check['password']  = newPass_en
			# check['newPass']
			ASC_orderMgmt_db.update_one_password(email, check)
			send_to_sms(newPass, phone)
			flash('Successfully reset the password')
		else:
			incorrect_credentials_flag = True
			flash('incorrect user credentials')
	else:
		incorrect_credentials_flag = True
		flash('incorrect user credentials')
	return redirect(url_for('login'))


# Set doors field with some generated value
def setDoorFields(po_no):
	Door_Spec_Id = generate_random_id(6, 4)

	doorsInfo = {}
	Retailer_PO_No = po_no

	doorsInfo["door_spec_id"]=Door_Spec_Id
	doorsInfo["retailer_po_no"] = Retailer_PO_No

	doorsInfo["door_type"] = ''
	doorsInfo["door_model"]=''
	doorsInfo["door_width"]=''
	doorsInfo["door_height"]=''
	doorsInfo["door_quantity"]=''
	doorsInfo["door_unit_price"]=''
	doorsInfo["door_extended_price"]=''
	
	doorsInfo["color"]=''
	doorsInfo["color_unit_price"]=''
	doorsInfo["color_ext_price"]=''

	doorsInfo["windload"]=''
	doorsInfo["stamp_design"]=''
	doorsInfo["spring_type"]=''

	doorsInfo["additional_struts"]=''
	doorsInfo["additional_struts_quantity"]=''
	doorsInfo["additional_struts_unit_price"]=''
	doorsInfo["additional_struts_extended_price"]=''

	doorsInfo["glass_type"]=''
	doorsInfo["glass_type_quantity"]=''
	doorsInfo["glass_unit_price"]=''
	doorsInfo["glass_ext_price"]=''

	doorsInfo["glass_comments"]=''
	doorsInfo["mosaic_glazing_instructions"]=''

	doorsInfo["decra_trim"]=''
	doorsInfo["decra_trim_quantity"]=''
	doorsInfo["decra_trim_unit_price"]=''
	doorsInfo["decra_trim_extended_price"]=''

	doorsInfo["track_type"]=''
	doorsInfo['track_type_quantity']=''
	doorsInfo['track_type_unit_price'] = ''
	doorsInfo['track_type_extended_price'] = ''

	doorsInfo["horizontal_radius"]=''
	doorsInfo["bracket_mount"]=''

	doorsInfo["blue_ridge_handles"]=''
	doorsInfo["blue_ridge_handles_quantity"]=''
	doorsInfo["blue_ridge_handles_unit_price"]=''
	doorsInfo["blue_ridge_handles_extended_price"]=''

	doorsInfo["blue_ridge_hinges"]=''
	doorsInfo["blue_ridge_hinges_quantity"]=''
	doorsInfo["blue_ridge_hinges_unit_price"]=''
	doorsInfo["blue_ridge_hinges_extended_price"]=''

	doorsInfo["other_decorative_hardware"]=''
	doorsInfo["other_hardware_quantity"]=''
	doorsInfo["other_hardware_unit_price"]=''
	doorsInfo["other_hardware_extended_price"]=''

	doorsInfo["vinyl_t_stop"]=''
	doorsInfo["vinyl_t_stop_quantity"]=''
	doorsInfo["vinyl_t_stop_unit_price"]=''
	doorsInfo["vinyl_t_stop_extended_price"]=''

	doorsInfo["lock_type"]=''
	doorsInfo["lock_type_quantity"]=''
	doorsInfo["lock_type_unit_price"]=''
	doorsInfo["lock_type_extended_price"]=''

	doorsInfo["punched_angle"]=''
	doorsInfo["punched_angle_quantity"]=''
	doorsInfo["punched_angle_unit_price"]=''
	doorsInfo["punched_angle_extended_price"]=''

	doorsInfo["winding_bars"]=''
	doorsInfo["winding_bars_quantity"]=''
	doorsInfo["winding_bars_unit_price"]=''
	doorsInfo["winding_bars_extended_price"]=''

	doorsInfo["other_door_accessories"]=''
	doorsInfo["other_door_accessories_quantity"]=''
	doorsInfo["other_door_accessories_unit_price"]=''
	doorsInfo["other_door_accessories_extended_price"]=''

	doorsInfo["opener_model"]=''
	doorsInfo["opener_model_quantity"]=''
	doorsInfo["opener_model_unit_price"]=''
	doorsInfo["opener_model_extended_price"]=''

	doorsInfo["opener_accessories"]=''
	doorsInfo["opener_accessories_quantity"]=''
	doorsInfo["opener_accessories_unit_price"]=''
	doorsInfo["opener_accessories_extended_price"]=''

	doorsInfo["operator_bracket"]=''
	doorsInfo["operator_bracket_quantity"]=''
	doorsInfo["operator_bracket_unit_price"]=''
	doorsInfo["operator_bracket_extended_price"]=''

	doorsInfo["other_opener_accessories"]=''
	doorsInfo["other_opener_accessories_quantity"]=''
	doorsInfo["other_opener_accessories_unit_price"]=''
	doorsInfo["other_opener_accessories_extended_price"]=''

	# Extra Parts Details
	doorsInfo['additional_part1'] = ''
	doorsInfo['part1_qty'] = ''
	doorsInfo['part1_u_price'] = ''
	doorsInfo['part1_e_price'] = ''

	doorsInfo['additional_part2'] = ''
	doorsInfo['part2_qty'] = ''
	doorsInfo['part2_u_price'] = ''
	doorsInfo['part2_e_price'] = ''

	doorsInfo['additional_part3'] = ''
	doorsInfo['part3_qty'] = ''
	doorsInfo['part3_u_price'] = ''
	doorsInfo['part3_e_price'] = ''

	doorsInfo['additional_part4'] = ''
	doorsInfo['part4_qty'] = ''
	doorsInfo['part4_u_price'] = ''
	doorsInfo['part4_e_price'] = ''

	doorsInfo['additional_part5'] = ''
	doorsInfo['part5_qty'] = ''
	doorsInfo['part5_u_price'] = ''
	doorsInfo['part5_e_price'] = ''

	# Labor_services destails
	doorsInfo['labor_service1'] = ''
	doorsInfo['labor_service1_quantity'] = ''
	doorsInfo['labor_service1_unit_price'] = ''
	doorsInfo['labor_service1_extended_price'] = ''

	doorsInfo['labor_service2'] = ''
	doorsInfo['labor_service2_quantity'] = ''
	doorsInfo['labor_service2_unit_price'] = ''
	doorsInfo['labor_service2_extended_price'] = ''

	doorsInfo['labor_service3'] = ''
	doorsInfo['labor_service3_quantity'] = ''
	doorsInfo['labor_service3_unit_price'] = ''
	doorsInfo['labor_service3_extended_price'] = ''

	doorsInfo['labor_service4'] = ''
	doorsInfo['labor_service4_quantity'] = ''
	doorsInfo['labor_service4_unit_price'] = ''
	doorsInfo['labor_service4_extended_price'] = ''

	doorsInfo['labor_service5'] = ''
	doorsInfo['labor_service5_quantity'] = ''
	doorsInfo['labor_service5_unit_price'] = ''
	doorsInfo['labor_service5_extended_price'] = ''

	doorsInfo['labor_service6'] = ''
	doorsInfo['labor_service6_quantity'] = ''
	doorsInfo['labor_service6_unit_price'] = ''
	doorsInfo['labor_service6_extended_price'] = ''

	doorsInfo['labor_service7'] = ''
	doorsInfo['labor_service7_quantity'] = ''
	doorsInfo['labor_service7_unit_price'] = ''
	doorsInfo['labor_service7_extended_price'] = ''

	doorsInfo['labor_service8'] = ''
	doorsInfo['labor_service8_quantity'] = ''
	doorsInfo['labor_service8_unit_price'] = ''
	doorsInfo['labor_service8_extended_price'] = ''

	doorsInfo['labor_service9'] = ''
	doorsInfo['labor_service9_quantity'] = ''
	doorsInfo['labor_service9_unit_price'] = ''
	doorsInfo['labor_service9_extended_price'] = ''

	doorsInfo['labor_service10'] = ''
	doorsInfo['labor_service10_quantity'] = ''
	doorsInfo['labor_service10_unit_price'] = ''
	doorsInfo['labor_service10_extended_price'] = ''

	doorsInfo['request_drawing'] = ''

	doorsInfo['sub_total_material_cost'] = 0.0
	doorsInfo['sub_total_labor_cost'] = 0.0
	doorsInfo["shipping_cost"]=0.0
	doorsInfo["total"]=0.0
	return doorsInfo


def addLog(po_Num, aName, aType, tag):
	log_info = {}

	user = session['fullname_asc']
	user_org = session['org_asc']

	activity_name = aName
	activity_type = aType
	activity_time = generateCurrentDate()
	tag = tag
	activity_user = user + " at " + user_org

	log_info['retailer_po_no'] = po_Num
	log_info['activity_user'] = activity_user
	log_info['activity_name'] = activity_name
	log_info['activity_type'] = activity_type
	log_info['activity_time'] = activity_time
	log_info['tag'] = tag
	log_info['logger_id'] = session['email_asc']
	log_info['logger_type'] = session['userType_asc']
	ASC_orderMgmt_db.saveNotes(log_info)
	return

def new_status(shortStatus, statusDesc):
	status_msg = 'Status '+ shortStatus +' ('+ statusDesc + ')' 
	return status_msg

def changeLog(po_no): 



	orderBasicRecords = []
	doorRecords = []
	getStatus = []
	changeLog = {}

	po_Num = po_no
	shortStatus = ''
	statusDesc = ''
	statusDate = ''
	new_stat = ''

	orderBasicInfo_list = ASC_orderMgmt_db.get_one_order_by_po(po_Num)
	doorsInfo = ASC_orderMgmt_db.get_one_door_info(po_Num)
	get_status = ASC_orderMgmt_db.getStatus(po_Num)
	
	for i in orderBasicInfo_list:
		orderBasicRecords.append(i)

	for d in doorsInfo:
		doorRecords.append(d)

	for s in get_status:
		getStatus.append(s)

	for gs in getStatus:		
		shortStatus = gs['status'] 
		statusDesc = gs['status_description']
		statusDate = gs['status_modified_date']
	
	new_stat = new_status(shortStatus, statusDesc)

	if session['save_info']:
		aName = "Consumer Info"
		aType = "saved"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['save_info'] = False

	if session['duplicate_item']:
		cId = session['door_s_id']
		aName = "Item with Collection Id : " + cId
		aType = "duplicated"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['door_s_id'] = ''
		session['duplicate_item'] = False

	if session['delete_Door']:
		cId = session['door_s_id']
		aName = "Item with Collection Id : " + cId
		aType = "deleted"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['door_s_id'] = ''
		session['delete_Door'] = False

	if session['add_Item']:
		cId = session['door_s_id']
		aName = "Item with Collection Id : " + cId
		aType = "added"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['door_s_id'] = ''
		session['add_Item'] = False

	if session['update_Item']:
		cId = session['door_s_id']
		aName = "Item with Collection Id : " + cId
		aType = "updated"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['door_s_id'] = ''
		session['update_Item'] = False

	if session['submit_Order']:
		aName = "Order"
		aType = "Submitted"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['submit_Order'] = False

	if session['add_note']:
		aName = "Note"
		aType = "added"
		tag=""
		addLog(po_Num, aName, aType, tag)
		session['add_note'] = False

	if session['process_order']:
		aName = "Order Processing"
		aType = "initiated"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['process_order'] = False

	if session['complete_Order']:
		aName = "Ready to invoice"
		aType = "initiated"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['complete_Order'] = False

	if session['cancel_order']:
		aName = "Order"
		aType = "Cancelled"
		tag="Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['cancel_order'] = False

	if session['manage_status']:
		aName = new_stat
		aType = "added"		
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['manage_status'] = False

	if session['save_dc_info']:
		aName = "DC " + orderBasicRecords[0]['door_center_name']
		aType = "assigned"		
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['save_dc_info'] = False

	if session['save_con_info']:
		aName = "Contractor with id: " + orderBasicRecords[0]['contractor_id']
		aType = "assigned"		
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['save_con_info'] = False

	if session['mail_to_cons']:
		aName = "Notification mail"
		aType = "sent to Consumer"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['mail_to_cons'] = False

	if session['msg_to_cons']:
		aName = "Notification message"
		aType = "sent to Consumer"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['msg_to_cons'] = False

	if session['contractor_ownership']:
		aName = "Ownership"
		aType = "transfered to Contractor"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['contractor_ownership'] = False
		session['materials_ready'] = False

	if session['dcOwnership']:
		aName = "Ownership"
		aType = "transfered to DC"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['dcOwnership'] = False

	if session['shipping_pickup']:
		aName = "Shipping type"
		aType = "selected"
		tag = ""
		addLog(po_Num, aName, aType, tag)
		session['shipping_pickup'] = False

	if session['save_labor_rate']:
		aName = "Labor rate"
		aType = "updated"
		tag = "Status_changed"
		addLog(po_Num, aName, aType, tag)
		session['save_labor_rate'] = False
	return


@app.route('/edit/<po_no>', methods=['POST'])
@login_required
def edit_record(po_no):
	po_num = po_no
	return redirect(url_for('setBasicInformation', po_no = po_num))

def order_status_change(po_no):
	global status_changed
	status_changed = True
	changeLog(po_no)
	ASC_orderMgmt_db.save_status_changes(po_no);
	return

@app.route("/orderSummary/<po_no>")
@login_required
def setBasicInformation(po_no):
	r_id = session['retailer_asc']
	pNum = po_no
	orderBasicRecords = []
	retailerRecords = []
	doorRecords = []
	log_File = []
	note = []
	manage_status = []
	dc_info = []
	dc_info_sorted = []
	con_info = []
	allLog = {}
	con_list_by_dc=[]
	status_list = []


	total_Order = 0
	total_mCost = 0
	total_lCost = 0
	shCost = 0
	short_status = ''
	status_desc = ''
	orderBasicInfo_list = ASC_orderMgmt_db.get_one_order_by_po(pNum)
	retailerInfo = ASC_orderMgmt_db.get_retailer_info(r_id)
	doorsInfo = ASC_orderMgmt_db.get_one_door_info(pNum)
	allLog = ASC_orderMgmt_db.get_log_byPO(pNum)
	notes = ASC_orderMgmt_db.get_notes(pNum)
	status = ASC_orderMgmt_db.getStatus(pNum)
	dcInfo = ASC_orderMgmt_db.getDCBasicInfo()
	contractorInfo = ASC_orderMgmt_db.getContractorInfo()

	for i in orderBasicInfo_list:
		orderBasicRecords.append(i)
	
	for r in retailerInfo:
		retailerRecords.append(r)	

	for d in doorsInfo:
		doorRecords.append(d)

	for l in allLog:
		log_File.append(l)

	for n in notes:
		note.append(n)

	for s in status:
		manage_status.append(s)

	for dc in dcInfo:
		dc_info.append(dc)
	dc_info_sorted = sorted(dc_info, key = lambda i: i['dc_name'])



	if doorRecords:
		if doorRecords[0]['total']:
			for t in doorRecords:
				total_Order = round(float(total_Order),2) + round(float(t['total']),2)

		totalOrder = round(float(total_Order),2)
		if doorRecords[0]['sub_total_material_cost']:
			for tm in doorRecords:
				total_mCost = round(float(total_mCost),2) + round(float(tm['sub_total_material_cost']),2)
		totalMCost = round(float(total_mCost),2)
		if doorRecords[0]['sub_total_labor_cost']:
			for tl in doorRecords:
				total_lCost = round(float(total_lCost),2)+ round(float(tl['sub_total_labor_cost']),2)
		if doorRecords[0]['shipping_cost']:
			for ts in doorRecords:
				shCost = round(float(shCost),2) + round(float(ts['shipping_cost']),2)
	else:
		totalOrder=0.0
		totalMCost=0
		totalLCost=0
		sh_Cost=0	

	ASC_orderMgmt_db.update_totalOrder(pNum, totalOrder)

	order_no = orderBasicRecords[0]['retailer_order_no']
	po_no = orderBasicRecords[0]['retailer_po_no']
	order_Type = orderBasicRecords[0]['order_type']
	order_submitted_date = orderBasicRecords[0]['order_submitted_date']
	order_submitted = orderBasicRecords[0]['order_submitted']
	order_Date = orderBasicRecords[0]['created_date']
	status = orderBasicRecords[0]['status']
	overall_status = orderBasicRecords[0]['overall_status']
	ship_pick = orderBasicRecords[0]['shipping_pickup_info']

	
	r_accnt = retailerRecords[0]['account']
	r_accName = retailerRecords[0]['program_name']
	r_phone = retailerRecords[0]['contact_number_1']
	r_email = retailerRecords[0]['email_1']

	c_fName = orderBasicRecords[0]['consumer_firstname']
	c_sName = orderBasicRecords[0]['consumer_lastname']
	c_email = orderBasicRecords[0]['consumer_email']
	c_sAdd = orderBasicRecords[0]['street_address']
	c_country = orderBasicRecords[0]['country']
	c_state = orderBasicRecords[0]['state']
	c_city = orderBasicRecords[0]['city']
	c_zip = orderBasicRecords[0]['zip']
	c_pPhone = orderBasicRecords[0]['consumer_primary_phone']
	c_sPhone = orderBasicRecords[0]['consumer_secondary_phone']
	c_specInst = orderBasicRecords[0]['special_instructions']
	c_consPreferance = orderBasicRecords[0]['consumer_update_preference']

	dc_id = orderBasicRecords[0]['door_center_id']
	dc_name = orderBasicRecords[0]['door_center_name']

	session['con_id'] = orderBasicRecords[0]['contractor_id']
	
	delivery_modes = config['Delivery_mode']['MODES'].split(', ')

	con_by_dc = ASC_orderMgmt_db.get_contractors_by_dc(dc_id)

	status_cursor = ASC_orderMgmt_db.get_diy_status(order_Type)

	for st in status_cursor:
		status_list.append(st['status_code'])


	for c in con_by_dc:
		con_list_by_dc.append(c)

	if con_list_by_dc:
		for c in contractorInfo:
			if c['account'] == con_list_by_dc[0]['account']:
				con_info.append(c)

		con_name = con_info[0]['contractor_name']
		con_num = con_info[0]['emp_mobile_1']
		con_mail = con_info[0]['email_1']
	else:
		con_info = []
		con_name = ''
		con_num = ''
		con_mail = ''



	for status in manage_status:
		short_status = manage_status[0]['status']
		status_desc = manage_status[0]['status_description']

	def calculate_labor_rate(l, labor_dict):
		rates = 0.0
		labor_rate = 0
		l_rate = 0
		labor_rate = labor_dict[l]
		if labor_rate == '':
			rates = rates+0.0
		elif labor_rate != '':
			labor_rate = float(labor_rate)
			if labor_rate > 0.0:
				rates = rates + labor_rate
			else:
				rates = rates + 0.0
		return rates
		
	total_rate = 0.0
	total_labor_rate = 0.0
	labor_rate_list = []
	labor_dict = {}
	labor_keys = ''
	labor_key_list = []
	labor_rate = ASC_orderMgmt_db.get_all_labor_rates(session['con_id'])
	for lr in labor_rate:
		labor_rate_list.append(lr)

	if labor_rate_list:
		for labors in labor_rate_list:
			labor_dict = labors
		labor_keys = labor_dict.keys()
		for l in labor_dict.keys():
			labor_key_list.append(l)	
		for rate in labor_dict:	
			total_rate = calculate_labor_rate(rate, labor_dict)
		total_labor_rate = total_rate
	
	else:
		total_labor_rate = 0.0

	canada_provinces = config['States_Provinces']['CANADA'].split(', ')
	us_states = config['States_Provinces']['US'].split(', ')
	cons_pref = config['cons_preference']['PREFERENCE_LIST'].split(', ')

	# dc_material_available_date = orderBasicRecords[0]['dc_material_available_date']
	# dc_material_submitted_by = orderBasicRecords[0]['dc_material_submitted_by']
	
	
	return render_template('basicinfoform.html',po_no=po_no,
												orderno=order_no,
												orderType = order_Type,
												oDate = order_Date,
												oSubmittedDate = order_submitted_date,
												oSubmitted = order_submitted,
												status = status,
												o_status = overall_status,
												totalOrder = totalOrder,
												totalMCost = totalMCost,
												totalLCost = total_lCost,
												shippingCost = shCost,
												shipPickup = ship_pick,
												rAccnt = r_accnt,
												rAccName = r_accName,
												rPhone = r_phone,
												rEmail = r_email, 
												cFName = c_fName,
												cSName = c_sName,
												cEmail = c_email,
												cSAdd = c_sAdd,
												cCountry = c_country,
												cState = c_state,
												cCity = c_city,
												cZip = c_zip,
												cPPhone = c_pPhone,
												cSPhone = c_sPhone,
												cSpecInst = c_specInst,
												cConsPreferance = c_consPreferance,
												canadaProvinces = canada_provinces,
												usStates = us_states,
												consPref = cons_pref,
												logFile = log_File,
												dcBasicInfo = dc_info_sorted,
												contractorInfo = con_info,
												conId = session['con_id'],
												conName = con_name,
												conNum = con_num,
												conMail = con_mail,
												totalLaborRate = total_labor_rate,
												dcId = dc_id,
												dcName = dc_name,
												door_record = doorRecords,
												notes = note,												
												user = session['username_asc'],
												shortStatus = short_status,
												statusDesc = status_desc,
												deliveryModes = delivery_modes,
												statusList = status_list
												)


@app.route('/save_dc_info/<po_no>', methods=['POST'])
@login_required
def save_DCInfo(po_no):
	po_num = po_no
	dc_info = []
	dc_info = request.form['DC_list'].split(" - ")
	if dc_info:
		dc_name = dc_info[0].strip()
		dc_id = dc_info[1].strip()
	ASC_orderMgmt_db.update_dc_info(po_num, dc_name, dc_id)
	session['save_dc_info'] = True
	changeLog(po_num)
	return redirect(url_for('setBasicInformation', po_no = po_num))



def get_field(r):
	labor_fields = {}
	r['price'] = [r['contractor_labor_default_value']]
	labor_fields['id_name'] = r['contractor_labor_id_name']
	labor_fields['price'] = r['price']
	return labor_fields

@app.route('/save_contractor_info/<po_no>', methods=['POST'])
@login_required
def save_contractor_info(po_no):
	po_num = po_no
	contractor_info = []
	default_rate = {}
	rates_list = []
	labor_rate_list = []
	new_labor_list = []
	rates_dict = {}
	check_rate_list = []

	contractor_info = request.form['contractor_list'].split(" - ")
	if contractor_info:
		contractor_name = contractor_info[0].strip()
		contractor_id = contractor_info[1].strip()

	ASC_orderMgmt_db.update_contractor_info(po_num, contractor_id)
	
	rates_dict['retailer_po_no'] = po_num
	rates_dict['contractor_id'] = contractor_id
	rates_list = ASC_orderMgmt_db.get_labor_rate_fields()

	for i in rates_list:
		rates_dict[i['contractor_labor_id_name']] = i['contractor_labor_default_value']

	labor_rate_by_id = ASC_orderMgmt_db.get_all_labor_rates(contractor_id)
	for lr in labor_rate_by_id:
		check_rate_list.append(lr)
	if not check_rate_list:
		ASC_orderMgmt_db.save_labor_rate_fields(rates_dict)
	session['save_con_info'] = True
	changeLog(po_num)
	return redirect(url_for('setBasicInformation', po_no = po_num))


def setData():
	#Empty List
	BasicInfos = {}	
	state = ''
	country = ''
	#request data from UI
	#Retailer Information
	Retailer_Account = request.form['retailerAccount']
	Retailer_PO_No = request.form['retailerPONum']
	# Status = request.form['status']

	BasicInfos["retailer_po_no"] = Retailer_PO_No
	BasicInfos["retailer_account"] = Retailer_Account

	# Country-------------------
	country_canada = request.form.get('country_canada')
	country_us = request.form.get('country_us')

	if country_canada:
		country = country_canada
	elif country_us:
		country = country_us
	
	# State -----------------------
	if country == "Canada":
		state = request.form['prvnc_c'].strip()
	elif country == "US":
		state = request.form['state_us'].strip()

	#Consumer Information
	company_name = request.form['companyName'].strip()
	Consumer_Firstname = request.form['conFirstName'].strip()
	Consumer_Lastname = request.form['conLastName'].strip()
	Consumer_Email =  request.form['conEmail'].strip()
	Street_Address = request.form['streetAdd'].strip()
	City = request.form['city'].strip()
	Zip = request.form['zip'].strip()
	Consumer_Primary_Phone = request.form['conPrimaryPhone'].strip()
	Consumer_Secondary_Phone = request.form['conSecondaryPhone'].strip()
	special_instructions = request.form['spcl_instructuins'].strip()
	consumer_preferance = request.form.get('consumer_preferance')
	#set data to the empty list
	BasicInfos["company_name"] = company_name
	BasicInfos["consumer_firstname"] = Consumer_Firstname.capitalize()
	BasicInfos["consumer_lastname"] = Consumer_Lastname.capitalize()
	BasicInfos["consumer_email"] = Consumer_Email
	BasicInfos["street_address"] = Street_Address
	BasicInfos["country"] = country
	BasicInfos["state"] = state
	BasicInfos["city"] = City
	BasicInfos["zip"] = Zip
	BasicInfos["consumer_primary_phone"] = Consumer_Primary_Phone
	BasicInfos["consumer_secondary_phone"] = Consumer_Secondary_Phone
	BasicInfos["special_instructions"] = special_instructions
	BasicInfos["consumer_update_preference"] = consumer_preferance


	return BasicInfos

# Save button - Basic information form
@app.route("/formdoor", methods=['POST'])
@login_required
def save_basic_info():
	basic_infos = setData()
	po_no = basic_infos['retailer_po_no']

	ASC_orderMgmt_db.update_one_record(po_no, basic_infos)
	session['save_info'] = True
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))


@app.route("/edit_Door/<doorSpec_id>/<po_no>", methods=['POST'])
@login_required
def edit_door(doorSpec_id, po_no):
	door_spec_id = doorSpec_id
	doorsInfo = []
	steel_traditional = []
	basic_infos = []
	labor_rates = []
	state_name_sname = []
	labor_rate_info = []
	labor_rate_keys = []
	labor_id_descriptors = {}
	po_num = po_no

	doors_Info = ASC_orderMgmt_db.get_one_door_info_for_duplicate(door_spec_id)
	cons_location = ASC_orderMgmt_db.get_one_order_by_po(po_num)
	labor_rate_details = ASC_orderMgmt_db.get_labor_rate_details()

	for door in doors_Info:
		doorsInfo.append(door)

	for loc in cons_location:
		basic_infos.append(loc)

	for lrd in labor_rate_details:
		labor_rate_info.append(lrd)

	# Residential Models
	steel_traditional = config['Residential_models']['STEEL_TRADITIONAL'].split(', ')
	steel_carriage_house = config['Residential_models']['STEEL CARRIAGE HOUSE'].split(', ')
	speciality = config['Residential_models']['SPECIALITY'].split(', ')

	# Commercial Models
	polyurethane_insu = config['Commercial_models']['POLYURETHANE_INSULATED'].split(', ')
	polystyrene_insulated = config['Commercial_models']['POLYSTYRENE_INSULATED'].split(', ')
	ribbed_panel = config['Commercial_models']['RIBBED_PANEL'].split(', ')
	aluminum_fullview = config['Commercial_models']['ALUMINUM_FULLVIEW'].split(', ')
	rolling_sheet_commercial = config['Commercial_models']['ROLLING_SHEET_COMMERCIAL'].split(', ')
	rolling_sheet_self_storage = config['Commercial_models']['ROLLING_SHEET_SELF_STORAGE'].split(', ')
	com_models = [polyurethane_insu, polystyrene_insulated, ribbed_panel, aluminum_fullview, rolling_sheet_commercial, rolling_sheet_self_storage]
	

	# Spring Type 
	spring_type = config['Spring_Type']['TYPES'].split(', ')

	lift_type = config['Track_Application_Lift_Type']['LIFT_TYPE'].split(', ')

	state_name_sname = basic_infos[0]['state']

	labor_rates_cursor = ASC_orderMgmt_db.get_labor_rates(state_name_sname)

	for rates in labor_rates_cursor:
		labor_rates.append(rates)

	for desc in labor_rate_info:
		labor_id_descriptors[desc['retail_labor_id_name']] = desc['retail_labor_service']

	return render_template('updateDoor.html',speciality_models = speciality,
											steelCarriageHouse = steel_carriage_house,
											steelTraditional = steel_traditional, 
											com_models = com_models,
											po_no = po_num, 
											door_SpecId = door_spec_id, 
											doors_info = doorsInfo, 
											user = session['username_asc'],
											springType = spring_type, 
											laborRates = labor_rates,
											laborIdDescriptors = labor_id_descriptors)

def setDoorDetails():	
	labor_rate_details = ASC_orderMgmt_db.get_labor_rate_details()
	doorsRecords={}

	labor_rate_info = []
	labor_id_descriptors = {}
	doorType = ''
	DoorModel = ''

	for lrd in labor_rate_details:
		labor_rate_info.append(lrd)

	for desc in labor_rate_info:
		labor_id_descriptors[desc['retail_labor_id_name']] = desc['retail_labor_service']

	#Order Information
	Retailer_PO_No = request.form['retailerPonum']
	doorsRecords ["retailer_po_no"] = Retailer_PO_No
	#DoorSpec Id
	Door_Spec_Id = request.form['doorSpecId']
	doorsRecords ["door_spec_id"] = Door_Spec_Id


	# Door Type selection
	doorType = 'checkbox'
	doorType1, doorType2 = False, False
	if request.form.get('resModelCheck'):
		# doorType1 = True
		doorType = "Residential Models"
	elif request.form.get('comModelCheck'):
		# doorType2 = True
		doorType = "Commercial Models"	
	
	doorsRecords ["door_type"]=doorType
	DoorModel = ''

	if doorType == "Residential Models":
		DoorModel = request.form['resDoorModel']
	elif doorType == "Commercial Models":
		DoorModel = request.form['comDoorModel']

	Door_Model = DoorModel
	doorsRecords ["door_model"] = Door_Model

	# Door Size
	Door_size_Width = request.form['dsWidth']
	Door_size_Height = request.form['dsHeight']
	Door_size_Quantity = request.form['dsQuantity']
	Door_size_Unit_price = request.form['dsUPrice']
	Door_size_Extended_price = request.form['dsExtPrice']	

	doorsRecords ["door_width"]=Door_size_Width
	doorsRecords ["door_height"]=Door_size_Height
	doorsRecords ["door_quantity"]=Door_size_Quantity
	doorsRecords ["door_unit_price"]=Door_size_Unit_price
	doorsRecords ["door_extended_price"]=Door_size_Extended_price

	# Color
	Color = request.form['color']
	Color_unit_price = request.form['clrUPrice']
	Color_ext_price = request.form['clrExtPrice']
	doorsRecords ["color"]=Color
	doorsRecords ["color_unit_price"]=Color_unit_price
	doorsRecords ["color_ext_price"]=Color_ext_price

	# Winload
	Windload = request.form['windload']
	doorsRecords ["windload"]=Windload

	# Stamp Design
	Stamp_Design = request.form['stampDsgn']
	doorsRecords ["stamp_design"]=Stamp_Design	

	# Spring Type
	Spring_Type = request.form['springType']
	doorsRecords ["spring_type"]=Spring_Type

	# Additional Struts
	Additional_Struts = request.form['addStruts']
	Additional_Struts_Quantity = request.form['addStrutsQty']
	Additional_Struts_Unit_price = request.form['addStrutsUPrice']
	Additional_Struts_Extended_price = request.form['addStrutsExtPrice']
	#set data to the empty list
	doorsRecords ["additional_struts"]=Additional_Struts
	doorsRecords ["additional_struts_quantity"]=Additional_Struts_Quantity
	doorsRecords ["additional_struts_unit_price"]=Additional_Struts_Unit_price
	doorsRecords ["additional_struts_extended_price"]=Additional_Struts_Extended_price

	# Glass Type
	Glass_type = request.form['glassType']
	Glass_type_Quantity = request.form['gtQuantity']
	Glass_unit_price = request.form['glassUPrice']
	Glass_ext_price = request.form['glassExtPrice']
	#set data to the empty list
	doorsRecords ["glass_type"]=Glass_type
	doorsRecords["glass_type_quantity"]=Glass_type_Quantity
	doorsRecords ["glass_unit_price"]=Glass_unit_price
	doorsRecords ["glass_ext_price"]=Glass_ext_price

	Glass_Comments= request.form['glassComments']
	doorsRecords ["glass_comments"]=Glass_Comments
	Mosaic_Glazing_Instructions = request.form['mosglzins']
	doorsRecords ["mosaic_glazing_instructions"]=Mosaic_Glazing_Instructions
	
	# Decra Trim
	Decra_Trim = request.form['decaTrim']
	Decra_Trim_Quantity = request.form['dtQuantity']
	Decra_Trim_Unit_price = request.form['decaTrimUPrice']
	Decra_Trim_Extended_price = request.form['decaTrimExtPrice']
	#set data to the empty list
	doorsRecords ["decra_trim"]=Decra_Trim
	doorsRecords["decra_trim_quantity"]=Decra_Trim_Quantity
	doorsRecords ["decra_trim_unit_price"]=Decra_Trim_Unit_price
	doorsRecords ["decra_trim_extended_price"]=Decra_Trim_Extended_price

	# Track type
	Track_type = request.form['trackType']
	Track_type_Quantity = request.form['trackTypeQty']
	Track_type_Unit_price = request.form['trackTypeUPrice']
	Track_type_Extended_price = request.form['trackTypeExtPrice']
	#set data to the empty list
	doorsRecords ["track_type"]=Track_type
	doorsRecords ["track_type_quantity"]=Track_type_Quantity
	doorsRecords ["track_type_unit_price"]=Track_type_Unit_price
	doorsRecords ["track_type_extended_price"]=Track_type_Extended_price

	# HR, Mount
	Horizontal_radius = request.form['hrRadius']
	Bracket_Mount = request.form['bracketMount']
	#set data to the empty list
	doorsRecords ["horizontal_radius"]=Horizontal_radius
	doorsRecords ["bracket_mount"]=Bracket_Mount

	Deco_Handles = request.form['decoHandles']
	Handles_Quantity = request.form['decoHndlQuantity']
	Handles_Unit_price = request.form['decoHndlUPrice']
	Handles_Extended_price = request.form['decoHndlExtPrice']
	#set data to the empty list
	doorsRecords ["blue_ridge_handles"]=Deco_Handles
	doorsRecords ["blue_ridge_handles_quantity"]=Handles_Quantity
	doorsRecords ["blue_ridge_handles_unit_price"]=Handles_Unit_price
	doorsRecords ["blue_ridge_handles_extended_price"]=Handles_Extended_price

	Deco_Hinges = request.form['decoHinges']
	Hinges_Quantity = request.form['decoHngsQuantity']
	Hinges_Unit_price = request.form['decoHngsUPrice']
	Hinges_Extended_price = request.form['decoHngsExtPrice']
	#set data to the empty list
	doorsRecords ["blue_ridge_hinges"]=Deco_Hinges
	doorsRecords ["blue_ridge_hinges_quantity"]=Hinges_Quantity
	doorsRecords ["blue_ridge_hinges_unit_price"]=Hinges_Unit_price
	doorsRecords ["blue_ridge_hinges_extended_price"]=Hinges_Extended_price

	Other_deco_hardware = request.form['otherHardware']
	Other_Hardware_Quantity = request.form['othHQuantity']
	Other_Hardware_Unit_price = request.form['othHUPrice']
	Other_Hardware_Extended_price = request.form['othHExtPrice']
	#set data to the empty list
	doorsRecords ["other_decorative_hardware"]=Other_deco_hardware
	doorsRecords ["other_hardware_quantity"]=Other_Hardware_Quantity
	doorsRecords ["other_hardware_unit_price"]=Other_Hardware_Unit_price
	doorsRecords ["other_hardware_extended_price"]=Other_Hardware_Extended_price


	#Other Door Options
	Vinyl_T_Stop = request.form['vinTStop']
	Vinyl_T_Stop_Quantity = request.form['vinTStopQty']
	Vinyl_T_Stop_Unit_price = request.form['vinTStopUPrice']
	Vinyl_T_Stop_Extended_price = request.form['vinTStopExtPrice']
	#set data to the empty list
	doorsRecords ["vinyl_t_stop"]=Vinyl_T_Stop
	doorsRecords ["vinyl_t_stop_quantity"]=Vinyl_T_Stop_Quantity
	doorsRecords ["vinyl_t_stop_unit_price"]=Vinyl_T_Stop_Unit_price
	doorsRecords ["vinyl_t_stop_extended_price"]=Vinyl_T_Stop_Extended_price	
	
	
	Lock_type = request.form['lockType']
	Lock_type_Quantity = request.form['lockTypeQty']
	Lock_type_Unit_price = request.form['lockTypeUPrice']
	Lock_type_Extended_price = request.form['lockTypeExtPrice']
	#set data to the empty list
	doorsRecords ["lock_type"]=Lock_type
	doorsRecords ["lock_type_quantity"]=Lock_type_Quantity
	doorsRecords ["lock_type_unit_price"]=Lock_type_Unit_price
	doorsRecords ["lock_type_extended_price"]=Lock_type_Extended_price

	Punched_angle = request.form['punchedAngle']
	Punched_angle_Quantity = request.form['punchedAngleQty']
	Punched_angle_Unit_price = request.form['punchedAngleUPrice']
	Punched_angle_Extended_price = request.form['punchedAngleExtPrice']
	#set data to the empty list
	doorsRecords ["punched_angle"]=Punched_angle
	doorsRecords ["punched_angle_quantity"]=Punched_angle_Quantity
	doorsRecords ["punched_angle_unit_price"]=Punched_angle_Unit_price
	doorsRecords ["punched_angle_extended_price"]=Punched_angle_Extended_price	

	Winding_Bars = request.form['windingBars']
	Winding_Bars_Quantity = request.form['winbarsQty']
	Winding_Bars_Unit_price = request.form['winbarsuprice']
	Winding_Bars_Extended_price = request.form['winbarsextprice']
	#set data to the empty list
	doorsRecords ["winding_bars"]=Winding_Bars
	doorsRecords ["winding_bars_quantity"]=Winding_Bars_Quantity
	doorsRecords ["winding_bars_unit_price"]=Winding_Bars_Unit_price
	doorsRecords ["winding_bars_extended_price"]=Winding_Bars_Extended_price

	Other_door_accsrs = request.form['othDoorAccs']
	Other_door_accsrs_Quantity = request.form['othdooraccssquan']
	Other_door_accsrs_Unit_price = request.form['othdooraccsuprice']
	Other_door_accsrs_Extended_price = request.form['othdooraccsextprice']
	#set data to the empty list
	doorsRecords ["other_door_accessories"]=Other_door_accsrs
	doorsRecords ["other_door_accessories_quantity"]=Other_door_accsrs_Quantity
	doorsRecords ["other_door_accessories_unit_price"]=Other_door_accsrs_Unit_price
	doorsRecords ["other_door_accessories_extended_price"]=Other_door_accsrs_Extended_price

	Opener_model = request.form['openermod']
	Opener_model_Quantity = request.form['openermodquan']
	Opener_model_Unit_price = request.form['openermoduprice']
	Opener_model_Extended_price = request.form['openermodextprice']
	#set data to the Empty list
	doorsRecords ["opener_model"]=Opener_model
	doorsRecords ["opener_model_quantity"]=Opener_model_Quantity
	doorsRecords ["opener_model_unit_price"]=Opener_model_Unit_price
	doorsRecords ["opener_model_extended_price"]=Opener_model_Extended_price

	Opener_accsr = request.form['openeracc']
	Opener_accsr_Quantity = request.form['openeraccquan']
	Opener_accsr_Unit_price = request.form['openeraccuprice']
	Opener_accsr_Extended_price = request.form['openeraccextprice']
	#set data to the Empty list
	doorsRecords ["opener_accessories"]=Opener_accsr
	doorsRecords ["opener_accessories_quantity"]=Opener_accsr_Quantity
	doorsRecords ["opener_accessories_unit_price"]=Opener_accsr_Unit_price
	doorsRecords ["opener_accessories_extended_price"]=Opener_accsr_Extended_price

	Operator_bracket = request.form['opbracket']
	Operator_bracket_Quantity = request.form['opbracketquan']
	Operator_bracket_Unit_price = request.form['opbracketuprice']
	Operator_bracket_Extended_price = request.form['opbracketextprice']
	#set data to the Empty list
	doorsRecords ["operator_bracket"]=Operator_bracket
	doorsRecords ["operator_bracket_quantity"]=Operator_bracket_Quantity
	doorsRecords ["operator_bracket_unit_price"]=Operator_bracket_Unit_price
	doorsRecords ["operator_bracket_extended_price"]=Operator_bracket_Extended_price

	Other_opener_accsr = request.form['otheroepnaccsr']	
	Other_opener_accsr_Quantity = request.form['otheroepnaccsrquan']
	Other_opener_accsr_Unit_price = request.form['otheroepnaccsruprice']
	Other_opener_accsr_Extended_price = request.form['otheroepnaccsrextprice']
	#set data to the Empty list
	doorsRecords ["other_opener_accessories"]=Other_opener_accsr
	doorsRecords ["other_opener_accessories_quantity"]=Other_opener_accsr_Quantity
	doorsRecords ["other_opener_accessories_unit_price"]=Other_opener_accsr_Unit_price
	doorsRecords ["other_opener_accessories_extended_price"]=Other_opener_accsr_Extended_price

	# Extra Parts Details
	additionalPart1 = request.form['additionalPart1']
	part1_Qty = request.form['partQty1']
	part1_UPrice = request.form['partUPrice1']
	part1_EPrice = request.form['partEPrice1']

	doorsRecords ["additional_part1"]=additionalPart1
	doorsRecords ["part1_qty"]=part1_Qty
	doorsRecords ["part1_u_price"]=part1_UPrice
	doorsRecords ["part1_e_price"]=part1_EPrice

	additionalPart2 = request.form['additionalPart2']
	part2_Qty = request.form['partQty2']
	part2_UPrice = request.form['partUPrice2']
	part2_EPrice = request.form['partEPrice2']

	doorsRecords ["additional_part2"]=additionalPart2
	doorsRecords ["part2_qty"]=part2_Qty
	doorsRecords ["part2_u_price"]=part2_UPrice
	doorsRecords ["part2_e_price"]=part2_EPrice

	additionalPart3 = request.form['additionalPart3']
	part3_Qty = request.form['partQty3']
	part3_UPrice = request.form['partUPrice3']
	part3_EPrice = request.form['partEPrice3']

	doorsRecords ["additional_part3"]=additionalPart3
	doorsRecords ["part3_qty"]=part3_Qty
	doorsRecords ["part3_u_price"]=part3_UPrice
	doorsRecords ["part3_e_price"]=part3_EPrice

	additionalPart4 = request.form['additionalPart4']
	part4_Qty = request.form['partQty4']
	part4_UPrice = request.form['partUPrice4']
	part4_EPrice = request.form['partEPrice4']

	doorsRecords ["additional_part4"]=additionalPart4
	doorsRecords ["part4_qty"]=part4_Qty
	doorsRecords ["part4_u_price"]=part4_UPrice
	doorsRecords ["part4_e_price"]=part4_EPrice

	additionalPart5 = request.form['additionalPart5']
	part5_Qty = request.form['partQty5']
	part5_UPrice = request.form['partUPrice5']
	part5_EPrice = request.form['partEPrice5']

	doorsRecords ["additional_part5"]=additionalPart5
	doorsRecords ["part5_qty"]=part5_Qty
	doorsRecords ["part5_u_price"]=part5_UPrice
	doorsRecords ["part5_e_price"]=part5_EPrice

	labor_service1_id = request.form['labor1'].strip().split("-")[0]
	# Fetch the descriptor
	if labor_service1_id:		
		labor_service1 = labor_id_descriptors[labor_service1_id]
	else:
		labor_service1 = ''
	labor_service1_Quantity = request.form['laborQty'].strip()
	labor_service1_UnitPrice = request.form['laborUPrice'].strip()
	labor_service1_ExtendedPrice = request.form['laborEPrice'].strip()

	doorsRecords ["labor_service1"]=labor_service1
	doorsRecords ["labor_service1_quantity"]=labor_service1_Quantity
	doorsRecords ["labor_service1_unit_price"]=labor_service1_UnitPrice
	doorsRecords ["labor_service1_extended_price"]=labor_service1_ExtendedPrice

	labor_service2_id = request.form['labor2'].strip().split("-")[0]
	if labor_service2_id:
		labor_service2 = labor_id_descriptors[labor_service2_id]
	else:
		labor_service2 = ''
	labor_service2_Quantity = request.form['laborQty2'].strip()
	labor_service2_UnitPrice = request.form['laborUPrice2'].strip()
	labor_service2_ExtendedPrice = request.form['laborEPrice2'].strip()

	doorsRecords ["labor_service2"]=labor_service2
	doorsRecords ["labor_service2_quantity"]=labor_service2_Quantity
	doorsRecords ["labor_service2_unit_price"]=labor_service2_UnitPrice
	doorsRecords ["labor_service2_extended_price"]=labor_service2_ExtendedPrice

	labor_service3_id = request.form['labor3'].strip().split("-")[0]
	if labor_service3_id:
		labor_service3 = labor_id_descriptors[labor_service3_id]
	else:
		labor_service3 = ''
	labor_service3_Quantity = request.form['laborQty3'].strip()
	labor_service3_UnitPrice = request.form['laborUPrice3'].strip()
	labor_service3_ExtendedPrice = request.form['laborEPrice3'].strip()

	doorsRecords ["labor_service3"]=labor_service3
	doorsRecords ["labor_service3_quantity"]=labor_service3_Quantity
	doorsRecords ["labor_service3_unit_price"]=labor_service3_UnitPrice
	doorsRecords ["labor_service3_extended_price"]=labor_service3_ExtendedPrice

	labor_service4_id = request.form['labor4'].strip().split("-")[0]
	if labor_service4_id:
		labor_service4 = labor_id_descriptors[labor_service4_id]
	else:
		labor_service4 = ''
	labor_service4_Quantity = request.form['laborQty4'].strip()
	labor_service4_UnitPrice = request.form['laborUPrice4'].strip()
	labor_service4_ExtendedPrice = request.form['laborEPrice4'].strip()

	doorsRecords ["labor_service4"]=labor_service4
	doorsRecords ["labor_service4_quantity"]=labor_service4_Quantity
	doorsRecords ["labor_service4_unit_price"]=labor_service4_UnitPrice
	doorsRecords ["labor_service4_extended_price"]=labor_service4_ExtendedPrice

	labor_service5_id = request.form['labor5'].strip().split("-")[0]
	if labor_service5_id:
		labor_service5 = labor_id_descriptors[labor_service5_id]
	else:
		labor_service5 = ''
	labor_service5_Quantity = request.form['laborQty5'].strip()
	labor_service5_UnitPrice = request.form['laborUPrice5'].strip()
	labor_service5_ExtendedPrice = request.form['laborEPrice5'].strip()

	doorsRecords ["labor_service5"]=labor_service5
	doorsRecords ["labor_service5_quantity"]=labor_service5_Quantity
	doorsRecords ["labor_service5_unit_price"]=labor_service5_UnitPrice
	doorsRecords ["labor_service5_extended_price"]=labor_service5_ExtendedPrice

	labor_service6_id = request.form['labor6'].strip().split("-")[0]
	if labor_service6_id:
		labor_service6 = labor_id_descriptors[labor_service6_id]
	else:
		labor_service6 = ''
	labor_service6_Quantity = request.form['laborQty6'].strip()
	labor_service6_UnitPrice = request.form['laborUPrice6'].strip()
	labor_service6_ExtendedPrice = request.form['laborEPrice6'].strip()

	doorsRecords ["labor_service6"]=labor_service6
	doorsRecords ["labor_service6_quantity"]=labor_service6_Quantity
	doorsRecords ["labor_service6_unit_price"]=labor_service6_UnitPrice
	doorsRecords ["labor_service6_extended_price"]=labor_service6_ExtendedPrice

	labor_service7_id = request.form['labor7'].strip().split("-")[0]
	if labor_service7_id:
		labor_service7 = labor_id_descriptors[labor_service7_id]
	else:
		labor_service7 = ''
	labor_service7_Quantity = request.form['laborQty7'].strip()
	labor_service7_UnitPrice = request.form['laborUPrice7'].strip()
	labor_service7_ExtendedPrice = request.form['laborEPrice7'].strip()

	doorsRecords ["labor_service7"]=labor_service7
	doorsRecords ["labor_service7_quantity"]=labor_service7_Quantity
	doorsRecords ["labor_service7_unit_price"]=labor_service7_UnitPrice
	doorsRecords ["labor_service7_extended_price"]=labor_service7_ExtendedPrice

	labor_service8 = request.form['labor8'].strip()
	labor_service8_Quantity = request.form['laborQty8'].strip()
	labor_service8_UnitPrice = request.form['laborUPrice8'].strip()
	labor_service8_ExtendedPrice = request.form['laborEPrice8'].strip()

	doorsRecords ["labor_service8"]=labor_service8
	doorsRecords ["labor_service8_quantity"]=labor_service8_Quantity
	doorsRecords ["labor_service8_unit_price"]=labor_service8_UnitPrice
	doorsRecords ["labor_service8_extended_price"]=labor_service8_ExtendedPrice

	labor_service9 = request.form['labor9'].strip()
	labor_service9_Quantity = request.form['laborQty9'].strip()
	labor_service9_UnitPrice = request.form['laborUPrice9'].strip()
	labor_service9_ExtendedPrice = request.form['laborEPrice9'].strip()

	doorsRecords ["labor_service9"]=labor_service9
	doorsRecords ["labor_service9_quantity"]=labor_service9_Quantity
	doorsRecords ["labor_service9_unit_price"]=labor_service9_UnitPrice
	doorsRecords ["labor_service9_extended_price"]=labor_service9_ExtendedPrice

	labor_service10 = request.form['labor10'].strip()
	labor_service10_Quantity = request.form['laborQty10'].strip()
	labor_service10_UnitPrice = request.form['laborUPrice10'].strip()
	labor_service10_ExtendedPrice = request.form['laborEPrice10'].strip()

	doorsRecords ["labor_service10"]=labor_service10
	doorsRecords ["labor_service10_quantity"]=labor_service10_Quantity
	doorsRecords ["labor_service10_unit_price"]=labor_service10_UnitPrice
	doorsRecords ["labor_service10_extended_price"]=labor_service10_ExtendedPrice

	request_drawing = request.form['requestDrawing']
	doorsRecords["request_drawing"] = request_drawing

	Sub_Total_Material_Cost = request.form['st_MatCost']
	Sub_Total_labor_Cost = request.form['st_LabrCost']
	Shipping_cost = request.form['shipCost']
	Total = request.form['total']

	doorsRecords ["sub_total_material_cost"]=Sub_Total_Material_Cost
	doorsRecords ["sub_total_labor_cost"]=Sub_Total_labor_Cost
	doorsRecords ["shipping_cost"]=Shipping_cost
	doorsRecords ["total"]=Total

	return doorsRecords


def set_laborRate_fields(po_num, door_spec_id):
	labor_rate_fields = {}

	labor_rate_fields['door_spec_id'] = door_spec_id
	labor_rate_fields['retailer_po_no'] = po_num

	labor_rate_fields['labortype1_name'] = ''
	labor_rate_fields['labortype1_rate_type'] = ''
	labor_rate_fields['labortype1_unit_price'] = ''
	labor_rate_fields['labortype1_ext_price'] = ''

	labor_rate_fields['labortype2_name'] = ''
	labor_rate_fields['labortype2_rate_type'] = ''
	labor_rate_fields['labortype2_unit_price'] = ''
	labor_rate_fields['labortype2_ext_price'] = ''

	labor_rate_fields['labortype3_name'] = ''
	labor_rate_fields['labortype3_rate_type'] = ''
	labor_rate_fields['labortype3_unit_price'] = ''
	labor_rate_fields['labortype3_ext_price'] = ''

	labor_rate_fields['labortype4_name'] = ''
	labor_rate_fields['labortype4_rate_type'] = ''
	labor_rate_fields['labortype4_unit_price'] = ''
	labor_rate_fields['labortype4_ext_price'] = ''

	labor_rate_fields['labortype5_name'] = ''
	labor_rate_fields['labortype5_rate_type'] = ''
	labor_rate_fields['labortype5_unit_price'] = ''
	labor_rate_fields['labortype5_ext_price'] = ''

	labor_rate_fields['labortype6_name'] = ''
	labor_rate_fields['labortype6_rate_type'] = ''
	labor_rate_fields['labortype6_unit_price'] = ''
	labor_rate_fields['labortype6_ext_price'] = ''

	labor_rate_fields['labortype7_name'] = ''
	labor_rate_fields['labortype7_rate_type'] = ''
	labor_rate_fields['labortype7_unit_price'] = ''
	labor_rate_fields['labortype7_ext_price'] = ''

	labor_rate_fields['labortype8_name'] = ''
	labor_rate_fields['labortype8_rate_type'] = ''
	labor_rate_fields['labortype8_unit_price'] = ''
	labor_rate_fields['labortype8_ext_price'] = ''

	labor_rate_fields['labortype9_name'] = ''
	labor_rate_fields['labortype9_rate_type'] = ''
	labor_rate_fields['labortype9_unit_price'] = ''
	labor_rate_fields['labortype9_ext_price'] = ''

	labor_rate_fields['labortype10_name'] = ''
	labor_rate_fields['labortype10_rate_type'] = ''
	labor_rate_fields['labortype10_unit_price'] = ''
	labor_rate_fields['labortype10_ext_price'] = ''

	labor_rate_fields['collection_total'] = 0.00	

	return labor_rate_fields



@app.route("/add_Doors", methods=['POST'])
@login_required
def update_adddoors_records():
	doorsonlineRecords = setDoorDetails()
	po_no = doorsonlineRecords['retailer_po_no']
	
	door_specID = doorsonlineRecords['door_spec_id']
	ASC_orderMgmt_db.update_one_door_record(door_specID, doorsonlineRecords)	

	req_drawing = doorsonlineRecords['request_drawing']
	if req_drawing =='Yes':
		sendData['po_no'] = po_no
		sendData['time'] = generateCurrentDate()
		sendData['content'] = 'Nexus Order# '+ po_no +' has requested a Shop Drawing'
		sendData['subject'] = config['Sendgrid']['REQ_DRAWING']
		sendData['mail'] = get_retailer_mail()
		send.send_to_amarr(sendData)

	session['door_s_id'] = door_specID
	session['update_Item'] = True
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))


@app.route("/duplicate/<doorSpec_id>/<po_no>", methods=['POST'])
@login_required
def duplicate_door(doorSpec_id, po_no):
	door_infos_list = []
	po_num = po_no
	door_spec_id = doorSpec_id

	doors_record_cursor = ASC_orderMgmt_db.get_one_door_info_for_duplicate(door_spec_id)
	for i in doors_record_cursor:
		door_infos_list.append(i)

	new_collection_id = generate_random_id(6, 4)
	door_infos_list[0]['door_spec_id'] = new_collection_id
	door_infos_list[0]['_id'] = ObjectId()
	ASC_orderMgmt_db.save_duplicate_doors_details(door_infos_list)

	session['duplicate_item'] = True
	changeLog(po_num)

	return redirect(url_for('setBasicInformation', po_no = po_no))


@app.route("/deleteDoor/<ds_id>/<po_no>", methods=['POST'])
@login_required
def delete_door_by_dsId(ds_id, po_no):
	session['delete_Door'] = True
	changeLog(po_no)
	ASC_orderMgmt_db.delete_a_door(ds_id)
	return redirect(url_for('setBasicInformation', po_no = po_no))


@app.route("/addDoor/<po_no>", methods=['POST'])
@login_required
def add_a_new_door(po_no):
	# doors_info = {}
	doors_info =setDoorFields(po_no)
	door_spec_id = doors_info['door_spec_id']
	con_order_ap = set_laborRate_fields(po_no, door_spec_id)
	ASC_orderMgmt_db.save_doors_details(doors_info)
	ASC_orderMgmt_db.create_con_order_ap(con_order_ap)
	session['add_Item'] = True
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))

@app.route("/submitOrder/<po_no>", methods=['POST'])
@login_required
def submit_an_order(po_no):
	basicInfos = {}	
	date_time = generateCurrentDate()
	basicInfos['order_submitted'] = "Yes"
	basicInfos['order_submitted_date'] = date_time
	basicInfos['status'] = 'Order Submitted'
	ASC_orderMgmt_db.update_orderPlaced_data(po_no, basicInfos)
	session['submit_Order'] = True
	changeLog(po_no)
	return redirect(url_for('order'))



@app.route('/send/<po_no>', methods=['POST'])
@login_required
def send_note(po_no):
	session['add_note'] = True
	noteDetails = {}
	mailer_name = []
	
	sendingDate = generateCurrentDate()
	msg = request.form['note']

	noteDetails['retailer_po_no'] = po_no
	noteDetails['sender'] = session['username_asc']
	noteDetails['sender_id'] = session['email_asc']
	noteDetails['sending_time'] = sendingDate
	noteDetails['message'] = msg
	noteDetails['sender_org'] = session['org_asc']

	ASC_orderMgmt_db.save_Notes(noteDetails)
	noteDetails['mail'] = get_retailer_mail()	
	mailer_name = noteDetails['mail'].split('@')
	noteDetails['mailer_name'] = mailer_name[0]
	send.send_to_mail(noteDetails)	
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))

@app.route('/orderProcessing/<po_no>', methods=['POST'])
@login_required
def order_processing(po_no):
	session['process_order'] = True
	basicInfos = {}	
	sendData = {}
	num = ''
	mail = ''
	contact_info = ASC_orderMgmt_db.get_number(po_no)
	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']
	basicInfos['status'] = 'Order Processing initiated'	
	basicInfos['asc_order_processing_date'] = generateCurrentDate()
	basicInfos['asc_order_processing_by'] = session['fullname_asc']
	ASC_orderMgmt_db.update_orderSubmitted_data(po_no, basicInfos)
	user = session['org_asc']
	sendData['sub'] = "Order Processing"
	sendData["msg"] = "Order Processing is started by :" + user
	sendData['number'] = num
	sendData['mail'] = mail
	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))

@app.route('/cancelOrder/<po_no>', methods=['POST'])
@login_required
def cancelOrder(po_no):
	session['cancel_order'] = True
	num = ''
	mail = ''
	sendData={}
	contact_info = ASC_orderMgmt_db.get_number(po_no)
	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']
	basicInfos = {}	
	basicInfos['overall_status'] = 'Cancelled'	
	ASC_orderMgmt_db.update_overall_status(po_no, basicInfos)
	user = session['org_asc']
	sendData['sub'] = "Order Cancelled"
	sendData["msg"] = "Order cancelled by :" + user
	sendData['number'] = num
	sendData['mail'] = mail
	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)
	changeLog(po_no)
	return redirect(url_for('order'))

@app.route('/completeOrder/<po_no>', methods=['POST'])
@login_required
def completeOrder(po_no):
	session['complete_Order'] = True
	num = ''
	mail = ''
	sendData={}
	contact_info = ASC_orderMgmt_db.get_number(po_no)
	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']
	basicInfos = {}	
	basicInfos['overall_status'] = 'Closed'	
	ASC_orderMgmt_db.update_overall_status(po_no, basicInfos)
	user = session['org_asc']
	sendData['sub'] = "Order Completed"
	sendData["msg"] = "Order Completed by :" + user
	sendData['number'] = num
	sendData['mail'] = mail
	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)
	changeLog(po_no)
	return redirect(url_for('order'))

@app.route('/moveto/dc_ownership/<po_no>/<dcName>', methods=['POST'])
@login_required
def moveto_dc_ownership(po_no, dcName):
	session['dcOwnership'] = True
	num = ''
	mail = ''
	dc_num = ''
	dc_mail = ''
	sendData = {}
	contact_info = ASC_orderMgmt_db.get_number(po_no)
	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']

	dc_contact_info = ASC_orderMgmt_db.get_dc_contact(dcName)
	for dc in dc_contact_info:

		dc_num = dc['dc_phone']
		dc_mail = dc['dc_email']


	dc_ownership_date = generateCurrentDate()
	sendData['sub'] = "Ownership changed"
	sendData['msg'] = "Ownership transfered to :" + dcName
	sendData['dc_ownership_date'] = dc_ownership_date
	sendData['dc_ownership'] = True
	sendData['number'] = num
	sendData['mail'] = mail
	sendData['dc_number'] = dc_num
	sendData['dc_mail'] = dc_mail
	ASC_orderMgmt_db.update_dc_ownership(po_no, sendData)
	send_mail_to_dc(po_no, sendData)
	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))

@app.route('/moveto/contractor_ownership/<po_no>/<conName>', methods=['POST'])
@login_required
def moveto_contractor_ownership(po_no, conName):
	session['contractor_ownership'] = True
	num = ''
	mail = ''
	contact_info = ASC_orderMgmt_db.get_number(po_no)
	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']

	contractor_contact_info = ASC_orderMgmt_db.get_contractor_info(conName)
	for cc in contractor_contact_info:
		con_num = cc['emp_mobile_1']
		con_mail = cc['email_1']

	sendData = {}
	sendData['sub'] = "Ownership changed"
	sendData['msg'] = "Ownership transfered to :" + conName
	sendData['contractor_ownership_ready'] = True
	sendData['contractor_ownership_date'] = generateCurrentDate()
	sendData['number'] = num
	sendData['mail'] = mail	
	sendData['con_number'] = con_num
	sendData['con_mail'] = con_mail
	ASC_orderMgmt_db.update_contractor_ownership(po_no, sendData)	
	send_mail_to_contractor(po_no, sendData)
	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)
	changeLog(po_no)
	return redirect(url_for('setBasicInformation', po_no = po_no))



@app.route('/manageStatus/<po_no>', methods=['POST'])
@login_required
def manageStatus(po_no):
	session['manage_status'] = True

	manageStatus = {}
	sendData = {}
	num = ''
	mail = ''

	contact_info = ASC_orderMgmt_db.get_number(po_no)

	for c in contact_info:
		num = c['consumer_primary_phone']
		mail = c['consumer_email']

	status = request.form.get('statusTitle')
	status_desc = request.form['statusDesc']
	status_date = generateCurrentDate()

	manageStatus['status_id'] = generate_random_id(3,4)
	manageStatus['po_number'] = po_no
	manageStatus['status'] = status
	manageStatus['status_description'] = status_desc
	manageStatus['status_modified_date'] = status_date

	ASC_orderMgmt_db.save_status(manageStatus)	

	user = session['org_asc']

	sendData['po_no'] = po_no
	sendData['user'] = user
	sendData['sub'] = 'Order Status changed'
	sendData['msg'] = 'Order Status : ' + status_desc +''
	sendData['number'] = num
	sendData['mail'] = mail

	send_mail_to_cons(po_no, sendData)
	send_msg_to_cons(po_no, sendData)

	changeLog(po_no)	
	return redirect(url_for('setBasicInformation', po_no = po_no))

@app.route('/add_shipping_pickup/<pono>', methods=['POST'])
@login_required
def add_shipping_pickup(pono):
	session['shipping_pickup'] = True
	addShppingPickup = request.form['shipping_pickup']
	ASC_orderMgmt_db.save_shipping_pickup(pono, addShppingPickup)
	changeLog(pono)
	return redirect(url_for('setBasicInformation', po_no = pono))









# ****************Labor Rate*********************************************

def get_list(lf, rate_list):
	labor_field = {}
	labor_field['id_name'] = lf['contractor_labor_id_name']
	labor_field['label'] = lf['contractor_labor_UI_label']
	labor_field['price'] = rate_list[0][lf['contractor_labor_id_name']]
	return labor_field
 


def set_labor_rates(d, labor_desc, laborRate):
	service_id = ''
	labor_rate_fields = {}
	rate_type = ''
	con_uPrice = 0.0


	def get_labor_id(service):
		labor_id = ''
		for i in labor_desc:
			if service == i['retail_labor_service']:
				labor_id = i['retail_labor_id_name']
		return labor_id

	
	if d['labor_service1']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service1'])
		con_uPrice = laborRate[0][service_id] 
		service = d['labor_service1']
		qty = d['labor_service1_quantity']
		uPrice = d['labor_service1_unit_price']
		ePrice = d['labor_service1_extended_price']
		
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service1'] = service
		labor_rate_fields['labor_service1_quantity'] = qty
		labor_rate_fields['labor_service1_unit_price'] = uPrice

		labor_rate_fields['labor_service1_extended_price'] = ePrice
		labor_rate_fields['labor_service1_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service1_con_ext_price'] = con_ePrice

		


	if d['labor_service2']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service2'])
		con_uPrice = laborRate[0][service_id]
		service = d['labor_service2']
		qty = d['labor_service2_quantity']
		uPrice = d['labor_service2_unit_price']
		ePrice = d['labor_service2_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['service_id1'] = service_id
		labor_rate_fields['labor_service2'] = service
		labor_rate_fields['labor_service2_quantity'] = qty
		labor_rate_fields['labor_service2_unit_price'] = uPrice

		labor_rate_fields['labor_service2_extended_price'] = ePrice
		labor_rate_fields['labor_service2_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service2_con_ext_price'] = con_ePrice


	if d['labor_service3']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service3'])
		try:
			con_uPrice = laborRate[0][service_id]
		except:
			con_uPrice = ''
		service = d['labor_service3']
		qty = d['labor_service3_quantity']
		uPrice = d['labor_service3_unit_price']
		ePrice = d['labor_service3_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service3'] = service
		labor_rate_fields['labor_service3_quantity'] = qty
		labor_rate_fields['labor_service3_unit_price'] = uPrice

		labor_rate_fields['labor_service3_extended_price'] = ePrice
		labor_rate_fields['labor_service3_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service3_con_ext_price'] = con_ePrice



	if d['labor_service4']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service4'])
		con_uPrice = laborRate[0][service_id]
		service = d['labor_service4']
		qty = d['labor_service4_quantity']
		uPrice = d['labor_service4_unit_price']
		ePrice = d['labor_service4_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service4'] = service
		labor_rate_fields['labor_service4_quantity'] = qty
		labor_rate_fields['labor_service4_unit_price'] = uPrice

		labor_rate_fields['labor_service4_extended_price'] = ePrice
		labor_rate_fields['labor_service4_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service4_con_ext_price'] = con_ePrice



	if d['labor_service5']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service5'])
		con_uPrice = laborRate[0][service_id]
		service = d['labor_service5']
		qty = d['labor_service5_quantity']
		uPrice = d['labor_service5_unit_price']
		ePrice = d['labor_service5_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service5'] = service
		labor_rate_fields['labor_service5_quantity'] = qty
		labor_rate_fields['labor_service5_unit_price'] = uPrice

		labor_rate_fields['labor_service5_extended_price'] = ePrice
		labor_rate_fields['labor_service5_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service5_con_ext_price'] = con_ePrice



	if d['labor_service6']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service6'])
		con_uPrice = laborRate[0][service_id]
		service = d['labor_service6']
		qty = d['labor_service6_quantity']
		uPrice = d['labor_service6_unit_price']
		ePrice = d['labor_service6_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service6'] = service
		labor_rate_fields['labor_service6_quantity'] = qty
		labor_rate_fields['labor_service6_unit_price'] = uPrice

		labor_rate_fields['labor_service6_extended_price'] = ePrice
		labor_rate_fields['labor_service6_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service6_con_ext_price'] = con_ePrice



	if d['labor_service7']:
		col_id = d['door_spec_id']
		service_id = get_labor_id(d['labor_service7'])
		con_uPrice = laborRate[0][service_id]
		service = d['labor_service7']
		qty = d['labor_service7_quantity']
		uPrice = d['labor_service7_unit_price']
		ePrice = d['labor_service7_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service7'] = service
		labor_rate_fields['labor_service7_quantity'] = qty
		labor_rate_fields['labor_service7_unit_price'] = uPrice

		labor_rate_fields['labor_service7_extended_price'] = ePrice
		labor_rate_fields['labor_service7_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service7_con_ext_price'] = con_ePrice



	# Special Labor Rates-----------------------------------------------
	if d['labor_service8']:
		col_id = d['door_spec_id']
		con_uPrice = ''
		service = d['labor_service8']
		qty = d['labor_service8_quantity']
		uPrice = d['labor_service8_unit_price']
		ePrice = d['labor_service8_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service8'] = service
		labor_rate_fields['labor_service8_quantity'] = qty
		labor_rate_fields['labor_service8_unit_price'] = uPrice

		labor_rate_fields['labor_service8_extended_price'] = ePrice
		labor_rate_fields['labor_service8_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service8_con_ext_price'] = con_ePrice


			

	if d['labor_service9']:
		col_id = d['door_spec_id']
		con_uPrice = ''
		service = d['labor_service9']
		qty = d['labor_service9_quantity']
		uPrice = d['labor_service9_unit_price']
		ePrice = d['labor_service9_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service9'] = service
		labor_rate_fields['labor_service9_quantity'] = qty
		labor_rate_fields['labor_service9_unit_price'] = uPrice

		labor_rate_fields['labor_service9_extended_price'] = ePrice
		labor_rate_fields['labor_service9_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service9_con_ext_price'] = con_ePrice


			

	if d['labor_service10']:
		col_id = d['door_spec_id']
		con_uPrice = ''
		service = d['labor_service10']
		qty = d['labor_service10_quantity']
		uPrice = d['labor_service10_unit_price']
		ePrice = d['labor_service10_extended_price']
		con_ePrice = 0.0

		labor_rate_fields['collection_id'] = col_id
		labor_rate_fields['labor_service10'] = service
		labor_rate_fields['labor_service10_quantity'] = qty
		labor_rate_fields['labor_service10_unit_price'] = uPrice

		labor_rate_fields['labor_service10_extended_price'] = ePrice
		labor_rate_fields['labor_service10_con_unit_price'] = con_uPrice
		labor_rate_fields['labor_service10_con_ext_price'] = con_ePrice


	return labor_rate_fields





# =============================================[ Refresh Module ]=================================================


def refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate):
	labor_rate_dict = {}
	ap_door_spec_id = ''
	con_u_p = 0
	con_unit_price = 0.0
	con_spec_price = ''
	con_ext_price = 0.0
	unit_price = 0.0
	ext_price = 0.0
	spec_price = ''
	rate_type = ''
	qty = 0
	labor_con_spec_price = ''
	labor_con_ext_price = 0.0
			
	for aplr in labor_rate_ap:
		if order_labor_service['door_spec_id'] == aplr['door_spec_id']:
			ap_door_spec_id = aplr['door_spec_id']
			if session['labor_service'] == 'labor_service1':	
				ap_name = order_labor_service['ret_labor_type']		
				ap_qty = aplr['labortype1_qty']
				ap_rate_type = aplr['labortype1_rate_type']
				ap_unit_price = aplr['labortype1_unit_price']
				ap_ext_price = aplr['labortype1_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service2':	
				ap_name = order_labor_service['ret_labor_type']	
				ap_qty = aplr['labortype2_qty']
				ap_rate_type = aplr['labortype2_rate_type']
				ap_unit_price = aplr['labortype2_unit_price']
				ap_ext_price = aplr['labortype2_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service3':	
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype3_qty']
				ap_rate_type = aplr['labortype3_rate_type']
				ap_unit_price = aplr['labortype3_unit_price']
				ap_ext_price = aplr['labortype3_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service4':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype4_qty']
				ap_rate_type = aplr['labortype4_rate_type']
				ap_unit_price = aplr['labortype4_unit_price']
				ap_ext_price = aplr['labortype4_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service5':
				ap_name = order_labor_service['ret_labor_type']		
				ap_qty = aplr['labortype5_qty']
				ap_rate_type = aplr['labortype5_rate_type']
				ap_unit_price = aplr['labortype5_unit_price']
				ap_ext_price = aplr['labortype5_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service6':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype6_qty']
				ap_rate_type = aplr['labortype6_rate_type']
				ap_unit_price = aplr['labortype6_unit_price']
				ap_ext_price = aplr['labortype6_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service7':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype7_qty']
				ap_rate_type = aplr['labortype7_rate_type']
				ap_unit_price = aplr['labortype7_unit_price']
				ap_ext_price = aplr['labortype7_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service8':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype8_qty']
				ap_rate_type = 'Special Rate'
				ap_unit_price = aplr['labortype8_unit_price']
				ap_ext_price = aplr['labortype8_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				# labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service9':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype9_qty']
				ap_rate_type = 'Special Rate'
				ap_unit_price = aplr['labortype9_unit_price']
				ap_ext_price = aplr['labortype9_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				# labor_id = order_labor_service['labor_type_id']

			if session['labor_service'] == 'labor_service10':
				ap_name = order_labor_service['ret_labor_type']
				ap_qty = aplr['labortype10_qty']
				ap_rate_type = 'Special Rate'
				ap_unit_price = aplr['labortype10_unit_price']
				ap_ext_price = aplr['labortype10_ext_price']
				ret_qty = order_labor_service['ret_qty']
				ret_unit_price = order_labor_service['ret_unit_price']
				ret_ext_price = order_labor_service['ret_ext_price']
				# labor_id = order_labor_service['labor_type_id']
				
	
	if order_labor_service['door_spec_id'] == ap_door_spec_id:		
		if labor_id:
			try:
				con_unit_price = float(laborRate[0][labor_id])
			except:
				con_unit_price = ''
				# con_unit_price = "{:.2f}".format(0.0)
		else:
			con_unit_price = ''
		# account payable qty exists
		if ap_qty:
			# account payable qty  == order labor rate qty
			if ap_qty == order_labor_service['ret_qty']:
				qty = ap_qty

				# check ap unit price existance
				if ap_unit_price:
					if float(ap_unit_price) == con_unit_price:
						rate_type = 'Default Rate'
						unit_price = "{:.2f}".format(float(ap_unit_price))
						ext_price =  "{:.2f}".format(float(qty)*float(unit_price))
					else:
						if ap_rate_type == 'Default Rate':
							rate_type = ap_rate_type
							unit_price =  "{:.2f}".format(float(con_unit_price))
							ext_price =  "{:.2f}".format(float(qty)*float(unit_price))
						elif ap_rate_type == 'Special Rate':
							rate_type = ap_rate_type
							if con_unit_price == '':
								unit_price =  0
							else:
								unit_price =  "{:.2f}".format(float(con_unit_price))
							spec_price =  "{:.2f}".format(float(ap_unit_price))
							ext_price =  "{:.2f}".format(float(qty)*float(spec_price))
				else:
					rate_type = ''
					unit_price =  "{:.2f}".format(float(con_unit_price))
					ext_price =  "{:.2f}".format(float(ap_ext_price))

			# account payable qty  != order labor rate qty
			else:
				qty = ap_qty
				if ap_unit_price:
					if ap_rate_type == 'Special Rate':
						qty = order_labor_service['ret_qty']
						rate_type = 'Special Rate'
						spec_price =  "{:.2f}".format(float(ap_unit_price))
						unit_price =  "{:.2f}".format(con_unit_price)
						ext_price =  "{:.2f}".format((float(qty) * spec_price))
					elif ap_rate_type == 'Default Rate':
						rate_type = 'Default Rate'
						unit_price =  "{:.2f}".format(float(con_unit_price))
						qty = order_labor_service['ret_qty']
						ext_price =  "{:.2f}".format(float(qty)*float(unit_price))
				else:
					rate_type = ''
					unit_price = ''
					ext_price = ''

		# Account payable qty doesnt exists
		else:
			if session['labor_service'] == 'labor_service8' or session['labor_service'] == 'labor_service9' or session['labor_service'] == 'labor_service10' :
				labor_id = ''
				unit_price = ''
			else:

				labor_id = order_labor_service['labor_type_id']
				if con_unit_price == '':
					unit_price = "{:.2f}".format(0.0)
				else:
					unit_price = "{:.2f}".format(float(con_unit_price))

			qty = order_labor_service['ret_qty']
			rate_type = ''
			ext_price = ''
			
		

	labor_rate_dict['labor_type'] = order_labor_service['ret_labor_type']
	labor_rate_dict['labor_ret_qty'] = qty
	labor_rate_dict['labor_ret_unit_price'] = order_labor_service['ret_unit_price']
	labor_rate_dict['labor_ret_ext_price'] = order_labor_service['ret_ext_price']
	labor_rate_dict['labor_rate_type'] = rate_type
	labor_rate_dict['labor_con_unit_price'] = unit_price
	labor_rate_dict['labor_con_spec_price'] = spec_price
	labor_rate_dict['labor_con_ext_price'] = ext_price	

	

	return labor_rate_dict


# Account Payable Edit Page ====================================================================================

@app.route('/accountPayable/<con_id>/<po_no>', methods=['POST', 'GET'])
@login_required
def account_payable(con_id, po_no):
	labor_desc = []
	door_list = []
	laborRate = []
	labor_rate_ap = []
	col_list = []
	session['labor_rate_list'] = []
	session['special_labor_rates'] = []
	labor_rate_fields = {}
	con_uPrice = 0.0	
	updated_labor_rate = {}


	# -------------------------------------------------------------------------

	# retail order labor rate from door specification
	door_records = ASC_orderMgmt_db.get_all_collections_labor_rates(po_no)

	# Contractor Labor rates
	labor_rate = ASC_orderMgmt_db.get_labor_rate_infos(con_id)	

	# retailer labor rates description
	labor_rate_id_service = ASC_orderMgmt_db.get_labor_rate_id()

	# Contractor order account payable for a retailer
	acc_payable_fields = ASC_orderMgmt_db.get_acc_payable_fields(po_no)

	# --------------------------------------------------------------------------

	for desc in labor_rate_id_service:
		labor_desc.append(desc)
	
	for dr in door_records:
		door_list.append(dr)

	for ap in acc_payable_fields:
		labor_rate_ap.append(ap)

	for lr in labor_rate:
		laborRate.append(lr)
	
	qty = 0
	ext_price = 0.0
	unit_price = 0.0

	def get_labor_id(service):
		labor_id = ''
		for i in labor_desc:
			if service == i['retail_labor_service']:
				labor_id = i['retail_labor_id_name']
		return labor_id


	for door in door_list:

		order_labor_service = {}
		updated_labor_service = {}
		door_spec_id = door['door_spec_id']

		# if labor_service1 has value	
		if door['labor_service1']:
			session['labor_service'] = 'labor_service1'
			labor_rate_id = get_labor_id(door['labor_service1'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service1']
			order_labor_service['ret_qty'] = door['labor_service1_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service1_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service1_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service1'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service1_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service1_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service1_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service1_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service1_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service1_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service1_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

			# session['special_labor_rates'].append(updated_labor_service)
			

		if door['labor_service2']:
			session['labor_service'] = 'labor_service2'
			labor_rate_id = get_labor_id(door['labor_service2'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service2']
			order_labor_service['ret_qty'] = door['labor_service2_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service2_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service2_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service2'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service2_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service2_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service2_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service2_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service2_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service2_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service2_con_ext_price'] = updated_labor_rate['labor_con_ext_price']
			
			# session['special_labor_rates'].append(updated_labor_service)

		if door['labor_service3']:
			session['labor_service'] = 'labor_service3'
			labor_rate_id = get_labor_id(door['labor_service3'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service3']
			order_labor_service['ret_qty'] = door['labor_service3_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service3_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service3_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service3'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service3_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service3_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service3_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service3_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service3_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service3_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service3_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

		if door['labor_service4']:
			session['labor_service'] = 'labor_service4'
			labor_rate_id = get_labor_id(door['labor_service4'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service4']
			order_labor_service['ret_qty'] = door['labor_service4_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service4_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service4_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service4'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service4_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service4_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service4_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service4_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service4_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service4_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service4_con_ext_price'] = updated_labor_rate['labor_con_ext_price']
			

		if door['labor_service5']:
			session['labor_service'] = 'labor_service5'
			labor_rate_id = get_labor_id(door['labor_service5'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service5']
			order_labor_service['ret_qty'] = door['labor_service5_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service5_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service5_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service5'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service5_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service5_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service5_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service5_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service5_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service5_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service5_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

		if door['labor_service6']:
			session['labor_service'] = 'labor_service6'
			labor_rate_id = get_labor_id(door['labor_service6'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service6']
			order_labor_service['ret_qty'] = door['labor_service6_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service6_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service6_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service6'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service6_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service6_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service6_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service6_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service6_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service6_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service6_con_ext_price'] = updated_labor_rate['labor_con_ext_price']


		if door['labor_service7']:
			session['labor_service'] = 'labor_service7'
			labor_rate_id = get_labor_id(door['labor_service7'])

			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service7']
			order_labor_service['ret_qty'] = door['labor_service7_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service7_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service7_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service7'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service7_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service7_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service7_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service7_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service7_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service7_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service7_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

		if door['labor_service8']:
			session['labor_service'] = 'labor_service8'		
			order_labor_service['labor_type_id'] = ''
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service8']
			order_labor_service['ret_qty'] = door['labor_service8_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service8_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service8_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service8'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service8_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service8_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service8_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service8_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service8_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service8_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service8_con_ext_price'] = updated_labor_rate['labor_con_ext_price']


			# ----

		if door['labor_service9']:
			session['labor_service'] = 'labor_service9'

			order_labor_service['labor_type_id'] = ''
			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service9']
			order_labor_service['ret_qty'] = door['labor_service9_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service9_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service9_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service9'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service9_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service9_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service9_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service9_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service9_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service9_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service9_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

		if door['labor_service10']:
			session['labor_service'] = 'labor_service10'
			order_labor_service['labor_type_id'] = ''
			order_labor_service['labor_type_id'] = labor_rate_id
			order_labor_service['door_spec_id'] = door_spec_id
			order_labor_service['ret_labor_type'] = door['labor_service10']
			order_labor_service['ret_qty'] = door['labor_service10_quantity']
			order_labor_service['ret_unit_price'] = door['labor_service10_unit_price']
			order_labor_service['ret_ext_price'] = door['labor_service10_extended_price']

			updated_labor_rate = refresh_module(order_labor_service, labor_rate_ap, labor_desc, laborRate)

			updated_labor_service['collection_id'] = door_spec_id
			updated_labor_service['labor_service10'] = updated_labor_rate['labor_type']
			updated_labor_service['labor_service10_quantity'] = updated_labor_rate['labor_ret_qty']
			updated_labor_service['labor_service10_unit_price'] = updated_labor_rate['labor_ret_unit_price']
			updated_labor_service['labor_service10_extended_price'] = updated_labor_rate['labor_ret_ext_price']
			updated_labor_service['labor_service10_rate_type'] = updated_labor_rate['labor_rate_type']
			updated_labor_service['labor_service10_con_unit_price'] = updated_labor_rate['labor_con_unit_price']
			updated_labor_service['labor_service10_con_special_price'] = updated_labor_rate['labor_con_spec_price']
			updated_labor_service['labor_service10_con_ext_price'] = updated_labor_rate['labor_con_ext_price']

		# if labor_service1 does not has value
		else:

			qty = 0
			unit_price = 0.0
			ext_price = 0.0

		session['special_labor_rates'].append(updated_labor_service)

	for d in door_list:
		col_list.append(d['door_spec_id'])
		# labor_rate_fields = set_labor_rates(d, labor_desc, laborRate)
		# session['labor_rate_list'].append(labor_rate_fields)
	# -----------------------------------------------------------------------

	return render_template('account_payable_edit.html',												
							user = session['username_asc'],
							p_num = po_no,
							con_id = con_id,
							labor_rates = session['special_labor_rates'],
							col_list = col_list) 

@app.route('/accountPayableSummary/<po_no>', methods=['POST'])
@login_required
def accountPayableSummary(po_no):
	rates_list = []
	ap_labor_rates = ASC_orderMgmt_db.get_updated_labor_rates(po_no)
	for rates in ap_labor_rates:
		rates_list.append(rates)
	return render_template('account_payable_summary.html', 											
							user = session['username_asc'],
							rates_list = rates_list,
							po_num = po_no)



def set_rate_history(ids, conId, p_num, special_rate):
	special_rate_history = {}
	special_rate_history['labor_rate_id'] = ids
	special_rate_history['contractor_id'] = conId
	special_rate_history['retailer_po_no'] = p_num
	special_rate_history['special_rate'] = special_rate
	ASC_orderMgmt_db.save_special_rate_history(special_rate_history)
	return


def add_labor_rates(ids, conId, p_num):
	default_rates = []
	special_rates = []
	rate = 0.0
	special_rate = 0.0
	value_type_ids = 'laborValue_'+ids
	default_value = 'default_value_'+ids
	special_value = 'special_value_'+ids
	value_type = request.form.get(value_type_ids)	

	if value_type:
		if value_type == 'Default Value':
			rate = float(request.form.get(default_value))
		elif value_type == 'Special Value':
			special_rate = request.form.get(special_value)
			get_rates_to_check = ASC_orderMgmt_db.check_rate(conId, p_num)
			for gr1 in get_rates_to_check[0]:
				default_rates.append(gr1)
			for gr2 in get_rates_to_check[1]:
				special_rates.append(gr2)
			if special_rate == default_rates[0][ids]:
				flash("no changes")
			else:
				rate_history = set_rate_history(ids, conId, p_num, special_rate)
			rate = float(special_rate)
		else:
			rate = 0.0
		ASC_orderMgmt_db.update_special_rate(conId, p_num, ids, rate)
	else:
		rate = 0.0
	return rate

@app.route('/save_price/<conId>/<p_num>', methods=['POST'])
@login_required
def save_price(conId, p_num):
	session['save_labor_rate'] = True
	rates = []
	rates_list = []
	labor_rate_ids = ASC_orderMgmt_db.get_all_labor_rates(conId)
	for l_rate in labor_rate_ids:
		rates = l_rate.keys()

		# add_labor_rates(rates)
	for r in rates:
		rate_value = add_labor_rates(r, conId, p_num)
		rates_list.append(rate_value)
	changeLog(p_num)
	# ASC_orderMgmt_db.update_price()
	return redirect(url_for('setBasicInformation', po_no = p_num))

# def set_labor_rates(door_id, po_num):
# 	labor_rates = {}
# 	labor_rates['labortype1_name'] = request.form


@app.route('/set_labor_rate/<door_id>/<po_num>/<con_id>/', methods=['POST'])
@login_required
def set_labor_rate(door_id, po_num, con_id):

	

	labor_type1 = {}

	labor_rates_list = []

	try:
		labor_service_type1 = request.form['labor_type1_'+door_id]
		if labor_service_type1:
			labor_type1['labor_service_type1'] = labor_service_type1 
			labor_type1['qty1'] = request.form['qty1_'+door_id]
			labor_type1['rate_type1'] = request.form.get('rateType1_'+door_id)
			if labor_type1['rate_type1'] == 'Default Rate':
				labor_type1['unit_price1'] = request.form['Con_default_unit_price1_'+door_id]
			elif labor_type1['rate_type1'] == 'Special Rate':
				labor_type1['unit_price1'] = request.form['Con_special_unit_price1_'+door_id]
			labor_type1['ext_price1'] = request.form['Con_ext_price1_'+door_id]

		else:
			labor_type1['labor_service_type1'] = ''
			labor_type1['qty1'] = 0
			labor_type1['rate_type1'] = ''
			labor_type1['unit_price1'] = "{:.2f}".format(0.0)
			labor_type1['ext_price1'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type1'] = ''
		labor_type1['qty1'] = 0
		labor_type1['rate_type1'] = ''
		labor_type1['unit_price1'] = "{:.2f}".format(0.0)
		labor_type1['ext_price1'] = "{:.2f}".format(0.0)
	

	#-----------------------------------------------------------------
	try:
		labor_service_type2 = request.form['labor_type2_'+door_id]
		if labor_service_type2:
			labor_type1['labor_service_type2'] = labor_service_type2
			labor_type1['qty2'] = request.form['qty2_'+door_id]
			labor_type1['rate_type2'] = request.form.get('rateType2_'+door_id)
			if labor_type1['rate_type2'] == 'Default Rate':
				labor_type1['unit_price2'] = request.form['Con_default_unit_price2_'+door_id]
			elif labor_type1['rate_type2'] == 'Special Rate':
				labor_type1['unit_price2'] = request.form['Con_special_unit_price2_'+door_id]
			labor_type1['ext_price2'] = request.form['Con_ext_price2_'+door_id]

		else:
			labor_type1['labor_service_type2'] = ''
			labor_type1['qty2'] = 0
			labor_type1['rate_type2'] = ''
			labor_type1['unit_price2'] = "{:.2f}".format(0.0)
			labor_type1['ext_price2'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type2'] = ''
		labor_type1['qty2'] = 0
		labor_type1['rate_type2'] = ''
		labor_type1['unit_price2'] = "{:.2f}".format(0.0)
		labor_type1['ext_price2'] = "{:.2f}".format(0.0)

	# -----------------------------------------------------------------
	try:
		labor_service_type3 = request.form['labor_type3_'+door_id]
		if labor_service_type3:
			labor_type1['labor_service_type3'] = labor_service_type3
			labor_type1['qty3'] = request.form['qty3_'+door_id]
			labor_type1['rate_type3'] = request.form['rateType3_'+door_id]
			if labor_type1['rate_type3'] == 'Default Rate':
				labor_type1['unit_price3'] = request.form['Con_default_unit_price3_'+door_id]
			elif labor_type1['rate_type3'] == 'Special Rate':
				labor_type1['unit_price3'] = request.form['Con_special_unit_price3_'+door_id]
			labor_type1['ext_price3'] = request.form['Con_ext_price3_'+door_id]
		else:
			labor_type1['labor_service_type3'] = ''
			labor_type1['qty3'] = 0
			labor_type1['rate_type3'] = ''
			labor_type1['unit_price3'] = "{:.2f}".format(0.0)
			labor_type1['ext_price3'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type3'] = ''
		labor_type1['qty3'] = 0
		labor_type1['rate_type3'] = ''
		labor_type1['unit_price3'] = "{:.2f}".format(0.0)
		labor_type1['ext_price3'] = "{:.2f}".format(0.0)

	

	# ---------------------------------------------------------------
	try:
		labor_service_type4 = request.form['labor_type4_'+door_id]
		if labor_service_type4:
			labor_type1['labor_service_type4'] = labor_service_type4
			labor_type1['qty4']  = request.form['qty4_'+door_id]
			labor_type1['rate_type4']  = request.form['rateType4_'+door_id]
			if labor_type1['rate_type4']  == 'Default Rate':
				labor_type1['unit_price4'] = request.form['Con_default_unit_price4_'+door_id]
			elif labor_type1['rate_type4']  == 'Special Rate':
				labor_type1['unit_price4'] = request.form['Con_special_unit_price4_'+door_id]
			labor_type1['ext_price4'] = request.form['Con_ext_price4_'+door_id]
			
		else:
			labor_type1['labor_service_type4'] = ''
			labor_type1['qty4'] = 0
			labor_type1['rate_type4'] = ''
			labor_type1['unit_price4'] = "{:.2f}".format(0.0)
			labor_type1['ext_price4'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type4'] = ''
		labor_type1['qty4'] = 0
		labor_type1['rate_type4'] = ''
		labor_type1['unit_price4'] = "{:.2f}".format(0.0)
		labor_type1['ext_price4'] = "{:.2f}".format(0.0)

	# -------------------------------------------------------------------
	try:
		labor_service_type5 = request.form['labor_type5_'+door_id]
		if labor_service_type5:
			labor_type1['labor_service_type5'] = labor_service_type5
			labor_type1['qty5'] = request.form['qty5_'+door_id]
			labor_type1['rate_type5'] = request.form['rateType5_'+door_id]
			if labor_type1['rate_type5'] == 'Default Rate':
				labor_type1['unit_price5'] = request.form['Con_default_unit_price5_'+door_id]
			elif labor_type1['rate_type5'] == 'Special Rate':
				labor_type1['unit_price5'] = request.form['Con_special_unit_price5_'+door_id]
			labor_type1['ext_price5'] = request.form['Con_ext_price5_'+door_id]
		else: 
			labor_type1['labor_service_type5'] = ''
			labor_type1['qty5'] = 0
			labor_type1['rate_type5'] = ''
			labor_type1['unit_price5'] = "{:.2f}".format(0.0)
			labor_type1['ext_price5'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type5'] = ''
		labor_type1['qty5'] = 0
		labor_type1['rate_type5'] = ''
		labor_type1['unit_price5'] = "{:.2f}".format(0.0)
		labor_type1['ext_price5'] = "{:.2f}".format(0.0)

	# -------------------------------------------------------------------

	try:
		labor_service_type6 = request.form['labor_type6_'+door_id]
		if labor_service_type6:
			labor_type1['labor_service_type6'] = labor_service_type6
			labor_type1['qty6'] = request.form['qty6_'+door_id]
			labor_type1['rate_type6'] = request.form['rateType6_'+door_id]
			if labor_type1['rate_type6'] == 'Default Rate':
				unit_price6 = request.form['Con_default_unit_price6_'+door_id]
			elif labor_type1['rate_type6'] == 'Special Rate':
				unit_price6 = request.form['Con_special_unit_price6_'+door_id]
			labor_type1['unit_price6'] = unit_price6
			labor_type1['ext_price6'] = request.form['Con_ext_price6_'+door_id]

		else:
			labor_type1['labor_service_type6'] = ''
			labor_type1['qty6'] = 0
			labor_type1['rate_type6'] = ''
			labor_type1['unit_price6'] = "{:.2f}".format(0.0)
			labor_type1['ext_price6'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type6'] = ''
		labor_type1['qty6'] = 0
		labor_type1['rate_type6'] = ''
		labor_type1['unit_price6'] = "{:.2f}".format(0.0)
		labor_type1['ext_price6'] = "{:.2f}".format(0.0)

	# -------------------------------------------------------------------

	try:
		labor_service_type7 = request.form['labor_type7_'+door_id]
		if labor_service_type7:
			labor_type1['labor_service_type7'] = labor_service_type7
			labor_type1['qty7'] = request.form['qty7_'+door_id]
			labor_type1['rate_type7'] = request.form['rateType7_'+door_id]			
			if labor_type1['rate_type7'] == 'Default Rate':
				unit_price7 = request.form['Con_default_unit_price7_'+door_id]
			elif labor_type1['rate_type7'] == 'Special Rate':
				unit_price7 = request.form['Con_special_unit_price7_'+door_id]
			labor_type1['unit_price7'] = unit_price7
			labor_type1['ext_price7'] = request.form['Con_ext_price7_'+door_id]

		else:
			labor_type1['labor_service_type7'] = ''
			labor_type1['qty7'] = 0
			labor_type1['rate_type7'] = ''
			labor_type1['unit_price7'] = "{:.2f}".format(0.0)
			labor_type1['ext_price7'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type7'] = ''
		labor_type1['qty7'] = 0
		labor_type1['rate_type7'] = ''
		labor_type1['unit_price7'] = "{:.2f}".format(0.0)
		labor_type1['ext_price7'] = "{:.2f}".format(0.0)
	

	# -------------------------------------------------------------------

	try:
		labor_service_type8 = request.form['labor_type8_'+door_id]
		if labor_service_type8:
			labor_type1['labor_service_type8'] = labor_service_type8
			labor_type1['qty8'] = request.form['qty8_'+door_id]
			labor_type1['rate_type8'] = request.form['rateType8_'+door_id]
			labor_type1['unit_price8'] = request.form['Con_special_unit_price8_'+door_id]
			labor_type1['ext_price8'] = request.form['Con_ext_price8_'+door_id]	
		else:
			labor_type1['labor_service_type8'] = ''
			labor_type1['qty8'] = 0
			labor_type1['rate_type8'] = ''
			labor_type1['unit_price8'] = "{:.2f}".format(0.0)
			labor_type1['ext_price8'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type8'] = ''
		labor_type1['qty8'] = 0
		labor_type1['rate_type8'] = ''
		labor_type1['unit_price8'] = "{:.2f}".format(0.0)
		labor_type1['ext_price8'] = "{:.2f}".format(0.0)
	# -------------------------------------------------------------------

	try:
		labor_service_type9 = request.form['labor_type9_'+door_id]
		if labor_service_type9:
			labor_type1['labor_service_type9'] = labor_service_type9
			labor_type1['qty9'] = request.form['qty9_'+door_id]
			labor_type1['rate_type9'] = request.form['rateType9_'+door_id]
			labor_type1['unit_price9'] = request.form['Con_special_unit_price9_'+door_id]
			labor_type1['ext_price9'] = request.form['Con_ext_price9_'+door_id]
		else:
			labor_type1['labor_service_type9'] = ''
			labor_type1['qty9'] = 0
			labor_type1['rate_type9'] = ''
			labor_type1['unit_price9'] = "{:.2f}".format(0.0)
			labor_type1['ext_price9'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type9'] = ''
		labor_type1['qty9'] = 0
		labor_type1['rate_type9'] = ''
		labor_type1['unit_price9'] = "{:.2f}".format(0.0)
		labor_type1['ext_price9'] = "{:.2f}".format(0.0)
	# -------------------------------------------------------------------

	try:
		labor_service_type10 = request.form['labor_type10_'+door_id]
		if labor_service_type10:
			labor_type1['labor_service_type10'] = labor_service_type10
			labor_type1['qty10'] = request.form['qty10_'+door_id]
			labor_type1['rate_type10'] = request.form['rateType10_'+door_id]
			labor_type1['unit_price10'] = request.form['Con_special_unit_price10_'+door_id]
			labor_type1['ext_price10'] = request.form['Con_ext_price10_'+door_id]

		else:
			labor_type1['labor_service_type10'] = ''
			labor_type1['qty10'] = 0
			labor_type1['rate_type10'] = ''
			labor_type1['unit_price10'] = "{:.2f}".format(0.0)
			labor_type1['ext_price10'] = "{:.2f}".format(0.0)
	except:
		labor_type1['labor_service_type10'] = ''
		labor_type1['qty10'] = 0
		labor_type1['rate_type10'] = ''
		labor_type1['unit_price10'] = "{:.2f}".format(0.0)
		labor_type1['ext_price10'] = "{:.2f}".format(0.0)

	# -------------------------------------------------------------------
	labor_rates_list.append(labor_type1)

	ASC_orderMgmt_db.update_con_order_ap(labor_rates_list, door_id, po_num)
	flash('Record successfully updated')
	# updated_labor_rates = set_labor_rates(door_id, po_num)
	# ASC_orderMgmt_db.save_ap_labor_rates(door_id, po_num)
	return redirect(url_for('account_payable', con_id = con_id, po_no = po_num))





# --------------------------------------------------------------------------------
# Contractor viewAll
# --------------------------------------------------------------------------------
@app.route('/get_contractor_list')
@login_required
def get_contractor_list():
	con_list = []
	con_cursor = ASC_orderMgmt_db.get_basic_details()
	for i in con_cursor:
		con_list.append(i)
	return render_template('contractors_view.html', contractorslist = con_list,  user = session['username_asc']) 
	



# ----------------------------------------------------------------------------------
# Door Center View All
# ----------------------------------------------------------------------------------
@app.route('/get_dc_list')
@login_required
def get_dc_list():
	dcbasicinfo_list = []
	dc_cursor = ASC_orderMgmt_db.get_dcbasicinfo_details()
	for i in dc_cursor:
		dcbasicinfo_list.append(i)
	return render_template('dc_view.html', dcbasicinfolist = dcbasicinfo_list,  user = session['username_asc'])



# ----------------------------------------------------------------------------------
# Retailer View All
# ----------------------------------------------------------------------------------
@app.route('/get_retailers')
@login_required
def get_retailers():
	rtlrInfo_list = []
	ret_cursor = ASC_orderMgmt_db.get_retailerInfo()
	for r in ret_cursor:
		rtlrInfo_list.append(r)
		return render_template('retailer_view.html', rtlrList = rtlrInfo_list,  user = session['username_asc'])


# ---------------------------------------------------------------------------------
# Search by Contractor & DC - Listing Page
# ---------------------------------------------------------------------------------


@app.route("/search_page/<search_type>")
@login_required
def search_page(search_type):
	contractor_list = []
	dc_list = []
	searchType = search_type
	all_orders = []
	search_item = ''
	orders_count = ''

	
	
	if searchType == 'Contractor': 
		con = ASC_orderMgmt_db.getContractorInfo()
		for c in con:
			contractor_list.append(c)

	elif searchType == 'DC': 
		dc = ASC_orderMgmt_db.getDCBasicInfo()		
		for d in dc:
			dc_list.append(d)
	if session['search_order']:
		if session['all_orders']:
			all_orders = sorted(session['all_orders'], key = lambda i: i['order_submitted_date'])
			orders_count = session['orders_count']
			# all_orders = session['all_orders']
			if searchType == 'Contractor':
				if contractor_list[0]['account'] == all_orders[0]['contractor_id']:
					search_item = contractor_list[0]['contractor_name']
			elif searchType == 'DC':
				search_item = all_orders[0]['door_center_name']
	else:
		all_orders = []


	session['search_order'] = False
	return render_template('search_by_contractor.html', 
							user = session['username_asc'],
							all_contractors = contractor_list,
							all_dc = dc_list,
							searchType = searchType, 
							all_orders =all_orders, 
							orders_count = orders_count, 
							search_item = search_item)


# ---------------------------------------------------------------------------------
# Search by Contractor & DC - Search 
# ---------------------------------------------------------------------------------

@app.route("/search_all_orders/<search_type>", methods=['POST', 'GET'])
@login_required
def search_all_orders(search_type):
	searchBy = []
	all_orders_list = []

	searchBy = request.form['search_by'].split(' - ')
	all_retailers = session['retailers']

	searchType = search_type
	if searchType == 'Contractor':
		for ar in all_retailers:
			all_orders = ASC_orderMgmt_db.get_all_records_by_con(ar['account'], searchBy[1])
			for ao in all_orders[0]:
				all_orders_list.append(ao)
				session['orders_count'] += all_orders[1]
			# session['all_open_orders'] = all_orders

	elif searchType == 'DC':
		for ar in all_retailers:
			all_orders = ASC_orderMgmt_db.get_all_records_by_dc(ar['account'], searchBy[1])
			for ao in all_orders[0]:
				all_orders_list.append(ao)
				session['orders_count'] += all_orders[1]
	
	# for ao in all_orders:
	# 	all_orders_list.append(ao)
	session['all_orders'] = all_orders_list
	session['orders_count'] = all_orders[1]
	session['search_order'] = True

	return redirect(url_for('search_page', search_type = search_type))

#********************************materials ready**************************************

# @app.route("/material_ready/<po_no>", methods=['POST'])
# def material_ready(po_no):
# 	mat_ready_info = {}
# 	m_ready = request.form['m_ready']
# 	if m_ready == 'Yes' :
# 		mat_ready_info['material_available'] = m_ready
	
# 		mat_ready_info['dc_material_available_date'] = generateCurrentDate()
# 		mat_ready_info['dc_material_submitted_by'] = session['fullname_asc'] + " ( "+ session['org_asc'] + " ) "

# 	ASC_orderMgmt_db.update_material_availability(po_no. mat_ready_info)



# ***************************Estimated date*******************************************
def generate_current_date():
	currentDT = datetime.datetime.now(pytz.timezone('US/Central'))
	date_time = currentDT.strftime("%Y %b %d ")
	return date_time

@app.route("/est_date_calc/<po_no>", methods=['POST'])
@login_required
def est_date_calc(po_no):
	eDate = request.form['est_date']
	eDate = datetime.datetime.strptime(eDate, '%Y-%m-%d')
	eDate = eDate.date()
	cDate = generateCurrentDate()
	c_date = datetime.datetime.strptime(cDate, '%Y %b %d %I:%M:%S%p')
	c_date_only = c_date.date()

	days_count = eDate - c_date_only
	r_days = days_count.days

	ASC_orderMgmt_db.update_est_date(po_no, str(eDate))

	return redirect(url_for('setBasicInformation', po_no = po_no))


# **********************Login Section***************************************************

@app.route("/login/")
def login():
	user_exists_flag = False
	if 'username_asc' in session:
		user_exists_flag = True

		session['dcOwnership'] = False
		session['records'] = []
		session['totalPages'] = 0
		session['recordsPerPage'] = 0
		session['orderCount'] = 0
		session['search_by_po'] = False
		session['search_by_dc'] = False
		session['search_by_status'] = False

		session['po_num'] = 0
		session['dc_id'] = ''
		session['check_status'] = ''
		session['diy'] = ''
		session['fni'] = ''
		session['con_id'] = ''

		session['search_results_activated_basicInfo'] = False
		session['search_code_page_number'] = ''
		session['search_term_page_number'] = '' 
		session['door_s_id'] = ''

		session['rPerPage'] = config['page_count']['RECORDS_PER_PAGE']
		session['defaultPage'] = config['page_count']['DEFAULT_PAGE']

		session['searchAll'] = config['searchcode']['SEARCH_ALL']
		session['searchPO'] = config['searchcode']['SEARCH_PO']
		session['searchDC'] = config['searchcode']['SEARCH_DC']
		session['searchStatus'] = config['searchcode']['SEARCH_STATUS']
		session['searchDIY'] = config['searchcode']['SEARCH_DIY']
		session['searchFNI'] = config['searchcode']['SEARCH_FNI']		

		session['special_labor_rates'] = []
		session['labor_service'] = ''

		session['dc_ownership'] = False
		session['contractor_ownership'] = False

		session['save_info'] = False
		session['duplicate_item'] = False
		session['delete_Door'] = False
		session['add_Item'] = False
		session['update_Item'] = False
		session['submit_Order'] = False
		session['add_note'] = False
		session['process_order'] = False
		session['complete_Order'] = False
		session['cancel_order'] = False
		session['manage_status'] = False
		session['save_dc_info'] = False
		session['mail_to_cons'] = False
		session['msg_to_cons'] = False

		session['save_con_info'] = False
		session['shipping_pickup'] = False
		session['mail_to_dc'] = False
		session['save_labor_rate'] = False

		session['all_orders'] = []
		session['search_order'] = False
		session['orders_count'] = 0

		session['count'] = 0
		
		return redirect(url_for('index'))
	else:
		return render_template('login.html', user = '', user_exists = user_exists_flag) 





@app.route("/login/attempt", methods=['POST'])
def login_attempt():
    login_id = request.form['id']
    login_pass = request.form['pass']
    cursor = ASC_orderMgmt_db.search_authorization_by_id(login_id)
    db_id = ''
    db_pass = ''
    db_auth_data = {}
    incorrect_pass_flag = False
    for c in cursor:
        db_auth_data = c
    if db_auth_data:
        if sha256_crypt.verify(login_pass, db_auth_data['password']):
            session['username_asc'] = db_auth_data['first_name']
            session['fullname_asc'] = db_auth_data['first_name'] + " " + db_auth_data['last_name']
            session['org_asc'] = db_auth_data['org_name']
            session['email_asc'] = db_auth_data['email']
            session['userId_asc'] = db_auth_data['user_id']
            session['userType_asc'] = db_auth_data['user_type']

            session['retailer_asc'] = ''

            session['retailers'] = []
            session['retailers'] = get_retailer()
            session['search_by'] = config['Search_by']['SEARCH_LIST'].split(', ')
            session.pop('_flashes', None)
        else:
        	incorrect_pass_flag = True
        	flash('incorrect user credentials')
    else:
    	incorrect_pass_flag = True
    	flash('incorrect user credentials')
    return redirect(url_for('login'))


@app.route('/delete-cookie/')
def delete_cookie():
    res = make_response("Cookie Removed")
    res.set_cookie('foo', 'bar', max_age=0)
    return res

@app.route('/test')
def test():
	test_dict = {}
	test_dict['name'] = 'Sundar'
	test_dict['place'] = 'Keonjhar'
	return render_template('account_payable_summary.html',
							test = test_dict )