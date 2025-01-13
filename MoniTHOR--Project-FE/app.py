from flask import Flask, session, render_template,redirect,request, url_for , jsonify
import requests 

from oauthlib.oauth2 import WebApplicationClient
from pythonBE import user , check_liveness ,domain
from pythonBE.logs import logger
import json
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz
import uuid
from datetime import datetime 
import subprocess

# Load environment variables from .env fileload_dotenv()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)  # __name__ helps Flask locate resources and configurations
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global parmeters to keep last job info.
global globalInfo 
globalInfo = {'runInfo': ('--/--/---- --:--', '-')} 

# Google OAuth2 details
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')

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
        # Save the user to users.json if not already saved
        with open('users.json', 'r') as f:
          current_info = json.load(f)
          currentListOfUsers=list(current_info)

        # Check if the user already exists
        if not any(user['username'] == google_user["username"] for user in currentListOfUsers):
            currentListOfUsers.append({"username": google_user["username"]})
            with open('users.json', 'w') as f:
                json.dump(currentListOfUsers, f, indent=4)

        # Log the user in and redirect to the dashboard
        session['user'] = google_user["username"]
        return redirect(url_for("main"))
    else:
        return "User email not available or not verified by Google."
    



# Route for login page 
@app.route('/login', methods=['GET', 'POST'])
def login():    
    return render_template('login.html')



@app.route('/update_user', methods=['POST'])
def BElogin():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')                        
        session['user'] = username
        globalInfo['runInfo'] = ['--/--/---- --:--', '-']
        logger.info(f"User: {username} Login Successful")     
        print("update user") 
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
    
    
    return render_template('dashboard.html', user=session['user'], data=data, all_domains=all_domains, latest_results=latest_results, scheduled_jobs=user_jobs,
                            utc_timezones=utc_timezones,last_run=globalInfo['runInfo'][0] ,number_of_domains=f"{globalInfo['runInfo'][1]} failures {failuresPrecent} %" )



# Route to run Livness check 
@app.route('/check/<username>', methods=['GET'])
def check_livness(username):    
    if session['user']=="" :
        return "No User is logged in" 
    url = f'http://127.0.0.1:5000/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} ,{info['numberOfDomains']}"
    print(globalInfo['runInfo'])
    # globalInfo['runInfo'][1]=info['']
    print (info)

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
        print(f'Error: {response.status_code}')

    
    user_file =f'./userdata/{username}_domains.json' 
    if os.path.exists(user_file):
     with open(user_file, 'r') as f:
          data = json.load(f)
    else:
        data = []      
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
    lastRunInfo=f"{globalInfo['runInfo']}-nodes,{failuresPrecent}% Failures"
    print(lastRunInfo)
    
    return render_template('results.html', user=session['user'], data=data, all_domains=all_domains, latest_results=latest_results,last_run=lastRunInfo)

# Route for Logoff
@app.route('/logoff', methods=['GET'])
def logoff():
    user=session['user']
    logger.info(f'User: {user} is logoff!')
    if user=="":
        return  ("No user is logged in")    
    session['user']=""    
    globalInfo['runInfo']=['--/--/---- --:--', '-']
    return  render_template('login.html')



# # Route for Register 
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     username = request.args.get('username')
#     password1 = request.args.get('password1')
#     password2 = request.args.get('password2')
#     logger.debug(f"Received: username={username}, password1={password1}, password2={password2} for register to monithor!")
#     # Process registration
#     status = user.register_user(username, password1, password2)

#     # Validate input parameters
#     if password1 != password2:        
#         return "Passwords do not match"
#     if status['message'] == 'Username already taken':
#         return "Username already taken"
#     if status['message'] == 'Registered successfully':
#         return "Registered successfully"         

#     return render_template('register.html')
    


@app.route('/BEregister', methods=['POST'])
def BEregister():
    print ("*********************")
    data = request.get_json()
    username = data.get('username')
    password1 = data.get('password1')
    password2 = data.get('password2')

    logger.debug(f"Received: username={username}, password1={password1}, password2={password2} for register to monithor!")

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
   


@app.route('/register', methods=['GET'])
def register():        
        return render_template('register.html')


# Route for login page 
@app.route('/', methods=['GET'])
def home():
        return render_template('login.html')



@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()  # Parse JSON payload
    return {"received": data}, 200

# Route to add a single domain 
@app.route('/add_domain/<domainName>',methods=['GET', 'POST'])
def add_new_domain(domainName):
    logger.debug(f'New domain added {domainName}')
    if session['user']=="" :
        return "No User is logged in" 
    # Get the domain name from the form data
    logger.debug(f'Domain name is {domainName}')
        
    return domain.add_domain(session['user'],domainName)   
    
# Route to remove a single domain 
@app.route('/remove_domain/<domainName>', methods=['GET', 'POST'])
def remove_domain(domainName):
    logger.debug(f'Remove domain being called to domain: {domainName}')
    if session['user'] == "":
        return "No User is logged in"

    logger.debug(f'Domain name is {domainName}')    
    response = domain.remove_domain(session['user'], domainName)

    if response['message'] == "Domain successfully removed":       
        try:
            logger.debug(f"Before update: globalInfo['runInfo']: {globalInfo['runInfo']}")
            current_count = int(globalInfo['runInfo'][1])
            if current_count>0:
                globalInfo['runInfo'] = (globalInfo['runInfo'][0], str(current_count - 1))
            logger.debug(f"After update: globalInfo['runInfo']: {globalInfo['runInfo']}")
        except ValueError:
            logger.error(f"Invalid value in globalInfo['runInfo'][1]: {globalInfo['runInfo'][1]}")
            globalInfo['runInfo'] = (globalInfo['runInfo'][0], '0')  # Fallback value

        return response
    
    
    return "Error: Domain could not be removed"
    

# usage : http://127.0.0.1:8080/bulk_upload/.%5Cuserdata%5CDomains_for_upload.txt 
# using  %5C instaed of  "\"  
# in UI put    ./userdata/Domains_for_upload.txt

@app.route('/bulk_upload/<filename>')
def add_from_file(filename):    
    if session['user']=="" :
        return "No User is logged in"           
    logger.info(f"File for bulk upload:{filename}")
    return domain.add_bulk(session['user'],filename)
    
    

    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        add_from_file(filepath)
        if os.path.exists(filepath): 
            os.remove(filepath)
               
        
        return {'message':'File successfully uploaded','file': filepath }

def Checkjob(username):       
    url = f'http://127.0.0.1:5000/BEcheck/{username}'
    respponse  = requests.get(url)        
    info=respponse.json()
    globalInfo['runInfo']=f"{info['start_date_time']} ,{info['numberOfDomains']}"
    print(globalInfo['runInfo'])
    # globalInfo['runInfo'][1]=info['']
    print (info)
    return info




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
