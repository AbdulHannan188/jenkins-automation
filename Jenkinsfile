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

        // ── 1. Clone check_deploy (ALL branches) ──────────────────────
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

                            # Clone ALL branches (no --single-branch)
                            git clone \
                                https://\${GIT_USER}:\${GIT_TOKEN}@github.com/${FRONTEND_REPO}.git \
                                ${FRONTEND_DIR}

                            cd ${FRONTEND_DIR}
                            git checkout ${SOURCE_BRANCH}
                            echo "▶ Cloned commit: \$(git rev-parse --short HEAD) on ${SOURCE_BRANCH}"
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

                            # Ensure authenticated remote
                            git remote set-url origin \
                                https://\${GIT_USER}:\${GIT_TOKEN}@github.com/${FRONTEND_REPO}.git

                            # Fetch latest from all branches
                            git fetch origin

                            # Show available remote branches (debug)
                            echo "── Available remote branches ──"
                            git branch -r

                            # Create local main tracking origin/main
                            git checkout -B ${TARGET_BRANCH} origin/${TARGET_BRANCH}

                            # Merge dev into main
                            git merge --no-ff origin/${SOURCE_BRANCH} \
                                -m "CI: merge ${SOURCE_BRANCH} → ${TARGET_BRANCH} ✅ all tests passed"

                            # Push merged main back to GitHub
                            git push origin ${TARGET_BRANCH}
                        """
                    }
                }
                echo "✅ ${SOURCE_BRANCH} merged into ${TARGET_BRANCH} in ${FRONTEND_REPO}!"
            }
        }
    }

    // ── Post-pipeline notifications ──────────────────────────────────
    post {
        success {
            echo "✅ Pipeline SUCCESS — ${SOURCE_BRANCH} merged into ${TARGET_BRANCH}"
        }
        failure {
            echo "❌ Pipeline FAILED — merge blocked, fix failing tests"
        }
        cleanup {
            sh "rm -rf ${VENV_DIR} ${FRONTEND_DIR} test-results"
        }
    }
}
