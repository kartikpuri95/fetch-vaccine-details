import json
import requests
from datetime import date,timedelta,datetime
import boto3
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os

total_dates=[]
today=date.today().strftime("%d-%m-%Y")
base = datetime.today()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'} # This is chrome, you can set whatever browser you like
cc_addresses=[{'email':'sample@gmail.com'}] ## List of all the people you want to send the email

to_addresses=[{'email':'sample@gmail.com'}]
district_id=392 ## this is the district id, make sure to replace it, check readme to how to find district id
## I am checking this for next 5 days
## And sending all the infortion for all the 5 days today to next 5
for x in range(0,5):
    new_date=base + timedelta(days=x)
    total_dates.append(new_date.strftime("%d-%m-%Y"))
def contains_word(s, w):
    return (' ' + w + ' ') in (' ' + s + ' ')
def sendInBlueEmail(params):
    configuration = sib_api_v3_sdk.Configuration()

    configuration.api_key['api-key'] =os.environ.get("SEND_IN_BLUE") ## Either pass your key directly here or add in the aws console of lambda function
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    subject = "from the Python SDK!"
    sender = {"name":"sample","email":"sample@gmail.com"}
    replyTo = {"name":"sample","email":"sample@gmail.com"}
    html_content = "<html><body><h1>Find Vaccine Availability in navi mumbai </h1></body></html>"
    to = to_addresses
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(bcc=cc_addresses,to=to_addresses, reply_to=replyTo, template_id=1, sender=sender, subject=subject,params=params)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
   
def handler(event, context):
    final_list={}
    final_list['hospital']=[]
    for date_obj in total_dates:
        hospital_center={}
        hospital_center['date']=date_obj
        hospital_center['hospitals']=[] 
        r =requests.get(f'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id=392&date={date_obj}',headers=headers)
        if r.status_code==200:
            print('Inside status code')
            json_response=r.json()
            centers=json_response['centers']
            for center in centers:
                address=center['address']
                #In below line i have filtered out all the hospital have address as NAVI MUMBAI
                if contains_word(address, 'Navi Mumbai') or  contains_word(address, 'NAVI MUMBAI'):
                    temp_dict={}
                    temp_dict['name']=center['name']
                    temp_dict['is_vaccine_available']='No'
                    temp_dict['address']=center['address']
                    temp_dict['fee_type']=center['fee_type']
                    temp_dict['vaccine_status']=[]
                    for ses in center['sessions']:
                        new_dict={}
                        new_dict['available_capacity']=ses['available_capacity']
                        if ses['available_capacity']>0:
                            temp_dict['is_vaccine_available']='Yes'
                        new_dict['for_age_group']=ses['min_age_limit']
                        new_dict['vaccine_name']=ses['vaccine']
                        new_dict['slots']=ses['slots']
                        temp_dict['vaccine_status'].append(new_dict)
                    hospital_center['hospitals'].append(temp_dict)
            final_list['hospital'].append(hospital_center)       
    sendInBlueEmail(final_list)
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps('Hello from your new Amplify Python lambda!')
    }