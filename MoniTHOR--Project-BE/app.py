from flask import Flask,request, jsonify
from pythonBE import user , check_liveness ,domain
from logger.logs import logger
import json
import os
from datetime import datetime 
from flask_cors import CORS
from logger.utils  import Utils
from elasticapm.contrib.flask import ElasticAPM
import logging
from elasticapm import traces, capture_span
utils = Utils()
import elasticapm
# Set up APM debugging
logging.getLogger('elasticapm').setLevel(logging.DEBUG)

app = Flask(__name__)  # __name__ helps Flask locate resources and configurations

# app.config['ELASTIC_APM'] = {
#   'SERVICE_NAME': 'Monothor-be',
#   'API_KEY': 'RmY0Q0NaVUJLaTZSRzdmcEpuU0c6REhuQnp4M3poRDZHSHZlRGxHdHo5Zw==',
#   'SERVER_URL': 'https://my-observability-project-bbb56a.apm.us-west-2.aws.elastic.cloud:443',
#   'ENVIRONMENT': 'Test',
#   'TRANSACTIONS_SAMPLE_RATE': 1.0,
#   'DEBUG': True,
# }

client = elasticapm.Client(
    service_name='Monothor-be-test',
    server_url = 'https://my-observability-project-bbb56a.apm.us-west-2.aws.elastic.cloud:443',
    api_key = 'RmY0Q0NaVUJLaTZSRzdmcEpuU0c6REhuQnp4M3poRDZHSHZlRGxHdHo5Zw==',
    environment = 'Test',
    transactions_sample_rate = 1.0,
    debug = True
)

client.capture_message("Starting Monothor-be-test")
client.begin_transaction("Starting Monothor-be-test")
import time
time.sleep(1)
client.end_transaction("Starting Monothor-be-test", "success")

# apm = ElasticAPM(app, logging=True)


CORS(app)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    app.config.update(config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global parmeters to keep last job info.
global globalInfo 
globalInfo = {'runInfo': ('--/--/---- --:--', '-')} 


# Route for BE login  
@app.route('/BElogin', methods=['POST'])
@utils.measure_this
def BElogin():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        logger.debug(f"Attempt to login with - User: {username}, Pass: {password}")
        
        status = user.login_user(username, password)
        if status['message'] == "Login Successful":
            
            
            logger.info(f"User: {username} Login Successful")
            return jsonify({"message": "Login Successful"})
        else:
            logger.info(f"User: {username} Login Failed")
            return jsonify({"message": "Invalid username or password!"}), 401
    return jsonify({"message": "Bad Request"}), 400



@app.route('/BElogin_lc', methods=['GET'])
@utils.measure_this
def BElogin_lc():   
    
    username = 'locust'# data.get('username')
    password = 'locust'# data.get('password')
        
    logger.debug(f"Attempt to login with - User: {username}, Pass: {password}")        
    status = user.login_user(username, password)
    if status['message'] == "Login Successful":                      
        logger.info(f"User: {username} Login Successful")
        return jsonify({"message": "Login Successful"})
    else:
        logger.info(f"User: {username} Login Failed")
        return jsonify({"message": "Invalid username or password!"}), 401
    


@app.route('/BEresults/<username>', methods=['GET'])
@utils.measure_this
def BEresults(username):
    if user.is_user_exist(username)['message']!="User exist" :        
        return "No User is logged in" 
    
    user_file = f'./userdata/{username}_domains.json'
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            data = json.load(f)
    else:
        data = []

    all_domains = [item['domain'] for item in data]
    latest_results = data[:6]
    failuresCount = sum(1 for item in data if item.get('status_code') == 'FAILED')
    
    failuresPrecent = round(float(failuresCount) / len(all_domains) * 100, 1) if len(all_domains) > 0 else 0
    lastRunInfo = f"{globalInfo['runInfo'][0]}, {globalInfo['runInfo'][1]} Domains, {failuresPrecent}% failures"

    response = {
        'user': username,
        'data': data,
        'all_domains': all_domains,
        'latest_results': latest_results,
        'last_run': lastRunInfo
    }
    
    return jsonify(response)
    


@app.route('/BEregister', methods=['POST','GET'])
@utils.measure_this
def BEregister():
    
    data = request.get_json()
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')   

    # Validate input parameters
    if not username or not password1 or not password2:
        return jsonify({"error": "All fields are required"}), 400
    if password1 != password2:
        return jsonify({"error": "Passwords do not match"}), 400

    # Process registration
    status = user.register_user(username, password1, password2)

    if status['message'] == 'Username already taken':
        return jsonify({"error": "Username already taken"}), 409
    if status['message'] == 'Registered successfully':
        return jsonify({"message": "Registered successfully"}), 201
    
    return jsonify({"error": "Registration failed"}), 500
   


@app.route('/submit', methods=['POST'])
@utils.measure_this
def submit_data():
    data = request.get_json()  # Parse JSON payload
    return {"received": data}, 200



# Route to add a single domain 
@app.route('/BEadd_domain/<domainName>/<username>',methods=['GET', 'POST'])
@utils.measure_this
def BEadd_new_domain(domainName,username):
    logger.debug(f'New domain is added {domainName}')    
    if user.is_user_exist(username)['message']!="User exist" :        
        return "User is not exist" 
    # Get the domain name from the form data
    logger.debug(f'Domain name is {domainName}')
        
    return domain.add_domain(username,domainName)   


# Route to add a single domain 
@app.route('/',methods=['GET', 'POST'])
@utils.measure_this
def BEadd_new_domain_lc():
        
    return domain.add_domain('dddd','google.com') 
    
# Route to remove a single domain 
@app.route('/BEremove_domain/<domainName>/<username>', methods=['GET', 'POST'])
@utils.measure_this
def remove_domain(domainName,username):
    if user.is_user_exist(username)['message']!="User exist" :
        return "User does not exist" 
    logger.debug(f'Remove domain being called to domain: {domainName}')
    
    logger.debug(f'Domain name is {domainName}')    
    response = domain.remove_domain(username, domainName)

    if response['message'] == "Domain successfully removed":               
        return response       
    return "Error: Domain could not be removed"
   

@app.route('/BEbulk_upload/<filename>/<username>')
@utils.measure_this
def add_from_file(filename,username, apm_context=None):    
    traces.execution_context.set_transaction(apm_context)
    with capture_span("add_from_file", "add_from_file", {"username": username}):
        if user.is_user_exist(username)['message']!="User exist" :
            return "User does not exist" 

            
        logger.info(f"File for bulk upload:{filename}")
        return domain.add_bulk(username,filename)
    
    
# Route to run Livness check 
# @function.measure_this()

@app.route('/BEcheck')
@utils.measure_this
def check_livness():
    client.begin_transaction("check_livness_transaction")    
    apm_context = traces.execution_context.get_transaction()
    data = request.get_json()
    username = data.get('username')
    if user.is_user_exist(username)['message']!="User exist" :
       return "User does not exist"             
    runInfo=check_liveness.livness_check (username, apm_context, client=client)            
    client.end_transaction("check_livness_transaction", "success")
    return runInfo
    

def asd_span_function(apm_context=None):
    traces.execution_context.set_transaction(apm_context)
    with capture_span("asd_span", "asd_span", {"username": "asd"}):
        time.sleep(2)
        return "asd"


@app.route('/asd', methods=['GET'])    
def asd():
    client.begin_transaction("asd_transaction")
    asd_span_function(apm_context=traces.execution_context.get_transaction())
    client.end_transaction("asd_transaction", "success")
    return "asd", 200
    


@app.route('/BEupload', methods=['POST'])
@utils.measure_this
def upload_file():
    client.begin_transaction("file_upload_transaction")    
    apm_context = traces.execution_context.get_transaction()

    if 'file' not in request.files:
        logger.error("No file")
        client.end_transaction("file_upload_transaction", "error")
        return {'error': 'No file part provided'}, 400
    
    username = request.form.get('user')
    if not username:
        client.end_transaction("file_upload_transaction", "error")
        return {'error': 'No username provided'}, 400
    
    file = request.files['file']
    if file.filename == '':
        client.end_transaction("file_upload_transaction", "error")
        return {'error': 'No selected file'}, 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    try:
        file.save(filepath)
        add_from_file(filepath, username, apm_context)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        client.end_transaction("file_upload_transaction", "success")
        return {'message': 'File successfully uploaded', 'file': filepath}
    
    except Exception as e:
        logger.error("Error:", e)
        client.end_transaction("file_upload_transaction", "error")
        return {'error': 'An error occurred during file upload'}, 500


def Checkjob(username):    
    globalInfo["runInfo"]=check_liveness.livness_check (username)    
    return  globalInfo["runInfo"]

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['BE_PORT'], debug=app.config['FLASK_DEBUG'])
    
