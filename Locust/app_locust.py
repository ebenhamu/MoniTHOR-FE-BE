# locust file 
# run :                                     >  locust -f app_locust.py 
# check locust ui for test run    -         >  http://localhost:8089/

import json
from locust import HttpUser, task, between
import random

class MyUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 to 5 seconds between tasks

    @task
    def homepage(self):
        pass
        #self.client.get("http://127.0.0.1:5000/BElogin_lc")  # Simulates visiting the login page

    @task
    def about_page(self):
        # Define character set (only digits)
        all_characters = '0123456789'
        # Generate a random password
        tag = ''.join(random.choice(all_characters) for _ in range(2))
        username='tester_'+tag
        
        url= f"http://127.0.0.1:5000/BEcheck"
        data={
            'username':username
        }
        headers = {
            'Content-Type': 'application/json'
        }
        self.client.get(url, headers=headers, data=json.dumps(data))          






        
        

    
    @task
    def Be_regisre(self):
        pass
        #self.client.get("http://127.0.0.1:5000/BEregister")  # Simulates visiting the register page

