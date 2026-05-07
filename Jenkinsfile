pipeline {
    agent any

    environment {
        GITHUB_REPO        = 'https://github.com/AbdulHannan188/check_deploy.git'// ← change this
        GITHUB_CREDENTIALS = 'github-token'                      // ← Jenkins credential ID
        TARGET_BRANCH      = 'main'                              // ← branch to merge into
        PYTHON_VERSION     = 'python3'
        VENV_DIR           = '.venv'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    triggers {
        // Activated by GitHub webhook (configure webhook in GitHub → Settings → Webhooks)
        githubPush()
    }

    stages {
        // ── 1. Checkout ──────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.SOURCE_BRANCH = sh(
                        script: 'git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "▶ Branch: ${env.SOURCE_BRANCH}  |  Commit: ${env.GIT_COMMIT_SHORT}"
            }
        }

        // ── 2. Set up Python virtual environment ─────────────────────────────
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

        // ── 3. Run pytest ────────────────────────────────────────────────────
        stage('Run Tests') {
            steps {
                sh """
            # ── Start the Vite frontend in background ─────────────────
            npm install
            npm run dev -- --host 0.0.0.0 --port 5173 &
            echo \$! > vite.pid

            # ── Wait up to 60s for port 5173 to be ready ─────────────
            echo "Waiting for Vite on port 5173..."
            for i in \$(seq 1 30); do
                if nc -z localhost 5173 2>/dev/null; then
                    echo "✅ Vite is up!"
                    break
                fi
                echo "  [\$i/30] waiting..."
                sleep 2
            done

            # ── Hard fail if app never came up ────────────────────────
            nc -z localhost 5173 || { echo "❌ Vite never started!"; exit 1; }

            # ── Run pytest ────────────────────────────────────────────
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

        // ── 4. Merge into target branch (only if tests passed) ───────────────
        stage('Merge to Target Branch') {
            // Only merge when not already on the target branch
            when {
                not { branch "${TARGET_BRANCH}" }
            }
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

                            # Set authenticated remote URL
                            git remote set-url origin \
                                https://${GIT_USER}:${GIT_TOKEN}@github.com/${GITHUB_REPO}.git

                            # Fetch latest target branch
                            git fetch origin ${TARGET_BRANCH}

                            # Switch to target branch and merge
                            git checkout ${TARGET_BRANCH}
                            git merge --no-ff ${env.SOURCE_BRANCH} \
                                -m "CI merge: ${env.SOURCE_BRANCH} → ${TARGET_BRANCH} [${env.GIT_COMMIT_SHORT}]"

                            # Push the merge
                            git push origin ${TARGET_BRANCH}
                        """
                    }
                }
                echo "✅ Merged ${env.SOURCE_BRANCH} into ${TARGET_BRANCH}"
            }
        }
    }

    // ── Post-pipeline notifications ──────────────────────────────────────────
    post {
        success {
            echo "✅ Pipeline SUCCESS — code merged into ${TARGET_BRANCH}"
        // Optional: add Slack/email notification here
        }
        failure {
            echo '❌ Pipeline FAILED — merge blocked. Check test results above.'
        // Optional: add Slack/email notification here
        }
        cleanup {
            // Remove virtualenv to keep workspace tidy
            sh "rm -rf ${VENV_DIR} test-results"
        }
    }
}
