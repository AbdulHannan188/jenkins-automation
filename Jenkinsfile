pipeline {
    agent any

    environment {
        // CHANGE THIS to your React app's GitHub URL
        REACT_REPO_URL = 'https://github.com/AbdulHannan188/your-react-repo.git'
        REACT_BRANCH = 'main'
        BASE_URL = 'http://localhost:5173'
    }

    stages {
        stage('Checkout Selenium tests') {
            steps {
                checkout scm
            }
        }

        stage('Checkout React app') {
            steps {
                dir('react-app') {
                    git branch: "${REACT_BRANCH}", url: "${REACT_REPO_URL}"
                }
            }
        }

        stage('Setup Python venv') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Install React dependencies') {
            steps {
                dir('react-app') {
                    sh 'npm install'
                }
            }
        }

        stage('Start React app') {
            steps {
                sh '''
                    cd react-app
                    nohup npm run dev -- --host 0.0.0.0 > /tmp/vite.log 2>&1 &
                    echo $! > /tmp/vite.pid

                    echo "Waiting for Vite to be ready..."
                    for i in $(seq 1 60); do
                        if curl -s http://localhost:5173 > /dev/null; then
                            echo "Vite is up!"
                            exit 0
                        fi
                        sleep 1
                    done

                    echo "Vite failed to start within 60 seconds"
                    cat /tmp/vite.log
                    exit 1
                '''
            }
        }

        stage('Run Selenium tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest
                '''
            }
        }
    }

    post {
        always {
            sh '''
                if [ -f /tmp/vite.pid ]; then
                    kill $(cat /tmp/vite.pid) 2>/dev/null || true
                    rm -f /tmp/vite.pid
                fi
            '''

            junit allowEmptyResults: true, testResults: 'results.xml'

            publishHTML([
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'report.html',
                reportName: 'Selenium HTML Report'
            ])

            archiveArtifacts artifacts: 'report.html, results.xml', allowEmptyArchive: true
        }

        failure {
            echo 'Build failed — check console output and Vite log above'
        }
    }
}