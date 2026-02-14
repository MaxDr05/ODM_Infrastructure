pipeline {
    agent any

    environment {
        // 宿主机路径(docker run用)
        HOST_LOG_PATH = "/Users/calvin/code/logs"
        HOST_REPORT_PATH = "/Users/calvin/code/reports"

        // Jenkins 容器内挂载路径（cp / python 用）
        JENKINS_MOUNT_LOGS = "/var/odm_logs"
        JENKINS_MOUNT_REPORTS = "/var/odm_reports"

        // 镜像定义
        RUNNER_IMAGE = "odm_device_runner:v1.0"
        ANALYZER_IMAGE = "odm_quality_guard:v1.1"

        // 真机配置
        TARGET_SERIAL = "D3H7N17B25007986"

        // 虚拟设备配置
        VIRTUAL_DEVICE = "MOCK_CALVIN"
    }

    stages {
        stage('Clean Workspace') {
            steps {
                // 【架构修正 1】使用 Docker 清理宿主机目录
                // 为什么？因为 Jenkins 容器内部可能没有权限，或者找不到 /Users/calvin 这个路径
                // 启动一个 alpine 容器，挂载同样的路径，进去执行 rm，这是最稳妥的
                sh """
                    docker run --rm \
                    -v ${HOST_LOG_PATH}:/app/log \
                    -v ${HOST_REPORT_PATH}:/app/report \
                    alpine sh -c "rm -f /app/log/*.log && rm -rf /app/report/*"
                """

            }
        }
        stage('Initialize DB'){
            steps{
                script{
                    echo "Initialize Database Entry..."
                    sh "python3 db_manager.py init --batch_id ${env.BUILD_TAG}"
                }
            }
        }

        stage('Distributed Testing') {
            // 容错点 E: 全局超时熔断
            // 冒烟测试一般 5 分钟，我们给 10 分钟 Buffer。超过直接 Kill。
            options {
                timeout(time: 10, unit: 'MINUTES')
            }
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
                // 注意：这里的前提是Python 代码得改为扫描这个目录
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
            script{
                echo "💾 Syncing Test Results to Database..."
                // Jenkins 容器看不见 /Users/calvin，但它看得见 /var/odm_reports
                sh "mkdir -p report"
                sh "mkdir -p raw-logs"
                // 使用 Jenkins 容器内的挂载路径进行拷贝
                sh "cp -r ${JENKINS_MOUNT_REPORTS}/. report/"
                sh "cp -r ${JENKINS_MOUNT_LOGS}/. raw-logs/"

                sh "python3 db_manager.py import --batch_id ${env.BUILD_TAG} --file_path ./report/summary.json"
            }
            allure includeProperties: false, jdk: '', results: [[path: "report"]]
            // 永久存档原始日志 (Artifacts)
            // 这样你可以在 Jenkins 每次构建的详情页右上角，下载到这次的所有 log
            archiveArtifacts artifacts: 'raw-logs/*.log', allowEmptyArchive: true
        }
    }
}