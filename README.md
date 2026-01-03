# ODM Distributed Test System (Architecture PoC)

**基于 Docker 容器化的 Android 并行测试与日志分析基础设施**

> **Note to Reviewers**: 本项目为分布式测试系统的**核心架构原型 (Proof of Concept)**。它抽取了大规模 ODM 设备测试中的核心调度逻辑与容错机制，移除了复杂的 Web UI 与持久化存储层，旨在演示**容器隔离**、**并行编排**以及**流式日志分析**的设计模式。
### 核心组件仓库
本仓库 (`odm_infrastructure`) 是系统的**编排层**，底层依赖以下两个独立组件：

| 组件名称 | 仓库地址 | 职责 | 核心技术 |
| :--- | :--- | :--- | :--- |
| **执行器 (Runner)** | [**maxdr05/odm_device_runner**](https://github.com/maxdr05/odm_device_runner) | 负责 ADB 隔离、设备保活与测试注入。 | Docker, Shell, ADB |
| **分析器 (Guard)** | [**maxdr05/odm_quality_guard**](https://github.com/maxdr05/odm_quality_guard) | 负责流式日志分析与质量门禁判定。 | Python 3.10, Pytest, Generator |
---

## 1. 项目背景与设计目标

在 ODM（原始设计制造）设备测试中，面对数十台甚至上百台原型机，传统的串行测试或基于线程的并发测试往往面临以下痛点：

* **环境污染**：ADB 服务冲突，残留进程影响下一轮测试。
* **依赖地狱**：不同型号设备需要不同版本的测试工具链。
* **资源竞争**：多设备同时写入同一文件导致 IO 冲突。

本项目旨在通过**容器化 (Containerization)** 技术解决上述问题，实现一个轻量级、高可控的自动化测试基础设施。

## 2. 核心架构 (Architecture)

系统采用 **Jenkins (Orchestrator)** + **Docker (Worker)** 的主从架构，数据流转基于 **Fan-out / Fan-in** 模式。

```mermaid
graph TD
    Jenkins[Jenkins Pipeline] -->|Fan-out: Parallel Stages| DockerRunner
    
    subgraph "Docker Host"
        DockerRunner[Runner Containers (xN)] -->|Execute| ADB[Real Devices / Emulators]
        DockerRunner -->|Write Logs| Volume[Shared Volume / Host Path]
    end
    
    Volume -->|Read Logs| LogAnalyzer[Analyzer Container]
    LogAnalyzer -->|Generate| Allure[Allure Report]
    
    Jenkins -->|Fan-in: Aggregation| LogAnalyzer

```

### 关键模块

* **Orchestrator (Jenkins)**: 负责任务分发与生命周期管理。利用 `Jenkinsfile` 的 `parallel` 语法实现并发控制。
* **Runner (ODM_Device_Runner)**: 基于 `debian-slim` 构建的无状态容器。内置 ADB 与容错脚本，负责单台设备的测试执行与 Logcat 采集。
* **Analyzer (ODM_Quality_Guard)**: 基于 `Python 3.10` 的无状态分析器。采用生成器模式（Generator）处理大文件日志，产出结构化测试报告。
* **Infrastructure**: 纯 Docker Compose 编排，无 K8s 依赖，适合中小规模（<20台设备）的敏捷部署。

## 3. 工程决策与取舍 (Design Trade-offs)

### ✅ 选择 Jenkins Pipeline 而非自研调度器

* **理由**：利用 Jenkins 成熟的 `Agent` 管理和 `Stage` 可视化，降低开发成本。通过 `parallel` 块即可实现进程级并发，无需在代码层处理复杂的线程锁。

### ✅ 选择 Docker Volume 挂载而非数据库

* **理由**：作为 MVP（最小可行性产品），直接操作文件系统是最直观的调试方式。
* **扩展性**：当前的 `load(logdir)` 接口已做抽象。若需上云，只需将底层的 `glob` 文件读取替换为 S3/OSS SDK 即可，业务逻辑层无需变动。

### ✅ 选择流式处理 (Yield) 而非一次性加载

* **场景**：ODM 压测日志通常在 500MB - 2GB 之间。
* **实现**：`FileLoader` 模块严格遵循 Python 生成器模式，确保内存占用保持在 O(1) 级别，防止在分析长稳测试（MTBF）日志时发生 OOM。

### ✅ 引入“预检机制 (Pre-flight Check)”

* **痛点**：ADB 经常出现 `offline` 或 `unauthorized` 状态，导致测试无效运行。
* **对策**：在 `entrypoint.sh` 中实现了严格的状态机检查。只有当设备状态明确为 `device` 且目标包已安装时，才会启动 Monkey 测试，否则直接 Fast Fail。

## 4. 已知限制 (Limitations)

鉴于本项目定位为架构演示，存在以下设计上的已知限制，暂未在当前版本解决：

1. **配置依赖**：
* 测试规则硬编码在代码/配置文件中，缺乏动态配置中心。
* *Future Work*: 引入 Consul 或简单的 API 服务下发规则。


2. **USB 物理限制**：
* 尽管软件架构支持无限扩展，但受限于宿主机的 USB 带宽和控制器，单节点建议挂载设备不超过 35 台。



## 5. 项目结构

```text
├── ODM_Device_Runner/       # [执行端]
│   ├── entrypoint.sh        # 核心：包含 ADB 守护进程与容错逻辑
│   └── Dockerfile           # 环境定义
├── ODM_Quality_Guard/       # [服务端/分析端]
│   ├── core/
│   │   ├── loader.py        # 内存安全的日志加载器 (Generator)
│   │   └── parse.py         # 规则引擎
│   └── tests/               # Pytest 测试用例集
├── odm_infrastructure/      # [基础设施]
│   ├── docker-compose.yml   # 容器编排
│   └── Jenkinsfile          # 流水线定义 (Parallel Pipeline)
└── README.md

```

## 6. 运行指南

### 前置条件

* Docker & Docker Compose
* Jenkins (支持 Docker Pipeline 插件)
* 至少一台 Android 设备开启 USB 调试

### 快速启动

1. **构建镜像**:
```bash
docker-compose build

```


2. **触发流水线**:
将项目接入 Jenkins，配置参数 `HOST_LOG_PATH` 指向宿主机挂载点。
3. **查看报告**:
Pipeline 执行结束后，通过 Allure 插件查看聚合后的测试结果。

---

> **Author**: [Calvin]
> **Role**: SDET / Automation Architect
> **Contact**: [qq603992850@gmail.com]