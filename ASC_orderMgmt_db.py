from pymongo import MongoClient
from flask import session
import datetime
import sys


from bson.objectid import ObjectId

from configparser import ConfigParser
import configparser

from configparser import ConfigParser
import configparser

config = ConfigParser()
config.read('app_config.ini', encoding="utf8")


# *********************Global variables********************************
global con_retailer
global con_doorsOnline
global db_doorsOnline
global db_retailer
global col_retailer
global col_doorInfo
global col_basicInfo
global col_changeLog
global col_note
global col_dc_basic_info
global col_contractor_info
global col_contractor_acc_payable

global con_dc
global db_dc
global col_dc

global con_basic_info
global db_basic_info
global col_basic_info


global con_technician_info
global db_technician_info
global col_technician_info

global col_contractor
global col_dc_activate
global col_labor_rate_contractor
global col_labor_rate_ret

global con_status
global db_status
global col_diy
global col_fni


# ****************************Retailer info Config**************************************
def connect_retailer_db():
	global con_retailer
	global db_retailer
	global col_retailer
	global col_labor_rate_ret

	dbName = config['RetailerDB']['DB_NAME']
	colName = config['RetailerDB']['COLLECTION_NAME']
	labor_rate_ret = config['RetailerDB']['COLLECTION_LABOR_RATE']

	con_retailer = MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
												+config['database']['PASSWORD']+'@'
												+config['database']['HOST']+'/'
												+dbName
												+'?retryWrites=true&w=majority')
	# con_retailer = MongoClient('mongodb+srv://Sourav:l9EG8ULwylphgjHS@nexusfieldservice.axvp7.mongodb.net/Retailer_Db?retryWrites=true&w=majority')
	# db_retailer = con_retailer[dbName]
	# col_retailer = db_retailer[colName]
	db_retailer = con_retailer[dbName]
	col_retailer = db_retailer[colName]
	col_labor_rate_ret = db_retailer[labor_rate_ret]

# ****************************Door Center DB Config**********************************
def connect_dc_db():
	global con_dc
	global db_dc
	global col_dc
	global col_dc_activate
	global col_dc_deactivate

	dc_db_name = config['dc']['DB_NAME']
	dc_col = config['dc']['COLLECTION_NAME']
	dc_activate_col = config['dc']['COL_ACTIVATE']
	dc_deactivate_col = config['dc']['COL_DEACTIVATE']
	con_dc = MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
												+config['database']['PASSWORD']+'@'
												+config['database']['HOST']+'/'
												+dc_db_name
												+'?retryWrites=true&w=majority')
	db_dc = con_dc[dc_db_name]
	col_dc = db_dc[dc_col]
	col_dc_activate = db_dc[dc_activate_col]
	col_dc_deactivate = db_dc[dc_deactivate_col]


# *******************************All Retailers DB Config**********************************
def connect_DoorsOnline():
	global con_doorsOnline
	global db_doorsOnline
	global col_doorInfo
	global col_basicInfo
	global col_changeLog
	global col_note
	global col_sChange
	global col_labor_rate
	global col_special_rate_history	
	global col_contractor_acc_payable

	retailer_db = session['retailer_db_name_asc']
	doors_info = config['basic_collection']['COL_DOOR']
	log = config['basic_collection']['COL_LOG']
	order_info = config['basic_collection']['COL_ORDER']
	notes = config['basic_collection']['COL_NOTES']
	status = config['basic_collection']['COL_STATUS']
	# labor_rate = config['basic_collection']['COL_LABOR_RATE']
	labor_rate = 'contractor_order_labor_rate'
	special_labor_rate_history = 'special_labor_rate_history'
	con_order_labor_fields = config['basic_collection']['COL_LABOR_ACC_PAYABLE']

	con_doorsOnline = MongoClient('mongodb+srv://'
									+config['database']['USERNAME']+':'
									+config['database']['PASSWORD']+'@'
									+config['database']['HOST']+'/'
									+retailer_db
									+'?retryWrites=true&w=majority')
	db_doorsOnline = con_doorsOnline[retailer_db]
	col_doorInfo = db_doorsOnline[doors_info]
	col_basicInfo = db_doorsOnline[order_info]
	col_changeLog = db_doorsOnline[log]
	col_note = db_doorsOnline[notes]
	col_sChange = db_doorsOnline[status]
	col_labor_rate = db_doorsOnline[labor_rate]
	col_special_rate_history = db_doorsOnline[special_labor_rate_history]
	col_contractor_acc_payable = db_doorsOnline[con_order_labor_fields]

def connect_allRetailer_basic_info(retailer_id):
	global con_allRtailer
	global db_allRtailer
	global col_allRtailer

	retailer_db_name = retailer_id
	order_info = config['basic_collection']['COL_ORDER']
	con_allRtailer = MongoClient('mongodb+srv://'
									+config['database']['USERNAME']+':'
									+config['database']['PASSWORD']+'@'
									+config['database']['HOST']+'/'
									+retailer_db_name
									+'?retryWrites=true&w=majority')
	db_allRtailer = con_allRtailer[retailer_db_name]
	col_allRtailer = db_allRtailer[order_info]



# *****************************Login DB Config**********************************
def connect_login_db():
	global con_login
	global db_login
	global col_login

	db_auth = config['Authorization']['DB_NAME']
	col_auth = config['Authorization']['COLLECTION_NAME']
	con_login = MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
											+config['database']['PASSWORD']+'@'
											+config['database']['HOST']+'/'
											+db_auth
											+'?retryWrites=true&w=majority')
	db_login = con_login[db_auth]
	col_login = db_login[col_auth]



# ****************************Contractor DB Config*****************************************
def connect_contractor_db():
	global con_contractor
	global db_contractor
	global col_contractor
	global col_technician
	global col_labor_rate_contractor
	global col_con_dc

	contractor_db = config['Contractor']['DB_NAME']
	contractor_col = config['Contractor']['COLLECTION_NAME']
	technician_col = config['Contractor']['COLLECTION_NAME']
	contractor_by_dc_col = config['Contractor']['COL_DC'] 
	labor_rates_col = 'labor_rates_info'
	con_contractor = MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
											+config['database']['PASSWORD']+'@'
											+config['database']['HOST']+'/'
											+contractor_db
											+'?retryWrites=true&w=majority')
	db_contractor = con_contractor[contractor_db]
	col_contractor = db_contractor[contractor_col]
	col_technician = db_contractor[technician_col]
	col_labor_rate_contractor = db_contractor[labor_rates_col]
	col_con_dc = db_contractor[contractor_by_dc_col]



# ******************************Sensitive Access********************************
# -------------Sendgrid
# def connect_sensitive_data():
# 	global con_sensData
# 	global db_sensData
# 	global col_sens_data

# 	sense_info_db = config['Sensitive_info']['DB_NAME']
# 	sense_info_col = config['Sensitive_info']['COL_NAME']
# 	con_sensData= MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
# 											+config['database']['PASSWORD']+'@'
# 											+config['database']['HOST']+'/'
# 											+contractor_db
# 											+'?retryWrites=true&w=majority')


# ****************************Labor Rate Fields**************************************
def connect_labor_rate_fields():
	global con_lab_field
	global db_lab_field
	global col_lab_field
	global col_lab_desc

	labor_field_db = 'Labor_rates_db'
	labor_field_col = 'labor_rates_info'
	labor_desc_col = 'retailer_labor_rates_info'

	con_lab_field = MongoClient('mongodb+srv://'+config['database']['USERNAME']+':'
											+config['database']['PASSWORD']+'@'
											+config['database']['HOST']+'/'
											+labor_field_db
											+'?retryWrites=true&w=majority')
	db_lab_field = con_lab_field[labor_field_db]
	col_lab_field = db_lab_field[labor_field_col]
	col_lab_desc = db_lab_field[labor_desc_col]



# *************************Basic Info for Contractor**********************************

def connectBasicInfo_db():
  global con_basic_info
  global db_basic_info
  global col_basic_info
  con_basic_info = MongoClient('mongodb+srv://'+config['database']['USERNAME']
                    +':'
                    +config['database']['PASSWORD']
                    +'@'
                    +config['database']['HOST']
                    +'/'
                    +config['contractor_db']['DB_NAME']
                    +'?retryWrites=true&w=majority')
  
  db_basic_info = con_basic_info.Contractors_Db
  col_basic_info = db_basic_info.Contractors_Basic_Info

# *************************Technician Config*********************************************

def connect_technician_db():
  global con_technician_info
  global db_technician_info
  global col_technician_info
  con_technician_info = MongoClient('mongodb+srv://'+config['database']['USERNAME']
                    +':'
                    +config['database']['PASSWORD']
                    +'@'
                    +config['database']['HOST']
                    +'/'
                    +config['contractor_db']['DB_NAME']
                    +'?retryWrites=true&w=majority')
  db_technician_info = con_technician_info.Contractors_Db
  col_technician_info = db_technician_info.technician_info



# *****************************Status ********************************************************

def connect_status_db():
	global con_status
	global db_status
	global col_diy
	global col_fni

	db_name = config['order_type']['DB']
	order_diy = config['order_type']['COL_DIY']
	order_fni = config['order_type']['COL_F&I']
	con_status = MongoClient('mongodb+srv://'+config['database']['USERNAME']
                    +':'
                    +config['database']['PASSWORD']
                    +'@'
                    +config['database']['HOST']
                    +'/'
                    +db_name
                    +'?retryWrites=true&w=majority')

	db_status = con_status[db_name]
	col_diy = db_status[order_diy]
	col_fni = db_status[order_fni]

#******************************Operations*****************************************************



def update_order_labor_rate(rates_dict):
	global col_labor_rate
	connect_DoorsOnline()
	col_labor_rate.insert(rates_dict)
	return

def getDCBasicInfo():
	global col_dc
	connect_dc_db()
	dcInfo = col_dc.find({}, {'_id': False, 'dc_name':1, 'dc_number':1})
	return dcInfo

def get_dc_contact(dcName):
	global col_dc
	connect_dc_db()
	dc_contact = col_dc.find({"dc_name":dcName}, {'_id': False})
	return dc_contact

def update_dc_ownership(po_no, sendData):
	global col_basicInfo
	connect_DoorsOnline()
	dc_o_date = sendData['dc_ownership_date']
	dc_oship = sendData['dc_ownership']
	col_basicInfo.update({"retailer_po_no": str(po_no)}, {'$set' :{'dc_transfer_date':dc_o_date, 
																		'dc_ownership': dc_oship} })

def update_contractor_ownership(po_no, sendData):
	global col_basicInfo
	connect_DoorsOnline()
	c_o_date = sendData['contractor_ownership_date']
	c_o_ready = sendData['contractor_ownership_ready']
	col_basicInfo.update({"retailer_po_no": str(po_no)}, {'$set' :{
																		'contractor_ownership_date':c_o_date, 
																		'contractor_ownership_ready':c_o_ready
																		} })
	return

def getContractorInfo():
	global col_contractor
	connect_contractor_db()
	contractor_info = col_contractor.find({}, {'_id': False, 'contractor_name':1, 'account':1, 'emp_mobile_1':1, 'email_1':1})
	return contractor_info

def get_contractors_by_dc(dc):
	global col_con_dc
	connect_contractor_db()
	con_by_dc = col_con_dc.find({'dc_num': dc}, {'_id':False, 'account':1})
	return con_by_dc

def get_contractor_info(conName):
	global col_contractor
	connect_contractor_db()
	contractor_contact = col_contractor.find({"contractor_name":conName}, {'_id': False})
	return contractor_contact

def getDCInfoByPO(pNum):
	global col_dc_basic_info
	connect_retailer_db()
	dcInfo_po = col_dc_basic_info.find({}, {'_id': False})
	return dcInfo_po

def update_dc_info(po_no, dc_name, dc_id):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'door_center_id':dc_id, 'door_center_name':dc_name} })
	return

def update_contractor_info(po_no, contractor_id):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'contractor_id':contractor_id} })
	return

def save_status(manageStatus):
	global col_sChange
	global col_basicInfo
	connect_DoorsOnline()
	col_sChange.insert(manageStatus)
	po = manageStatus['po_number']
	status = manageStatus['status']
	status_id = manageStatus['status_id']
	status_desc = manageStatus['status_description']
	col_basicInfo.update({'retailer_po_no': str(po)}, {'$set': {
																'status': status, 
																'current_status_id': status_id, 
																'current_status_title':status,
																'current_status_desc':status_desc}})
	return

def get_all_status():
	global col_sChange
	connect_DoorsOnline()
	status = col_sChange.find({}, {'_id': False})	
	return status

def get_number(po_no):
	global col_basicInfo
	connect_DoorsOnline()
	num = col_basicInfo.find({'retailer_po_no' : str(po_no)}, {'_id': False, "consumer_primary_phone":1, "consumer_email":1})
	return num

def getStatus(po_no):
	global col_sChange
	connect_DoorsOnline()
	status = col_sChange.find({'po_number':str(po_no)}, {'_id': False})
	newStatus = []
	for s in status:
		newStatus.append(s)
	return newStatus

# login section
def search_authorization_by_id(id):
	global col_login
	connect_login_db()
	searched_data = col_login.find({'user_id':str(id)}, {'_id': False})
	return searched_data

def get_all_door():	
	global col_doorInfo
	connect_DoorsOnline()
	allDoors = col_doorInfo.find({}, {'_id': False})
	return allDoors

def saveNotes(notes):
	global col_changeLog
	connect_DoorsOnline()
	col_changeLog.insert(notes)
	return

def save_Notes(noteDetails):
	global col_note
	connect_DoorsOnline()
	col_note.insert(noteDetails)
	return

def get_log_byPO(pNum):
	global col_changeLog
	connect_DoorsOnline()
	logfile = col_changeLog.find({"retailer_po_no": str(pNum)}, {'_id': False})
	return logfile

def get_all_log():
	global col_changeLog
	connect_DoorsOnline()
	logfile = col_changeLog.find({}, {'_id': False})
	return logfile

def get_all_notes():
	global col_note
	connect_DoorsOnline()
	allNotes = col_note.find({}, {'_id': False})
	return allNotes

def get_notes(pNum):
	global col_note
	connect_DoorsOnline()
	notes = col_note.find({"retailer_po_no": str(pNum)}, {'_id': False})
	return notes


def save_doorsbasic_details(basic_info):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.insert(basic_info)
	return "saved Successfully in basic Info"

def save_doors_details(doors_info):
	global col_doorInfo
	connect_DoorsOnline()
	col_doorInfo.insert(doors_info)
	return "saved Successfully in Door Info"

def create_con_order_ap(con_order_ap):
	global col_contractor_acc_payable
	connect_DoorsOnline()
	col_contractor_acc_payable.insert(con_order_ap)
	return "saved Successfully in Door Info"

def get_basicinfo_details_paginated_all(pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	dc_info_count = col_basicInfo.count({"order_submitted": "Yes"})
	totalPages = (dc_info_count + nPerPage - 1) // nPerPage
	dcbasicinfo_from_db = col_basicInfo.find({"order_submitted": "Yes"}, {'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [dcbasicinfo_from_db, totalPages, nPerPage, dc_info_count]

def get_basicinfo_details_paginated(pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	dc_info_count = col_basicInfo.count({"order_submitted": "Yes"})
	totalPages = (dc_info_count + nPerPage - 1) // nPerPage
	dcbasicinfo_from_db = col_basicInfo.find({"order_submitted": "Yes"}, {'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [dcbasicinfo_from_db, totalPages, nPerPage, dc_info_count]

def get_basicInfo():
	global col_basicInfo
	connect_DoorsOnline()
	doorsonlineinfo_from_db = col_basicInfo.find({})
	return doorsonlineinfo_from_db

def get_one_order_basicInfo(o_id, pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	order_by_id_count = col_basicInfo.count({'$and': [{"order_submitted": "Yes"}, 
														{"retailer_po_no": str(o_id)}, {'_id':False}
														] })
	totalPages = (order_by_id_count + nPerPage - 1) // nPerPage
													
	orderData = col_basicInfo.find({'$and': [
											{"order_submitted": "Yes"}, 
											{"retailer_po_no": str(o_id)}
											] }, {'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [orderData, totalPages, nPerPage, order_by_id_count]

 

def get_one_order_by_po(o_id):
	global col_basicInfo
	connect_DoorsOnline()
	orderData = col_basicInfo.find({"retailer_po_no": str(o_id)}, {'_id': False})
	return orderData

def get_one_order_by_dc(dc, pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	order_by_dc_count = col_basicInfo.count({'$and': [
													{"order_submitted": "Yes"}, 
													{"door_center_id": str(dc)}
													] })
	totalPages = (order_by_dc_count + nPerPage - 1) // nPerPage
	orderData = col_basicInfo.find({'$and': [
											{"order_submitted": "Yes"}, 
											{"door_center_id": str(dc)}
											] }, 
											{'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [orderData, totalPages, nPerPage, order_by_dc_count]

def get_one_order_byStatus(status, pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	order_by_status_count = col_basicInfo.count({'$and': [
														{"order_submitted": "Yes"}, 
														{"overall_status": str(status)}
														] })
	totalPages = (order_by_status_count + nPerPage - 1) // nPerPage
	orderData = col_basicInfo.find({'$and': [
											{"order_submitted": "Yes"}, 
											{"overall_status": str(status)}
											]}, {'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [orderData, totalPages, nPerPage, order_by_status_count]

def get_order_by_diY_order(diy_fni_status, pageNum, recordsPerPage):
	global col_basicInfo
	connect_DoorsOnline()
	pagenum = pageNum
	nPerPage = recordsPerPage
	order_by_diy_status_count = col_basicInfo.count({'$and': [
														{"order_submitted": "Yes"}, 
														{"status": str(diy_fni_status)}
														] })
	totalPages = (order_by_diy_status_count + nPerPage - 1) // nPerPage
	orderData = col_basicInfo.find({'$and': [
											{"order_submitted": "Yes"}, 
											{"status": str(diy_fni_status)}
											]}, {'_id': False}).skip(pagenum*nPerPage).limit(nPerPage)
	return [orderData, totalPages, nPerPage, order_by_diy_status_count]




def get_one_door_info(pNum):	
	global col_doorInfo
	connect_DoorsOnline()
	doorInfo = col_doorInfo.find({"retailer_po_no": str(pNum)}, {'_id': False})
	return doorInfo

# get Retailer Info
def get_retailer_info(r_id):
	global col_retailer
	connect_retailer_db()
	retailerInfo = col_retailer.find({"account": str(r_id)}, {'_id': False})	
	return retailerInfo

def get_all_retailer_info():
	global col_retailer
	connect_retailer_db()
	all_retailers = col_retailer.find({}, {'_id': False, 'account':1, 'program_name':1})	
	return all_retailers

def update_order_status(po_no, basic_infos):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'status':basic_infos['Status']}})
	return

def update_one_record(po_no, basic_infos):
    global col_basicInfo
    connect_DoorsOnline()    
    col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'retailer_account':basic_infos['retailer_account'],
    															'company_name' :basic_infos["company_name"],
    															'consumer_firstname':basic_infos["consumer_firstname"],
    															'consumer_lastname':basic_infos["consumer_lastname"],
    															'consumer_email':basic_infos["consumer_email"],
    															'street_address':basic_infos["street_address"],
    															'country':basic_infos["country"],
    													        'state':basic_infos["state"],
    												     	    'city':basic_infos["city"],
    															'zip':basic_infos["zip"],
    															'consumer_primary_phone':basic_infos["consumer_primary_phone"],
    															'consumer_secondary_phone':basic_infos["consumer_secondary_phone"],
    															'special_instructions':basic_infos["special_instructions"],
    															'consumer_update_preference':basic_infos["consumer_update_preference"]} })
    return

def update_one_door_record(door_specID, doorsonlineRecords):
    global col_doorInfo
    door_info = doorsonlineRecords
    connect_DoorsOnline()    
    col_doorInfo.update_one({"door_spec_id": str(door_specID)}, 
    							{'$set' :{'door_type':door_info["door_type"],
										'door_model':door_info["door_model"],
										'door_width':door_info["door_width"],
										'door_height':door_info["door_height"],
										'door_quantity':door_info["door_quantity"],
										'door_unit_price':door_info['door_unit_price'],
										'door_extended_price':door_info["door_extended_price"],
										'color':door_info["color"],
										'color_unit_price':door_info["color_unit_price"],
										'color_ext_price':door_info["color_ext_price"],
										'windload':door_info["windload"],
										'stamp_design':door_info["stamp_design"],
										'spring_type':door_info["spring_type"],
										'additional_struts':door_info["additional_struts"],
										'additional_struts_quantity':door_info["additional_struts_quantity"],
										'additional_struts_unit_price':door_info["additional_struts_unit_price"],
										'additional_struts_extended_price':door_info["additional_struts_extended_price"],
										'glass_type':door_info["glass_type"],
										'glass_type_quantity':door_info["glass_type_quantity"],
										'glass_unit_price':door_info["glass_unit_price"],
										'glass_ext_price':door_info["glass_ext_price"],
										'glass_comments':door_info["glass_comments"],""
										'mosaic_glazing_instructions':door_info["mosaic_glazing_instructions"],
										'decra_trim':door_info["decra_trim"],
										'decra_trim_quantity':door_info["decra_trim_quantity"],
										'decra_trim_unit_price':door_info["decra_trim_unit_price"],
										'decra_trim_extended_price':door_info["decra_trim_extended_price"],
										'track_type':door_info["track_type"],
										'track_type_quantity':door_info["track_type_quantity"],
										'track_type_unit_price':door_info["track_type_unit_price"],
										'track_type_extended_price':door_info["track_type_extended_price"],
										'horizontal_radius':door_info["horizontal_radius"],
										'bracket_mount':door_info["bracket_mount"],
										'blue_ridge_handles':door_info["blue_ridge_handles"],
										'blue_ridge_handles_quantity':door_info["blue_ridge_handles_quantity"],
										'blue_ridge_handles_unit_price':door_info["blue_ridge_handles_unit_price"],
										'blue_ridge_handles_extended_price':door_info["blue_ridge_handles_extended_price"],
										'blue_ridge_hinges':door_info["blue_ridge_hinges"],
										'blue_ridge_hinges_quantity':door_info["blue_ridge_hinges_quantity"],
										'blue_ridge_hinges_unit_price':door_info["blue_ridge_hinges_unit_price"],
										'blue_ridge_hinges_extended_price':door_info["blue_ridge_hinges_extended_price"],
										'other_decorative_hardware':door_info["other_decorative_hardware"],
										'other_hardware_quantity':door_info["other_hardware_quantity"],
										'other_hardware_unit_price':door_info["other_hardware_unit_price"],
										'other_hardware_extended_price':door_info["other_hardware_extended_price"],
										'vinyl_t_stop':door_info["vinyl_t_stop"],
										'vinyl_t_stop_quantity':door_info["vinyl_t_stop_quantity"],
										'vinyl_t_stop_unit_price':door_info["vinyl_t_stop_unit_price"],
										'vinyl_t_stop_extended_price':door_info["vinyl_t_stop_extended_price"],
										'lock_type':door_info["lock_type"],
										'lock_type_quantity':door_info["lock_type_quantity"],
										'lock_type_unit_price':door_info["lock_type_unit_price"],
										'lock_type_extended_price':door_info["lock_type_extended_price"],
										'punched_angle':door_info["punched_angle"],
										'punched_angle_quantity':door_info["punched_angle_quantity"],
										'punched_angle_unit_price':door_info["punched_angle_unit_price"],
										'punched_angle_extended_price':door_info["punched_angle_extended_price"],
										'winding_bars':door_info["winding_bars"],
										'winding_bars_quantity':door_info["winding_bars_quantity"],
										'winding_bars_unit_price':door_info["winding_bars_unit_price"],
										'winding_bars_extended_price':door_info["winding_bars_extended_price"],
										'other_door_accessories':door_info["other_door_accessories"],
										'other_door_accessories_quantity':door_info["other_door_accessories_quantity"],
										'other_door_accessories_unit_price':door_info["other_door_accessories_unit_price"],
										'other_door_accessories_extended_price':door_info["other_door_accessories_extended_price"],
										'opener_model':door_info["opener_model"],
										'opener_model_quantity':door_info["opener_model_quantity"],
										'opener_model_unit_price':door_info["opener_model_unit_price"],
										'opener_model_extended_price':door_info["opener_model_extended_price"],
										'opener_accessories':door_info["opener_accessories"],
										'opener_accessories_quantity':door_info["opener_accessories_quantity"],
										'opener_accessories_unit_price':door_info["opener_accessories_unit_price"],
										'opener_accessories_extended_price':door_info["opener_accessories_extended_price"],
										'operator_bracket':door_info["operator_bracket"],
										'operator_bracket_quantity':door_info["operator_bracket_quantity"],
										'operator_bracket_unit_price':door_info["operator_bracket_unit_price"],
										'operator_bracket_extended_price':door_info["operator_bracket_extended_price"],
										'other_opener_accessories':door_info["other_opener_accessories"],
										'other_opener_accessories_quantity':door_info["other_opener_accessories_quantity"],
										'other_opener_accessories_unit_price':door_info["other_opener_accessories_unit_price"],
										'other_opener_accessories_extended_price':door_info["other_opener_accessories_extended_price"],
										'additional_part1':door_info["additional_part1"],
										'part1_qty':door_info["part1_qty"],
										'part1_u_price':door_info["part1_u_price"],
										'part1_e_price':door_info["part1_e_price"],
										'additional_part2':door_info["additional_part2"],
										'part2_qty':door_info["part2_qty"],
										'part2_u_price':door_info["part2_u_price"],
										'part2_e_price':door_info["part2_e_price"],
										'additional_part3':door_info["additional_part3"],
										'part3_qty':door_info["part3_qty"],
										'part3_u_price':door_info["part3_u_price"],
										'part3_e_price':door_info["part3_e_price"],
										'additional_part4':door_info["additional_part4"],
										'part4_qty':door_info["part4_qty"],
										'part4_u_price':door_info["part4_u_price"],
										'part4_e_price':door_info["part4_e_price"],
										'additional_part5':door_info["additional_part5"],
										'part5_qty':door_info["part5_qty"],
										'part5_u_price':door_info["part5_u_price"],
										'part5_e_price':door_info["part5_e_price"],
										'labor_service1':door_info["labor_service1"],
										'labor_service1_quantity':door_info["labor_service1_quantity"],
										'labor_service1_unit_price':door_info["labor_service1_unit_price"],
										'labor_service1_extended_price':door_info["labor_service1_extended_price"],
										'labor_service2':door_info["labor_service2"],
										'labor_service2_quantity':door_info["labor_service2_quantity"],
										'labor_service2_unit_price':door_info["labor_service2_unit_price"],
										'labor_service2_extended_price':door_info["labor_service2_extended_price"],
										'labor_service3':door_info["labor_service3"],
										'labor_service3_quantity':door_info["labor_service3_quantity"],
										'labor_service3_unit_price':door_info["labor_service3_unit_price"],
										'labor_service3_extended_price':door_info["labor_service3_extended_price"],
										'labor_service4':door_info["labor_service4"],
										'labor_service4_quantity':door_info["labor_service4_quantity"],
										'labor_service4_unit_price':door_info["labor_service4_unit_price"],
										'labor_service4_extended_price':door_info["labor_service4_extended_price"],
										'labor_service5':door_info["labor_service5"],
										'labor_service5_quantity':door_info["labor_service5_quantity"],
										'labor_service5_unit_price':door_info["labor_service5_unit_price"],
										'labor_service5_extended_price':door_info["labor_service5_extended_price"],
										'labor_service6':door_info["labor_service6"],
										'labor_service6_quantity':door_info["labor_service6_quantity"],
										'labor_service6_unit_price':door_info["labor_service6_unit_price"],
										'labor_service6_extended_price':door_info["labor_service6_extended_price"],
										'labor_service7':door_info["labor_service7"],
										'labor_service7_quantity':door_info["labor_service7_quantity"],
										'labor_service7_unit_price':door_info["labor_service7_unit_price"],
										'labor_service7_extended_price':door_info["labor_service7_extended_price"],
										'labor_service8':door_info["labor_service8"],
										'labor_service8_quantity':door_info["labor_service8_quantity"],
										'labor_service8_unit_price':door_info["labor_service8_unit_price"],
										'labor_service8_extended_price':door_info["labor_service8_extended_price"],
										'labor_service9':door_info["labor_service9"],
										'labor_service9_quantity':door_info["labor_service9_quantity"],
										'labor_service9_unit_price':door_info["labor_service9_unit_price"],
										'labor_service9_extended_price':door_info["labor_service9_extended_price"],
										'labor_service10':door_info["labor_service10"],
										'labor_service10_quantity':door_info["labor_service10_quantity"],
										'labor_service10_unit_price':door_info["labor_service10_unit_price"],
										'labor_service10_extended_price':door_info["labor_service10_extended_price"],
										'request_drawing':door_info["request_drawing"],
										'sub_total_material_cost':door_info["sub_total_material_cost"],
										'sub_total_labor_cost':door_info["sub_total_labor_cost"],
										'shipping_cost':door_info["shipping_cost"],
										'total':door_info["total"]} })													
    return

def save_shipping_pickup(po_no, addShppingPickup):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'shipping_pickup_info':addShppingPickup} })
	return

def get_one_door_info_for_duplicate(doorSpec_id):
	global col_doorInfo
	connect_DoorsOnline()
	door_records = col_doorInfo.find({"door_spec_id": str(doorSpec_id)}, {'_id': False})
	return door_records

def save_duplicate_doors_details(door_infos_list):
	global col_doorInfo
	connect_DoorsOnline()
	col_doorInfo.insert(door_infos_list)
	return "Duplicate door details saved successfully"

def delete_a_door(ds_id):
	global col_doorInfo
	connect_DoorsOnline()
	col_doorInfo.remove({"door_spec_id": str(ds_id)})
	return "Door Deleted Successfully"

def update_orderSubmitted_data(po_no, basic_infos):
	global col_basicInfo
	connect_DoorsOnline()
	asc_o_p_date = basic_infos['asc_order_processing_date']
	asc_o_p_by = basic_infos['asc_order_processing_by']
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'status':basic_infos['status'],
																		'asc_order_processing_date': asc_o_p_date, 
																		'asc_order_processing_by': asc_o_p_by} })
	return

def update_overall_status(po_no, basic_infos):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'overall_status':basic_infos['overall_status']} })
	return

def update_orderPlaced_data(po_no, basic_infos):
    global col_basicInfo
    connect_DoorsOnline()    
    col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'order_submitted':basic_infos['order_submitted'],
    															'order_submitted_date':basic_infos['order_submitted_date'],
    															'status':basic_infos['status']} })
    return


# def save_ap_labor_rates(po_no, basic_infos):
#     global col_basicInfo
#     connect_DoorsOnline()    
#     col_basicInfo.update_one({"retailer_po_no": str(po_no)}, {'$set' :{'order_submitted':basic_infos['order_submitted'],
#     															'order_submitted_date':basic_infos['order_submitted_date'],
#     															'status':basic_infos['status']} })
#     return


def check_password(email):
	global col_login
	connect_login_db()
	searched_data = col_login.find({'user_id':str(email)}, {'_id': False})
	return searched_data 

def update_one_password(email, check):
	global col_login
	connect_login_db()
	col_login.update_one({"user_id": str(email)}, {'$set' :{'password':check['password']} })
	return

def update_totalOrder(pNum, totalOrder):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update_one({"retailer_po_no": str(pNum)}, {'$set' :{'total_order':totalOrder}})
	return


# *******************Labor Rates**********************************

def get_labor_rate_fields():
	global col_lab_field
	connect_labor_rate_fields()
	labor_rate_fields = col_lab_field.find({}, {'_id': False})
	return labor_rate_fields

def save_labor_rate_fields(rates_dict):
	global col_labor_rate
	connect_DoorsOnline()
	col_labor_rate.insert(rates_dict)
	return "Labor rate fields generated"

def get_labor_rate_infos(con_id):
	global col_labor_rate_contractor
	connect_contractor_db()
	labor_rates = col_labor_rate_contractor.find({'contractor_id': str(con_id)}, {'_id': False, 'contractor_id':0})
	return labor_rates

def get_all_labor_rates(conId):
	global col_labor_rate
	connect_DoorsOnline()
	all_labor_rate = col_labor_rate.find({'contractor_id': str(conId)}, {'_id': False, 'contractor_id':0, 'retailer_po_no':0})
	return all_labor_rate

def check_rate(conId, p_num):
	global col_labor_rate
	connect_DoorsOnline()
	all_rates = col_labor_rate.find({'$and': [{"contractor_id":conId},{"retailer_po_no": str(p_num)}]}
									, {'_id': False, 'contractor_id':0, 'retailer_po_no':0})
	all_special_rates = col_special_rate_history.find({'$and': [{"contractor_id":conId}, {"retailer_po_no": str(p_num)} ]}, {'_id': False})
	return [all_rates, all_special_rates]

def save_special_rate_history(special_rate_history):
	global col_special_rate_history
	connect_DoorsOnline()
	col_special_rate_history.insert(special_rate_history)
	return

def update_special_rate(conId, p_num, ids, rate):
	global col_labor_rate
	connect_DoorsOnline()
	col_labor_rate.update_one({'$and': [{"contractor_id":conId},{"retailer_po_no": str(p_num)}]},
									{'$set' :{ids: rate}})
	return


def get_labor_rates(state_name_sname):
	global col_labor_rate_ret
	connect_retailer_db()
	labor_rates = col_labor_rate_ret.find({"State":str(state_name_sname)}, {'_id':False, 'Country': 0})
	return labor_rates

def get_labor_rate_details():
	global col_lab_desc
	connect_labor_rate_fields()
	lr_details = col_lab_desc.find({}, {"_id":False})
	return lr_details


def get_all_collections(po_no):	
	global col_doorInfo
	connect_DoorsOnline()
	all_doors = col_doorInfo.find({"retailer_po_no": str(po_no)}, {'_id':0})
	return all_doors

def get_all_collections_labor_rates(po_no):	
	global col_doorInfo
	connect_DoorsOnline()
	all_doors = col_doorInfo.find({"retailer_po_no": str(po_no)}, {'_id':0, 'door_spec_id':1, 'retailer_po_no':1, 'labor_service1':1, 'labor_service1_quantity':1,
		'labor_service1_unit_price':1,'labor_service1_extended_price':1, 'labor_service2':1, 'labor_service2_quantity':1,
		'labor_service2_unit_price':1, 'labor_service2_extended_price':1, 'labor_service3':1, 'labor_service3_quantity':1, 
		'labor_service3_unit_price':1, 'labor_service3_extended_price':1, 'labor_service4':1, 'labor_service4_quantity':1, 
		'labor_service4_unit_price':1, 'labor_service4_extended_price':1, 'labor_service5':1, 'labor_service5_quantity':1,
		'labor_service5_unit_price':1, 'labor_service5_extended_price':1, 'labor_service6':1, 'labor_service6_quantity':1, 
		'labor_service6_unit_price':1, 'labor_service6_extended_price':1, 'labor_service7':1, 'labor_service7_quantity':1, 
		'labor_service7_unit_price':1, 'labor_service7_extended_price':1, 'labor_service8':1, 'labor_service8_quantity':1, 
		'labor_service8_unit_price':1, 'labor_service8_extended_price':1, 'labor_service9':1, 'labor_service9_quantity':1, 
		'labor_service9_unit_price':1, 'labor_service9_extended_price':1, 'labor_service10':1, 'labor_service10_quantity':1,
		'labor_service10_unit_price':1, 'labor_service10_extended_price':1})
	return all_doors

# --------------------------------------------------------------------
def get_basic_details():
	global col_contractor
	connect_contractor_db()
	installerinfo_from_db = col_contractor.find({'deactivated':False})
	return installerinfo_from_db


def get_tech_accN(account_no):
	global col_technician
	connect_contractor_db()
	tech_data_from_db = col_technician.find({"account": str(account_no)},{"_id":0})
	return tech_data_from_db


# ---------------------------------------------------------------------  
def get_dcbasicinfo_details():
	global col_dc
	connect_dc_db()
	dcbasicinfo_from_db = col_dc.find({'deactivated' : False},{"_id":0})
	return dcbasicinfo_from_db



# ---------------------------------------------------------------------  
def get_retailerInfo():
	global col_retailer
	connect_retailer_db()
	retailerInfo_fromDB = col_retailer.find({},{"_id":0})
	return retailerInfo_fromDB


def get_labor_rate_id():
	global col_lab_desc
	connect_labor_rate_fields()
	labor_rate_id = col_lab_desc.find({}, {'_id':False, 'retail_labor_id_name':1, 'retail_labor_service':1})
	return labor_rate_id


# ------------------------------------------------------------------------
def get_acc_payable_fields(po_no):
	global col_contractor_acc_payable
	connect_DoorsOnline()
	labor_rate_fields = col_contractor_acc_payable.find({"retailer_po_no": str(po_no)}, {'_id':0})
	return labor_rate_fields



# -------------------------------------------Update Contractor Order Account Payable
def update_con_order_ap(labor_rates_list, door_id, po_num):
	global col_contractor_acc_payable
	connect_DoorsOnline()
	col_contractor_acc_payable.update_one({'$and': [{"door_spec_id":door_id}, {"retailer_po_no": str(po_num)}]},
											{'$set' :{'labortype1_name': labor_rates_list[0]['labor_service_type1'],
													'labortype1_qty': labor_rates_list[0]['qty1'],
													'labortype1_rate_type': labor_rates_list[0]['rate_type1'],
													'labortype1_unit_price': labor_rates_list[0]['unit_price1'],
													'labortype1_ext_price': labor_rates_list[0]['ext_price1'],
													'labortype2_name': labor_rates_list[0]['labor_service_type2'],
													'labortype2_qty': labor_rates_list[0]['qty2'],
													'labortype2_rate_type': labor_rates_list[0]['rate_type2'],
													'labortype2_unit_price': labor_rates_list[0]['unit_price2'],
													'labortype2_ext_price': labor_rates_list[0]['ext_price2'],

													'labortype3_name': labor_rates_list[0]['labor_service_type3'],
													'labortype3_qty' : labor_rates_list[0]['qty3'],
													'labortype3_rate_type' :labor_rates_list[0]['rate_type3'],
													'labortype3_unit_price' :labor_rates_list[0]['unit_price3'],
													'labortype3_ext_price' :labor_rates_list[0]['ext_price3'],
													'labortype4_name' :labor_rates_list[0]['labor_service_type4'],
													'labortype4_qty' :labor_rates_list[0]['qty4'],
													'labortype4_rate_type' :labor_rates_list[0]['rate_type4'],
													'labortype4_unit_price' :labor_rates_list[0]['unit_price4'],
													'labortype4_ext_price' :labor_rates_list[0]['ext_price4'],

													'labortype5_name' :labor_rates_list[0]['labor_service_type5'],
													'labortype5_qty' :labor_rates_list[0]['qty5'],
													'labortype5_rate_type' :labor_rates_list[0]['rate_type5'],
													'labortype5_unit_price' :labor_rates_list[0]['unit_price5'],
													'labortype5_ext_price' :labor_rates_list[0]['ext_price5'],
													'labortype6_name' :labor_rates_list[0]['labor_service_type6'],
													'labortype6_qty' :labor_rates_list[0]['qty6'],
													'labortype6_rate_type' :labor_rates_list[0]['rate_type6'],
													'labortype6_unit_price' :labor_rates_list[0]['unit_price6'],
													'labortype6_ext_price' :labor_rates_list[0]['ext_price6'],

													'labortype7_name' :labor_rates_list[0]['labor_service_type7'],
													'labortype7_qty' :labor_rates_list[0]['qty7'],
													'labortype7_rate_type' :labor_rates_list[0]['rate_type7'],
													'labortype7_unit_price' :labor_rates_list[0]['unit_price7'],
													'labortype7_ext_price' :labor_rates_list[0]['ext_price7'],
													'labortype8_name' :labor_rates_list[0]['labor_service_type8'],
													'labortype8_qty' :labor_rates_list[0]['qty8'],
													'labortype8_rate_type' :labor_rates_list[0]['rate_type8'],
													'labortype8_unit_price' :labor_rates_list[0]['unit_price8'],
													'labortype8_ext_price' :labor_rates_list[0]['ext_price8'],

													'labortype9_name' :labor_rates_list[0]['labor_service_type9'],
													'labortype9_qty' :labor_rates_list[0]['qty9'],
													'labortype9_rate_type' :labor_rates_list[0]['rate_type9'],
													'labortype9_unit_price' :labor_rates_list[0]['unit_price9'],
													'labortype9_ext_price' :labor_rates_list[0]['ext_price9'],
													'labortype10_name' :labor_rates_list[0]['labor_service_type10'],
													'labortype10_qty' :labor_rates_list[0]['qty10'],
													'labortype10_rate_type' :labor_rates_list[0]['rate_type10'],
													'labortype10_unit_price' :labor_rates_list[0]['unit_price10'],
													'labortype10_ext_price' :labor_rates_list[0]['ext_price10'],
													}})
	return 

# account payable updated rates (Summary page)
def get_updated_labor_rates(po_no):
	global col_contractor_acc_payable
	connect_DoorsOnline()
	updated_labor_rates = col_contractor_acc_payable.find({'retailer_po_no': str(po_no)}, {'_id':0})
	return updated_labor_rates


# status according to order type
def get_diy_status(order_type):
	global col_diy
	global col_fni
	connect_status_db()
	if order_type == 'DIY':
		status_cur = col_diy.find({}, {'_id':0})
	elif order_type == 'F&I':
		status_cur = col_fni.find({}, {'_id':0})
	return status_cur

def get_diy_status_list():
	global col_diy
	connect_status_db()	
	status_diy = col_diy.find({}, {'_id':0})
	return status_diy

def get_fni_status_list():
	global col_fni
	connect_status_db()	
	status_fni = col_fni.find({}, {'_id':0})
	return status_fni


def get_all_records_by_con(retailer_id, con_id):
	global col_allRtailer
	print('--------------------retailer id' + str(retailer_id))
	connect_allRetailer_basic_info(retailer_id)
	orders_by_con = col_allRtailer.find({'contractor_id': str(con_id)}, {'_id':0})
	orders_count = col_allRtailer.count({'contractor_id': str(con_id)})
	return [orders_by_con, orders_count]

def get_all_records_by_dc(retailer_id, dc_id):
	global col_allRtailer
	print('--------------------retailer id' + str(retailer_id))
	connect_allRetailer_basic_info(retailer_id)
	orders_by_dc = col_allRtailer.find({'door_center_id': str(dc_id)}, {'_id':0})
	orders_count = col_allRtailer.count({'door_center_id': str(dc_id)})
	return [orders_by_dc, orders_count]

def update_est_date(po_no, e_date):
	global col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update({'retailer_po_no': str(po_no)}, {'$set' :{'estimated_date': e_date}})
	return

def update_material_availability(po_no, mat_ready_info):
	global  col_basicInfo
	connect_DoorsOnline()
	col_basicInfo.update({'retailer_po_no' : str(po_no)},
							{'$set':{'dc_material_available_date': mat_ready_info['dc_material_available_date'], 
									'dc_material_submitted_by' :mat_ready_info['dc_material_submitted_by'],
									
									}})
	return
