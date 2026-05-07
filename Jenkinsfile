pipeline {
    agent any

    environment {
        // ── jenkins-automation repo (this repo) ──────────────────────
        GITHUB_CREDENTIALS = 'github-token'

        // ── check_deploy repo (your frontend) ────────────────────────
        FRONTEND_REPO      = 'AbdulHannan188/check_deploy'
        FRONTEND_DIR       = 'check_deploy'        // local folder name
        SOURCE_BRANCH      = 'dev'
        TARGET_BRANCH      = 'main'

        // ── Python ───────────────────────────────────────────────────
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
        // ── 1. Clone check_deploy dev branch ─────────────────────────
        stage('Checkout Frontend (check_deploy)') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: "${GITHUB_CREDENTIALS}",
                        usernameVariable: 'GIT_USER',
                        passwordVariable: 'GIT_TOKEN'
                    )]) {
                        sh """
                            # Remove old clone if exists
                            rm -rf ${FRONTEND_DIR}

                            # Clone only the dev branch
                            git clone \
                                --branch ${SOURCE_BRANCH} \
                                --single-branch \
                                https://\${GIT_USER}:\${GIT_TOKEN}@github.com/${FRONTEND_REPO}.git \
                                ${FRONTEND_DIR}

                            cd ${FRONTEND_DIR}
                            echo "▶ Cloned commit: \$(git rev-parse --short HEAD)"
                        """
                    }
                }
            }
        }

        // ── 2. Setup Python venv ──────────────────────────────────────
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

        // ── 3. Start Vite + Run Tests ─────────────────────────────────
        stage('Run Tests') {
            steps {
                sh """
                    # ── Install frontend deps & start Vite ───────────
                    cd ${FRONTEND_DIR}
                    npm install
                    npm run dev -- --host 0.0.0.0 --port 5173 &
                    echo \$! > ../vite.pid

                    cd ..

                    # ── Wait up to 60s for Vite ───────────────────────
                    echo "Waiting for Vite on port 5173..."
                    for i in \$(seq 1 30); do
                        if nc -z localhost 5173 2>/dev/null; then
                            echo "✅ Vite is up!"
                            break
                        fi
                        echo "  [\$i/30] waiting 2s..."
                        sleep 2
                    done

                    # ── Hard fail if Vite never came up ───────────────
                    nc -z localhost 5173 || { echo "❌ Vite never started!"; exit 1; }

                    # ── Run pytest ────────────────────────────────────
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
                    sh 'rm -f vite.pid'
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

        // ── 4. Merge dev → main in check_deploy ──────────────────────
        stage('Merge dev → main (check_deploy)') {
            steps {
                script {
                    withCredentials([usernamePassword(
                credentialsId: "${GITHUB_CREDENTIALS}",
                usernameVariable: 'GIT_USER',
                passwordVariable: 'GIT_TOKEN'
            )]) {
                        sh """
                    cd ${FRONTEND_DIR}

                    git config user.email "jenkins@ci.local"
                    git config user.name  "Jenkins CI"

                    # Authenticate remote
                    git remote set-url origin \
                        https://\${GIT_USER}:\${GIT_TOKEN}@github.com/${FRONTEND_REPO}.git

                    # Fetch all branches (not just dev)
                    git fetch origin

                    # Create local main tracking origin/main  ← THIS IS THE FIX
                    git checkout -b main origin/main

                    # Merge dev into main
                    git merge --no-ff origin/dev \
                        -m "CI: merge dev → main ✅ all tests passed"

                    # Push to check_deploy main
                    git push origin main
                """
            }
                }
                echo '✅ dev merged into main in check_deploy!'
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline SUCCESS — check_deploy dev merged into main'
        }
        failure {
            echo '❌ Pipeline FAILED — merge blocked, fix failing tests'
        }
        cleanup {
            sh "rm -rf ${VENV_DIR} ${FRONTEND_DIR} test-results"
        }
    }
}
