# locust file 
# run :                                     >  locust -f app_locust.py 
# check locust ui for test run    -         >  http://localhost:8089/

from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 to 5 seconds between tasks

    @task
    def homepage(self):
        self.client.get("http://127.0.0.1:5000/BElogin_lc")  # Simulates visiting the login page

    @task
    def about_page(self):
        pass
        #self.client.get("http://127.0.0.1:5000/")  # Simulates visiting the register page

    
    @task
    def Be_regisre(self):
        pass
        #self.client.get("http://127.0.0.1:5000/BEregister")  # Simulates visiting the register page

