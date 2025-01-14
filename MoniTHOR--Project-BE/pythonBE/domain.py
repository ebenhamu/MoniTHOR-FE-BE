import os
import json
import re
from logger.logs import logger


def add_domain (userName,domain) :
    logger.debug(f'Function is invoked {userName}, {domain}')
    successMessage = { 'message' : "Domain successfully added"}
    failureMessageExist = { 'message' : "Domain already exist in file"}
    failureMessageNotValid = { 'message' : "Invalid Domain Name"}
    
    domain=domain.replace('"','')
    
    if not is_valid_domain(domain):
        return failureMessageNotValid

    
    userDomainsFile=f'./userdata/{userName}_domains.json'
    
    
    
    if not os.path.exists(userDomainsFile) :
         with open(userDomainsFile, 'w') as f:
            f.write("{}")



    with open(f'{userDomainsFile}', 'r') as f:
        current_info = json.load(f)
        currentListOfDomains=list(current_info)       
        
       
    for d in currentListOfDomains :             
        if d['domain'] == domain:            
            return failureMessageExist

    newDomain ={'domain':domain,'status':'unknown','ssl_expiration':'unknown','ssl_issuer':'unknown' }
    
    if len(currentListOfDomains) < 100 :
        currentListOfDomains.append(newDomain)             
    

    with open(userDomainsFile, 'w') as f:        
        json.dump(currentListOfDomains, f, indent=4)
        logger.debug(f'The {domain} Upload To {userDomainsFile} By {userName}')        
      
        return successMessage



def remove_domain (userName,domain) :
    logger.debug(f'Function is invoked {userName}, {domain}')
    successMessage = { 'message' : "Domain successfully removed"}
    notInFileMessage = { 'message' : "Domain not in file"}
    failureMessageNotValid = { 'message' : "Invalid Domain Name"}
    domainsFileisNotExist  = { 'message' : "Domains file is not exist"}
    
    domain=domain.replace('"','')
    
    if not is_valid_domain(domain):
        return failureMessageNotValid

    userDomainsFile=f'./userdata/{userName}_domains.json'
    
    if not os.path.exists(userDomainsFile):
        return domainsFileisNotExist



    with open(userDomainsFile, 'r') as f:
        current_info = json.load(f)
        currentListOfDomains=list(current_info)
        newList=[]
        
    msg=notInFileMessage
    for d in currentListOfDomains :        
        if d['domain'] == domain:
            msg=successMessage
        else:
            newList.append(d) 
       
    with open(userDomainsFile, 'w') as f:
        json.dump(newList, f, indent=4)        
        return msg
# function to read from file a list of domain and add to domain file.

def add_bulk(userName,fileName):
    fileName=fileName.replace('"','')
    logger.debug(f"File: {fileName}, User: {userName}")

    
    if not os.path.exists(fileName):
        return "File Not Exist"
    
    try:
        with open(fileName, 'r') as infile:
            for line in infile:
                add_domain(userName,line.strip())
    
    except Exception as e:        
        return (str(e))
     
    return "Bulk upload finished"






# Function to validate the domain name

def is_valid_domain(s):    
    # Regex to check valid Domain Name
    pattern= r"^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$"         
    
    # Return string matche value - bool
    return bool(re.match(pattern,s))





