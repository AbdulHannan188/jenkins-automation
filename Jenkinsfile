pipeline {
    agent any

    environment {
        GITHUB_REPO        = 'AbdulHannan188/check_deploy'  // ✅ correct repo
        GITHUB_CREDENTIALS = 'github-token'
        SOURCE_BRANCH_NAME = 'dev'
        TARGET_BRANCH      = 'main'
        PYTHON_VERSION     = 'python3'
        VENV_DIR           = '.venv'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "▶ Commit: ${env.GIT_COMMIT_SHORT} on dev branch"
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh """
                    ${PYTHON_VERSION} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        stage('Run Tests') {
            steps {
                sh """
                    # ── Install frontend deps & start Vite ───────────────
                    npm install
                    npm run dev -- --host 0.0.0.0 --port 5173 &
                    echo \$! > vite.pid

                    # ── Wait up to 60s for Vite to be ready ──────────────
                    echo "Waiting for Vite on port 5173..."
                    for i in \$(seq 1 30); do
                        if nc -z localhost 5173 2>/dev/null; then
                            echo "✅ Vite is up!"
                            break
                        fi
                        echo "  [\$i/30] not ready, waiting 2s..."
                        sleep 2
                    done

                    # ── Hard fail if Vite never started ───────────────────
                    nc -z localhost 5173 || { echo "❌ Vite never started!"; exit 1; }

                    # ── Run pytest ────────────────────────────────────────
                    . ${VENV_DIR}/bin/activate
                    BASE_URL=http://localhost:5173 pytest tests/ \
                        --junitxml=test-results/results.xml \
                        --html=test-results/report.html \
                        --self-contained-html \
                        -v
                """
            }
            post {
                always {
                    sh "[ -f vite.pid ] && kill \$(cat vite.pid) 2>/dev/null || true"
                    sh "rm -f vite.pid"
                    junit allowEmptyResults: true, testResults: 'test-results/results.xml'
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'test-results',
                        reportFiles          : 'report.html',
                        reportName           : 'Pytest Report'
                    ])
                }
            }
        }

        stage('Merge dev → main') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: "${GITHUB_CREDENTIALS}",
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
                            git config user.email "jenkins@ci.local"
                            git config user.name  "Jenkins CI"

                            # Authenticate remote
                            git remote set-url origin \
                                https://\${GIT_USER}:\${GIT_TOKEN}@github.com/${GITHUB_REPO}.git

                            # Fetch both branches
                            git fetch origin

                            # Merge dev into main and push
                            git checkout main
                            git merge --no-ff origin/dev \
                                -m "CI: merge dev → main [${env.GIT_COMMIT_SHORT}] ✅ all tests passed"
                            git push origin main
                        """
                    }
                }
                echo "✅ dev successfully merged into main!"
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline SUCCESS — dev merged into main"
        }
        failure {
            echo "❌ Pipeline FAILED — merge blocked, tests did not pass"
        }
        cleanup {
            sh "rm -rf ${VENV_DIR} test-results"
        }
    }
}