import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException
import requests
from requests.exceptions import RequestException
import ssl
import socket
from datetime import datetime


def get_url_status(url):
    try:        
        response = requests.get(f'http://{url}', timeout=10)                  
        if response.status_code==200:
            return 'OK'
        else:
            return 'FAILED'
    except RequestException as e:
        return 'FAILED'




def certificate_checks(url):
    try:
        # Remove "https://", "http://", "www." from the URL if present
        hostname = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        
        # Establish a secure connection to fetch the SSL certificate
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443) ,timeout=1) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()                                             
                
        # Get the certificate's expiration date
        expiry_date_str = cert['notAfter']
        expiry_date = datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z")                       
        
        # Convert expiration date to a readable string format
        expiry_date_formatted = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
                      
        issued_by = dict(x[0] for x in cert['issuer'])
        issuer = issued_by['organizationName']               
        
        # Check if the certificate is expired
        return expiry_date_formatted , issuer
        
    except Exception as e:
        return 'FAILED','FAILED'


