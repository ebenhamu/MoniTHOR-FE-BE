#!groovy

import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// Configure security realm with admin user
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin") // username: admin, password: admin
instance.setSecurityRealm(hudsonRealm)

// Configure authorization strategy
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false) // Disable anonymous access
instance.setAuthorizationStrategy(strategy)

instance.save()

println("Admin user 'admin' created with password 'admin'.")
