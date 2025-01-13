import jenkins.model.*
import hudson.security.*
import hudson.util.*

def instance = Jenkins.getInstance()
def pm = instance.getPluginManager()
def uc = instance.getUpdateCenter()

def plugins = [
  'ace-editor', 'ant', 'antisamy-markup-formatter', 'apache-httpcomponents-client-4-api',
  'bootstrap4-api', 'bootstrap5-api', 'bouncycastle-api', 'branch-api', 'build-timeout',
  'caffeine-api', 'checks-api', 'cloudbees-folder', 'command-launcher', 'credentials',
  'credentials-binding', 'display-url-api', 'durable-task', 'echarts-api', 'email-ext',
  'font-awesome-api', 'git', 'git-client', 'git-server', 'github', 'github-api',
  'github-branch-source', 'gradle', 'handlebars', 'jackson2-api', 'jaxb', 'jdk-tool',
  'jjwt-api', 'jquery3-api', 'jsch', 'junit', 'ldap', 'lockable-resources', 'mailer',
  'matrix-auth', 'matrix-project', 'momentjs', 'okhttp-api', 'pam-auth', 'pipeline-build-step',
  'pipeline-github-lib', 'pipeline-graph-analysis', 'pipeline-input-step',
  'pipeline-milestone-step', 'pipeline-model-api', 'pipeline-model-definition',
  'pipeline-model-extensions', 'pipeline-rest-api', 'pipeline-stage-step',
  'pipeline-stage-tags-metadata', 'pipeline-stage-view', 'plain-credentials',
  'plugin-util-api', 'popper-api', 'popper2-api', 'resource-disposer', 'scm-api',
  'script-security', 'snakeyaml-api', 'ssh-credentials', 'ssh-slaves', 'sshd', 'structs',
  'timestamper', 'token-macro', 'trilead-api', 'workflow-aggregator', 'workflow-api',
  'workflow-basic-steps', 'workflow-cps', 'workflow-cps-global-lib', 'workflow-durable-task-step',
  'workflow-job', 'workflow-multibranch', 'workflow-scm-step', 'workflow-step-api',
  'workflow-support', 'ws-cleanup', 'pipline-stage-view'
]

plugins.each {
  if (!pm.getPlugin(it)) {
    def plugin = uc.getPlugin(it)
    if (plugin) {
      plugin.deploy()
    }
  }
}

instance.save()
