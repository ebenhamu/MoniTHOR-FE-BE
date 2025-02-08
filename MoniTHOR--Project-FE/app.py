from flask import Flask, session, render_template,redirect,request, url_for , jsonify
import requests 
from oauthlib.oauth2 import WebApplicationClient
from logger.logs import logger
import json
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz
import uuid
from datetime import datetime 
import socket

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# __name__ helps Flask locate resources and configurations
app = Flask(__name__)  

# Load environment variables from .env file
if os.path.exists('.env'):
    load_dotenv()
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
    app.secret_key = os.getenv('FLASK_SECRET_KEY')    
else:
    GOOGLE_CLIENT_ID = 'NO_ENV_FILE_KEY'
    app.secret_key = 'NO_ENV_FILE_KEY'
    GOOGLE_CLIENT_SECRET = 'NO_ENV_FILE_KEY'
    GOOGLE_DISCOVERY_URL = 'NO_ENV_FILE_KEY'    

# Load configuration from JSON file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    app.config.update(config)


if app.config['BE_SERVER'] == 'localhost' or app.config['BE_SERVER'] == '127.0.0.1'  :       
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        app.config["BE_SERVER"]=local_ip
        logger.info(f'BE server IP : {app.config['BE_SERVER']}')

# Global parmeters to keep last job info.
global globalInfo 
globalInfo = {'runInfo': ('--/--/---- --:-- ')} 

# Google OAuth2 details
# Initialize OAuth2 client
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()
scheduled_jobs = [] # Store scheduled jobs

# Route for Job schedule 
@app.route('/schedule_bulk_monitoring', methods=['POST'])
def schedule_bulk_monitoring():
    # Get form data    
    schedule_date = request.form['schedule_date']
    schedule_time = request.form['schedule_time']
    timezone = request.form['timezone']
    interval = request.form.get('interval')
    user = session['user']    
    schedule_date_time=f"{schedule_date} {schedule_time}"
    # Convert time to UTC
    local_tz = pytz.timezone(timezone)
    local_time = local_tz.localize(datetime.fromisoformat(schedule_date_time))
    utc_time = local_time.astimezone(pytz.utc)

    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    if interval:
        # Schedule a recurring job
        scheduler.add_job(Checkjob,trigger='interval',hours=int(interval),args=[user],id=job_id,start_date=utc_time)
    else:
        # Schedule a one-time job
        scheduler.add_job(Checkjob,trigger=DateTrigger(run_date=utc_time),args=[user],id=job_id)
    
    # Save job info
    scheduled_jobs.append({'id': job_id,'user': user,'time': schedule_time,'timezone': timezone,'interval': interval})    

    return {'message': 'Monitoring scheduled successfully!'}

# Route for job cancel 
@app.route('/cancel_job/<job_id>', methods=['POST'])
def cancel_job(job_id):
    scheduler.remove_job(job_id)
    global scheduled_jobs
    scheduled_jobs = [job for job in scheduled_jobs if job['id'] != job_id]
    return {'message': 'Job canceled successfully!'}

#Route for Google Authentication
@app.route('/google-login')
def google_login():
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    # Generate the authorization URL
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url_for('google_callback', _external=True),
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

# Route For Google Callback
@app.route('/callback')
def google_callback():
    # Get the authorization code Google sent back
    code = request.args.get("code")

    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare token request
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=url_for('google_callback', _external=True),
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get user info
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # Extract user info
    userinfo = userinfo_response.json()
    if userinfo.get("email_verified"):
        google_user = {
            "username": userinfo["email"]
        }
        logger.info(f'{userinfo["email"]} Login With Google Account')       

        # URL of the BEregister endpoint
        url=f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEregister'

        # Data to be sent in the request
        data = {
            'username': google_user["username"],
            'password1': 'google_login',
            'password2': 'google_login'
        }

        # Headers for the request
        headers = {
            'Content-Type': 'application/json'
        }

        try:
        # Make a POST request to the BEregister endpoint
            response = requests.post(url, headers=headers, data=json.dumps(data))
    
        # Check the response status code
            if response.status_code == 201:
                logger.info(f'Registration successful:{google_user["username"]}')
            elif response.status_code == 409:
                logger.info(f'Info: Username  {google_user["username"]} already registered:')
            else:
                logger.error('Error:', response.json())

        except Exception as e:
            logger.error('An error occurred:', str(e))

        # Log the user in and redirect to the dashboard
        session['user'] = google_user["username"]
        return redirect(url_for("main"))
    else:
        return "User email not available or not verified by Google."
    



# Route for login page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    
    return render_template('login.html' ,beserver_ip=app.config['BE_SERVER'])


# update user in session
@app.route('/update_user', methods=['POST'])
def update_user_details():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')                        
        session['user'] = username
        globalInfo['runInfo'] = ['--/--/---- --:-- ']
        logger.info(f"User: {username} Login Successful")             
        return "Session user udpated"


# Route for Dashboard  
@app.route('/dashboard', methods=['GET'])
def main():
    try:        
        username=session['user']    
    except:        
        return render_template('login.html')
    username=session['user'] 

    data = [] 

    # Extract the required parts for the forms
    all_domains = [item['domain'] for item in data]  # List of domain names
    latest_results = data[:6]  # Last 6 results
    
    failuresCount = sum(1 for item in data if item.get('status_code') == 'FAILED' )    
    if len(all_domains)>0 :
        failuresPrecent=  round (float(float(failuresCount)/float(len(all_domains)))*100,1)
    else:
        failuresPrecent=0
    
    
    # Pass scheduled jobs for the current user
    user_jobs = [job for job in scheduled_jobs if job['user'] == session['user']]
    utc_timezones = [tz for tz in pytz.all_timezones if tz.startswith('UTC')]              
    
    return render_template('dashboard.html', user=username, data=data, all_domains=all_domains, latest_results=latest_results, scheduled_jobs=user_jobs,
                            utc_timezones=utc_timezones,last_run=globalInfo['runInfo'][0] ,number_of_domains=f"{len(all_domains)} failures {failuresPrecent} %" ,BE_SERVER_ip=app.config["BE_SERVER"])



# Route to run Livness check 
@app.route('/check/<username>', methods=['GET'])
def check_livness(username):    
    if session['user']=="" :
        return "No User is logged in" 
    url= f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} "#,{info['numberOfDomains']}"      
    return info



# Route for user results
@app.route('/results', methods=['GET'])
def results():    
    try:        
        username=session['user']    
    except:        
        return render_template('login.html')

    username=session['user']   

    url= f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEresults/{username}'
    response = requests.get(url)
    if response.status_code == 200:
        resdata = response.json()        
    else:
        logger.log(f'Error: {response.status_code}')

    data=resdata['data']

    # Extract the required parts for the forms
    all_domains = [item['domain'] for item in data]  # List of domain names
    latest_results = data[:6]  # Last 6 results
    # Calculate failures 
    failuresCount = sum(1 for item in data if item.get('status_code') == 'FAILED' )
    if len(all_domains)>0 :
        failuresPrecent=  round (float(float(failuresCount)/float(len(all_domains)))*100,1)
    else:
        failuresPrecent=0   
    lastRunInfo=f"{globalInfo['runInfo']}{len(all_domains)}-nodes,{failuresPrecent}% Failures"
        
    return render_template('results.html', user=session['user'], data=data, all_domains=all_domains, latest_results=latest_results,last_run=lastRunInfo,beserver_ip=app.config['BE_SERVER'])

# Route for Logoff
@app.route('/logoff', methods=['GET'])
def logoff():
    user=session['user']
    logger.info(f'User: {user} is logoff!')
    if user=="":
        return  ("No user is logged in")    
    session['user']=""    
    globalInfo['runInfo']=['--/--/---- --:-- ']
    
    return render_template('login.html' ,beserver_ip=app.config['BE_SERVER'])



@app.route('/register', methods=['GET'])
def register():            
    return render_template('register.html' ,beserver_ip=app.config['BE_SERVER'])

@app.route('/register_user', methods=['POST','GET'])
def register_user():            
    data = request.get_json()
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2') 
    logger.info("Registering user {username}")    
    url=f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEregister'

    # Data to be sent in the request
    data = {
       'username':username,
       'password1': password1,
       'password2': password2
        }

        # Headers for the request
    headers = {
            'Content-Type': 'application/json'
        }
 
    try:
        # Make a POST request to the BEregister endpoint
        response = requests.post(url, headers=headers, data=json.dumps(data))        
        return response.json()
    except:
        return "Registration error"

@app.route('/login_user', methods=['POST','GET'])
def login_user():            
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')         
    url=f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BElogin'    
    # Data to be sent in the request
    data = {
       'username':username,
       'password': password       
        }
        # Headers for the request
    headers = {
            'Content-Type': 'application/json'
        }
 
    try:
        # Make a POST request to the BElogin endpoint
        response = requests.post(url, headers=headers, data=json.dumps(data))        
        logger.info(f'info: logging user : {username}')
        logger.debug(f'debug :logging user : {username}')
        return response.json()
    except:
        return "Login error"
    
# Route for login page 
@app.route('/', methods=['GET'])
def home():
        return render_template('login.html')



@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()  # Parse JSON payload
    return {"received": data}, 200


@app.route('/upload', methods=['POST'])
def upload():
    url=f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEupload'

    if 'file' not in request.files or request.files['file'].filename == '':
        return {"error": "No file provided"}, 400

    file = request.files['file']
    username = request.form.get('user')

    files = {
        'file': (file.filename, file.stream, file.mimetype)
    }
    data = {
        'user': username
    }

    try:
        response = requests.post(url, files=files, data=data)

        if response.ok:            
            return response.json()
        else:
            return {"error": "File upload failed"}, response.status_code
    except Exception as e:
        logger.error("Error:", e)
        return {"error": "An error occurred during file upload"}, 500

    
# Route to add a single domain 
@app.route('/add_domain/<domainName>/<userName>',methods=['GET', 'POST'])

def add_new_domain(domainName,userName):
    url= f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}//BEadd_domain/{domainName}/{userName}'    
    response  = requests.get(url)         
    return response.json()



@app.route('/remove_domain/<domainName>/<userName>',methods=['GET', 'POST'])

def remove_domain(domainName,userName):    
    url= f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}//BEremove_domain/{domainName}/{userName}'      
    response  = requests.get(url)         
    return response.json()

def Checkjob(username):       
    url= f'http://{app.config['BE_SERVER']}:{app.config['BE_PORT']}/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} ,{info['numberOfDomains']}"          
    return info



   



    
if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['FE_PORT'], debug=app.config['FLASK_DEBUG'])