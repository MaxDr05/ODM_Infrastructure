pipeline {
    agent any

    environment {
        // 宿主机路径 (给 Docker run 挂载用的)
        HOST_LOG_PATH = "/Users/calvin/code/logs"
        HOST_REPORT_PATH = "/Users/calvin/code/reports"

        // Jenkins 容器内部路径 (给 Allure 插件读取用的)
        JENKINS_INSIDE_REPORT_PATH = "/var/odm_reports"

        RUNNER_IMAGE = "odm_device_runner:v1.0"
        ANALYZER_IMAGE = "odm_quality_guard:v1.0"

        TARGET_SERIAL = "jenkins_report_test_001"
        LOG_FILENAME = "device_jenkins_report_test_001.log"
    }

    stages {
        stage('Clean Workspace') {
            steps {
                sh "rm -f ${HOST_LOG_PATH}/${LOG_FILENAME}"
                // 清理旧的报告文件
                sh "rm -rf ${HOST_REPORT_PATH}/*"
            }
        }

        stage('Run Monkey Test') {
            steps {
                sh """
                    docker run --rm \
                    -e SERIAL=${TARGET_SERIAL} \
                    -v ${HOST_LOG_PATH}:/app/log \
                    ${RUNNER_IMAGE}
                """
            }
        }

        stage('Quality Gate Analysis') {
            steps {
                // 注意：这里挂载了 /app/report (单数)
                sh """
                    docker run --rm \
                    -v ${HOST_LOG_PATH}:/app/log \
                    -v ${HOST_REPORT_PATH}:/app/report \
                    ${ANALYZER_IMAGE} \
                    /app/log/${LOG_FILENAME}
                """
            }
        }
    }

    post {
        always {
            // 1. 在 Workspace 下创建一个存放原始数据的目录 (标准命名: allure-results)
            sh "mkdir -p allure-results"

            // 2. 把外部挂载点的数据复制进来
            // cp -r: 递归复制
            // /var/odm_reports/.: 复制文件夹下的所有内容，而不包含文件夹本身
            sh "cp -r /var/odm_reports/. allure-results/"

            // 3. 告诉插件去哪里找数据 (使用相对路径)
            allure includeProperties: false,
                   jdk: '',
                   results: [[path: "allure-results"]]
        }
    }
}