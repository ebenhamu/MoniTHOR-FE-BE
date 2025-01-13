#!groovy

import jenkins.model.*

def instance = Jenkins.getInstance()
def jenkinsUrl = "http://{{ ansible_host }}:8080" // Replace with your Jenkins URL

instance.setSystemMessage("Welcome to Jenkins!")
instance.getDescriptorByType(jenkins.model.JenkinsLocationConfiguration.class).setUrl(jenkinsUrl)

instance.save()
