pipeline {
    agent any

    environment {
        // 宿主机路径
        HOST_LOG_PATH = "/Users/calvin/code/logs"
        HOST_REPORT_PATH = "/Users/calvin/code/reports"

        // 镜像定义
        RUNNER_IMAGE = "odm_device_runner:v1.0"
        ANALYZER_IMAGE = "odm_quality_guard:v1.0"

        // 服务名
        SCHEDULER_SERVICE = "scheduler"

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

                // 清理 Jenkins 自己的 workspace (为了下一次构建干净)
                cleanWs()
            }
        }

        stage('Run Device Tests') {
            steps{
                script{
                    echo "🚀 Launching Scheduler Service..."
                    // [核心动作] 使用 Docker Compose 启动调度器
                    // --rm: 跑完就销毁容器
                    // 这里的 logs 目录已经在 docker-compose.yml 里映射好了
                    sh "docker-compose run --rm ${SCHEDULER_SERVICE}"
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
                sh "mkdir -p allure-results"
                sh "mkdir -p raw-logs"
                //  把宿主机产生的数据（Reports + Logs）拷贝回 Jenkins Workspace
                sh "cp -r /var/odm_reports/. allure-results/"
                sh "cp -r /var/odm_logs/. raw-logs/"
            }
            allure includeProperties: false, jdk: '', results: [[path: "allure-results"]]
            // 永久存档原始日志 (Artifacts)
            // 这样你可以在 Jenkins 每次构建的详情页右上角，下载到这次的所有 log
            archiveArtifacts artifacts: 'raw-logs/*.log', allowEmptyArchive: true
        }
    }
}