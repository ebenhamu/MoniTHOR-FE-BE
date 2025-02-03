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

app = Flask(__name__)  # __name__ helps Flask locate resources and configurations

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




os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
        url = 'http://127.0.0.1:5000/BEregister'

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
                logger.info('Error:', response.json())

        except Exception as e:
            print('An error occurred:', str(e))

        # Log the user in and redirect to the dashboard
        session['user'] = google_user["username"]
        return redirect(url_for("main"))
    else:
        return "User email not available or not verified by Google."
    



# Route for login page 
@app.route('/login', methods=['GET', 'POST'])
def login():
    local_ip = get_BEServer_ip()  # Get the local IP address
    return render_template('login.html' ,beserver_ip=local_ip)


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
    usr=session['user']    
    user_file =f'./userdata/{usr}_domains.json'
    if os.path.exists(user_file):
     with open(user_file, 'r') as f:
          data = json.load(f)
    else:
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
    
    local_ip = get_BEServer_ip()  # Get the local IP address
    
    
    return render_template('dashboard.html', user=session['user'], data=data, all_domains=all_domains, latest_results=latest_results, scheduled_jobs=user_jobs,
                            utc_timezones=utc_timezones,last_run=globalInfo['runInfo'][0] ,number_of_domains=f"{len(all_domains)} failures {failuresPrecent} %" ,beserver_ip=local_ip)



# Route to run Livness check 
@app.route('/check/<username>', methods=['GET'])
def check_livness(username):    
    if session['user']=="" :
        return "No User is logged in" 
    url = f'http://127.0.0.1:5000/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} "#,{info['numberOfDomains']}"      
    return info



# Route for user results
@app.route('/results', methods=['GET'])
def results():
    username=session['user']    


    url = f'http://127.0.0.1:5000/BEresults/{username}'
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
    
    local_ip = get_BEServer_ip()  # Get the local IP address
    return render_template('results.html', user=session['user'], data=data, all_domains=all_domains, latest_results=latest_results,last_run=lastRunInfo,beserver_ip=local_ip)

# Route for Logoff
@app.route('/logoff', methods=['GET'])
def logoff():
    user=session['user']
    logger.info(f'User: {user} is logoff!')
    if user=="":
        return  ("No user is logged in")    
    session['user']=""    
    globalInfo['runInfo']=['--/--/---- --:-- ']
    local_ip = get_BEServer_ip()  # Get the local IP address
    return render_template('login.html' ,beserver_ip=local_ip)



@app.route('/register', methods=['GET'])
def register():        
    local_ip = get_BEServer_ip()  # Get the local IP address
    return render_template('register.html' ,beserver_ip=local_ip)


# Route for login page 
@app.route('/', methods=['GET'])
def home():
        return render_template('login.html')



@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()  # Parse JSON payload
    return {"received": data}, 200

    
    
    

def Checkjob(username):       
    url = f'http://127.0.0.1:5000/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} ,{info['numberOfDomains']}"          
    return info

# Function to get the backend server IP
def get_BEServer_ip():
    if app.config["BEServer"] == 'localhost':
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    else:
        return  app.config["BEServer"]
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
