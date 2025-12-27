#!/usr/bin/env groovy

/**
 * EDMS Jenkins Declarative Pipeline
 * 
 * Complete CI/CD pipeline with automated testing, deployment, and rollback
 * 
 * Required Jenkins Plugins:
 * - Pipeline
 * - Docker Pipeline
 * - SSH Agent
 * - Credentials Binding
 * - Blue Ocean (optional, for better UI)
 * 
 * Required Credentials:
 * - staging-ssh-key: SSH private key for staging
 * - production-ssh-key: SSH private key for production
 * - github-token: GitHub token for releases
 */

pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '30', daysToKeepStr: '90'))
        disableConcurrentBuilds()
        timeout(time: 2, unit: 'HOURS')
        timestamps()
    }
    
    parameters {
        choice(
            name: 'DEPLOYMENT_ENV',
            choices: ['none', 'staging', 'production'],
            description: 'Target deployment environment'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run test suite'
        )
        booleanParam(
            name: 'SKIP_VALIDATION',
            defaultValue: false,
            description: 'Skip pre-deployment validation (not recommended)'
        )
    }
    
    environment {
        PACKAGE_NAME = "edms-production-${BUILD_NUMBER}"
        DOCKER_BUILDKIT = '1'
        COMPOSE_DOCKER_CLI_BUILD = '1'
        
        // Staging credentials
        STAGING_HOST = credentials('staging-host')
        STAGING_USER = credentials('staging-user')
        
        // Production credentials
        PRODUCTION_HOST = credentials('production-host')
        PRODUCTION_USER = credentials('production-user')
    }
    
    stages {
        // ====================================================================
        // STAGE 1: CHECKOUT AND SETUP
        // ====================================================================
        stage('Checkout') {
            steps {
                script {
                    echo "🔄 Checking out code..."
                    checkout scm
                    
                    // Get commit info
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    
                    env.GIT_COMMIT_MSG = sh(
                        script: "git log -1 --pretty=%B",
                        returnStdout: true
                    ).trim()
                    
                    echo "Commit: ${env.GIT_COMMIT_SHORT}"
                    echo "Message: ${env.GIT_COMMIT_MSG}"
                }
            }
        }
        
        // ====================================================================
        // STAGE 2: PRE-DEPLOYMENT VALIDATION
        // ====================================================================
        stage('Pre-Deployment Validation') {
            when {
                expression { return !params.SKIP_VALIDATION }
            }
            steps {
                script {
                    echo "✅ Running pre-deployment checks..."
                    
                    sh '''
                        chmod +x scripts/create-production-package.sh
                        chmod +x scripts/pre-deploy-check.sh
                        
                        # Create package
                        ./scripts/create-production-package.sh
                        
                        # Run validation
                        ./scripts/pre-deploy-check.sh edms-production-*/
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'edms-production-*/pre-deployment-report-*.txt',
                        allowEmptyArchive: true,
                        fingerprint: true
                    )
                }
            }
        }
        
        // ====================================================================
        // STAGE 3: TESTING
        // ====================================================================
        stage('Run Tests') {
            when {
                expression { return params.RUN_TESTS }
            }
            parallel {
                stage('Backend Tests') {
                    agent {
                        docker {
                            image 'python:3.11'
                            args '-v /var/run/docker.sock:/var/run/docker.sock'
                        }
                    }
                    steps {
                        script {
                            echo "🧪 Running backend tests..."
                            sh '''
                                cd backend
                                pip install -q -r requirements/test.txt
                                python manage.py test --verbosity=2
                                python manage.py check --deploy
                            '''
                        }
                    }
                    post {
                        always {
                            junit(
                                testResults: 'backend/test-results.xml',
                                allowEmptyResults: true
                            )
                        }
                    }
                }
                
                stage('Frontend Tests') {
                    agent {
                        docker {
                            image 'node:20'
                        }
                    }
                    steps {
                        script {
                            echo "🧪 Running frontend tests..."
                            sh '''
                                cd frontend
                                npm ci --quiet
                                npm run lint || true
                                npm test -- --watchAll=false
                                npm run build
                            '''
                        }
                    }
                    post {
                        always {
                            archiveArtifacts(
                                artifacts: 'frontend/build/**/*',
                                allowEmptyArchive: true
                            )
                        }
                    }
                }
            }
        }
        
        // ====================================================================
        // STAGE 4: CREATE DEPLOYMENT PACKAGE
        // ====================================================================
        stage('Create Deployment Package') {
            steps {
                script {
                    echo "📦 Creating deployment package..."
                    
                    sh '''
                        chmod +x scripts/create-production-package.sh
                        ./scripts/create-production-package.sh
                        
                        # List created files
                        ls -lh edms-production-*.tar.gz
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'edms-production-*.tar.gz',
                        fingerprint: true
                    )
                    archiveArtifacts(
                        artifacts: 'edms-production-*/MANIFEST.txt',
                        fingerprint: true
                    )
                    archiveArtifacts(
                        artifacts: 'edms-production-*/checksums.sha256',
                        fingerprint: true
                    )
                }
            }
        }
        
        // ====================================================================
        // STAGE 5: DEPLOY TO STAGING
        // ====================================================================
        stage('Deploy to Staging') {
            when {
                anyOf {
                    branch 'develop'
                    expression { return params.DEPLOYMENT_ENV == 'staging' }
                }
            }
            steps {
                script {
                    echo "🚀 Deploying to staging environment..."
                    
                    sshagent(credentials: ['staging-ssh-key']) {
                        sh '''
                            chmod +x scripts/deploy-to-remote.sh
                            
                            # Deploy
                            ./scripts/deploy-to-remote.sh \
                                ${STAGING_USER}@${STAGING_HOST} \
                                --path /opt/edms \
                                --verbose
                            
                            # Validate deployment
                            ssh ${STAGING_USER}@${STAGING_HOST} \
                                'cd /opt/edms-production-* && ./scripts/post-deploy-check.sh'
                            
                            # Run health check
                            ssh ${STAGING_USER}@${STAGING_HOST} \
                                'cd /opt/edms-production-* && ./scripts/health-check.sh --alert'
                            
                            # Download reports
                            scp ${STAGING_USER}@${STAGING_HOST}:/opt/edms-production-*/post-deployment-report-*.txt \
                                ./staging-validation-report.txt || true
                            
                            scp ${STAGING_USER}@${STAGING_HOST}:/opt/edms-production-*/health-report-*.html \
                                ./staging-health-report.html || true
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'staging-*.txt,staging-*.html',
                        allowEmptyArchive: true
                    )
                }
                success {
                    echo "✅ Staging deployment successful!"
                }
                failure {
                    echo "❌ Staging deployment failed!"
                }
            }
        }
        
        // ====================================================================
        // STAGE 6: STAGING SMOKE TESTS
        // ====================================================================
        stage('Staging Smoke Tests') {
            when {
                anyOf {
                    branch 'develop'
                    expression { return params.DEPLOYMENT_ENV == 'staging' }
                }
            }
            steps {
                script {
                    echo "🔥 Running smoke tests on staging..."
                    
                    sshagent(credentials: ['staging-ssh-key']) {
                        sh '''
                            for i in {1..3}; do
                                echo "Health check $i/3..."
                                ssh ${STAGING_USER}@${STAGING_HOST} \
                                    'cd /opt/edms-production-* && ./scripts/health-check.sh --quick' || exit 1
                                
                                if [ $i -lt 3 ]; then
                                    sleep 30
                                fi
                            done
                            
                            echo "✅ Staging smoke tests passed"
                        '''
                    }
                }
            }
        }
        
        // ====================================================================
        // STAGE 7: DEPLOY TO PRODUCTION (MANUAL APPROVAL)
        // ====================================================================
        stage('Deploy to Production') {
            when {
                anyOf {
                    branch 'main'
                    expression { return params.DEPLOYMENT_ENV == 'production' }
                }
            }
            steps {
                script {
                    // Manual approval
                    timeout(time: 1, unit: 'HOURS') {
                        input(
                            message: 'Deploy to Production?',
                            ok: 'Deploy',
                            submitter: 'admin,release-manager',
                            parameters: [
                                booleanParam(
                                    name: 'CONFIRMED',
                                    defaultValue: false,
                                    description: 'I confirm this deployment to production'
                                )
                            ]
                        )
                    }
                    
                    echo "🚀 Deploying to production environment..."
                    
                    sshagent(credentials: ['production-ssh-key']) {
                        sh '''
                            # Create backup
                            echo "Creating pre-deployment backup..."
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-current && ./scripts/backup-system.sh' || echo "Backup failed"
                            
                            # Deploy
                            chmod +x scripts/deploy-to-remote.sh
                            ./scripts/deploy-to-remote.sh \
                                ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                --path /opt/edms \
                                --verbose
                            
                            # Post-deployment validation
                            echo "Running post-deployment validation..."
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-production-* && ./scripts/post-deploy-check.sh'
                            
                            # Health check with alert
                            echo "Running health check..."
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-production-* && ./scripts/health-check.sh --alert --report'
                            
                            # Download reports
                            scp ${PRODUCTION_USER}@${PRODUCTION_HOST}:/opt/edms-production-*/post-deployment-report-*.txt \
                                ./production-validation-report.txt || true
                            
                            scp ${PRODUCTION_USER}@${PRODUCTION_HOST}:/opt/edms-production-*/health-report-*.html \
                                ./production-health-report.html || true
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'production-*.txt,production-*.html',
                        allowEmptyArchive: true,
                        fingerprint: true
                    )
                }
                success {
                    echo "✅ Production deployment successful!"
                    
                    // Send success notification
                    script {
                        emailext(
                            subject: "✅ Production Deployment Successful - Build #${BUILD_NUMBER}",
                            body: """
                                Production deployment completed successfully!
                                
                                Build: #${BUILD_NUMBER}
                                Commit: ${env.GIT_COMMIT_SHORT}
                                Message: ${env.GIT_COMMIT_MSG}
                                
                                View build: ${BUILD_URL}
                                View artifacts: ${BUILD_URL}artifact/
                            """,
                            to: '${DEFAULT_RECIPIENTS}',
                            attachLog: false
                        )
                    }
                }
                failure {
                    echo "❌ Production deployment failed! Initiating rollback..."
                    
                    // Automatic rollback
                    sshagent(credentials: ['production-ssh-key']) {
                        sh '''
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-production-* && ./scripts/rollback.sh --previous --backup-first --force'
                            
                            # Verify rollback
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-production-* && ./scripts/health-check.sh --alert'
                        '''
                    }
                    
                    // Send failure notification
                    script {
                        emailext(
                            subject: "❌ Production Deployment Failed - Build #${BUILD_NUMBER}",
                            body: """
                                Production deployment failed and was rolled back!
                                
                                Build: #${BUILD_NUMBER}
                                Commit: ${env.GIT_COMMIT_SHORT}
                                
                                Check logs: ${BUILD_URL}console
                            """,
                            to: '${DEFAULT_RECIPIENTS}',
                            attachLog: true
                        )
                    }
                }
            }
        }
        
        // ====================================================================
        // STAGE 8: POST-DEPLOYMENT MONITORING
        // ====================================================================
        stage('Post-Deployment Monitoring') {
            when {
                anyOf {
                    branch 'main'
                    expression { return params.DEPLOYMENT_ENV == 'production' }
                }
            }
            steps {
                script {
                    echo "📊 Monitoring production for 5 minutes..."
                    
                    sshagent(credentials: ['production-ssh-key']) {
                        sh '''
                            for i in {1..5}; do
                                echo "Health check $i/5..."
                                ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                    'cd /opt/edms-production-* && ./scripts/health-check.sh --quick' || exit 1
                                
                                if [ $i -lt 5 ]; then
                                    sleep 60
                                fi
                            done
                            
                            echo "✅ System stable after 5 minutes"
                            
                            # Generate final report
                            ssh ${PRODUCTION_USER}@${PRODUCTION_HOST} \
                                'cd /opt/edms-production-* && ./scripts/health-check.sh --report'
                            
                            # Download final report
                            scp ${PRODUCTION_USER}@${PRODUCTION_HOST}:/opt/edms-production-*/health-report-*.html \
                                ./production-final-health-report.html || true
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: 'production-final-*.html',
                        allowEmptyArchive: true
                    )
                }
            }
        }
    }
    
    post {
        always {
            echo "Pipeline execution completed"
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: '**/*.tar.gz', type: 'INCLUDE'],
                    [pattern: '**/node_modules', type: 'INCLUDE']
                ]
            )
        }
        success {
            echo "✅ Pipeline completed successfully"
        }
        failure {
            echo "❌ Pipeline failed"
        }
        unstable {
            echo "⚠️ Pipeline completed with warnings"
        }
    }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

def notifySlack(String message, String color = 'good') {
    if (env.SLACK_WEBHOOK) {
        slackSend(
            color: color,
            message: message,
            channel: '#deployments',
            tokenCredentialId: 'slack-token'
        )
    }
}

def createGitHubRelease() {
    if (env.GITHUB_TOKEN) {
        sh """
            curl -X POST \
                -H "Authorization: token ${GITHUB_TOKEN}" \
                -H "Content-Type: application/json" \
                https://api.github.com/repos/YOUR_ORG/YOUR_REPO/releases \
                -d '{
                    "tag_name": "v${BUILD_NUMBER}",
                    "name": "Release v${BUILD_NUMBER}",
                    "body": "Deployment from commit ${GIT_COMMIT_SHORT}\\n\\n${GIT_COMMIT_MSG}",
                    "draft": false,
                    "prerelease": false
                }'
        """
    }
}
