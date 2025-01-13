pipeline {
    agent {
        label 'Docker'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                script {
                    cleanWs()
                    echo "Workspace cleaned."
                    sh '''
                    sudo docker rm -f $(sudo docker ps -a -q) || true
                    '''
                }
                echo "Docker containers removed."
            }
        }

        stage('Clone repo') {
            steps {
                script {
                    git branch: 'main', url: 'https://github.com/MayElbaz18/MoniTHOR--Project.git'
                }
                echo "Clone repo success!"
            }
        }

        stage('Docker build & run - Monithor - WebApp image') {
            steps {
                script {
                    sh """
                    sudo docker build -t monithor:temp .
                    sudo docker run --network host -d -p 8080:8080 --name monithor_container monithor:temp
                    """
                }
            }
        }

        stage('Move .env file to dir') {
            steps {
                script {
                    sh """
                    sudo docker cp /root/.env monithor_container:/MoniTHOR--Project
                    """
                }
            }
        }

        stage('Docker build & run - Selenium image') {
            steps {
                dir('selenium'){
                    script {
                        sh """
                        sudo docker build -t selenium:temp .
                        sudo docker run -d --network host --name selenium_container selenium:temp
                        """
                    }
                }
            }
        }

        stage('Show Results') {
            steps {
                script {
                    sh """
                    sudo docker logs selenium_container
                    """
                }
            }
        }
    }
}
