pipeline {
    agent any

    environment {
        // 宿主机路径
        HOST_LOG_PATH = "/Users/calvin/code/logs"
        HOST_REPORT_PATH = "/Users/calvin/code/reports"

        // 镜像定义
        RUNNER_IMAGE = "odm_device_runner:v1.0"
        ANALYZER_IMAGE = "odm_quality_guard:v1.0"

        // 真机配置
        TARGET_SERIAL = "D3H7N17B25007986"

        // 虚拟设备配置
        VIRTUAL_DEVICE = "MOCK_CALVIN"
    }

    stages {
        stage('Clean Workspace') {
            steps {
                // 直接清理宿主机日志目录下的所有文件，不用一个一个删
                sh "rm -f ${HOST_LOG_PATH}/*.log"
                sh "rm -rf ${HOST_REPORT_PATH}/*"
            }
        }

        stage('Distributed Testing') {
            // 【修正 1】parallel 块结构
            parallel {
                stage('Real Steel') {
                    // 【修正 2】必须有 steps 块
                    steps {
                        sh """
                            docker run --rm \
                            -e SERIAL=${TARGET_SERIAL} \
                            -e ADB_SERVER_SOCKET=tcp:host.docker.internal:5037 \
                            -v ${HOST_LOG_PATH}:/app/log \
                            ${RUNNER_IMAGE}
                        """
                    }
                }

                stage('Virtual Warrior') {
                    steps {
                        sh """
                            docker run --rm \
                            -e SERIAL=${VIRTUAL_DEVICE} \
                            -e ADB_SERVER_SOCKET=tcp:host.docker.internal:5037 \
                            -v ${HOST_LOG_PATH}:/app/log \
                            ${RUNNER_IMAGE}
                        """
                    }
                }
            }
        }

        stage('Quality Gate Analysis') {
            steps {
                // 【修正 3】Fan-In 聚合分析
                // 不再传 specific filename，而是传目录 /app/log
                // 注意：这里的前提是你的 Python 代码得改为扫描这个目录
                sh """
                    docker run --rm \
                    -v ${HOST_LOG_PATH}:/app/log \
                    -v ${HOST_REPORT_PATH}:/app/report \
                    ${ANALYZER_IMAGE} \
                    /app/log
                """
            }
        }
    }

    post {
        always {
            sh "mkdir -p allure-results"
            sh "cp -r /var/odm_reports/. allure-results/"
            allure includeProperties: false, jdk: '', results: [[path: "allure-results"]]
        }
    }
}