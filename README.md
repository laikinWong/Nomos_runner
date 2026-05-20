# Nomos Runner

自动化测试执行节点，用于接收和执行 Web 自动化测试任务。

## 功能特性

- 设备注册与状态管理
- RabbitMQ 消息队列消费测试任务
- Redis 实时发布设备状态和屏幕画面
- 支持 Core 和 Keyword 两种测试模式
- 腾讯云 COS 文件上传

## 环境要求

- Python 3.9+
- RabbitMQ
- Redis
- MySQL

## 安装

```bash
# 克隆项目
git clone https://github.com/laikinWong/Nomos_runner.git
cd Nomos_runner

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

## 配置

在项目根目录创建 `.env` 文件，参考 `settings.py.example` 配置以下参数：

```env
# 后端服务地址
BASE_URL=http://127.0.0.1:8001

# 消息队列配置
MQ_HOST=127.0.0.1
MQ_PORT=5672
MQ_USERNAME=guest
MQ_PASSWORD=guest
MQ_QUEUE=fastapi

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fastapi

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=

# 腾讯云 COS 配置
COS_REGION=ap-guangzhou
COS_SECRET_ID=your_secret_id
COS_SECRET_KEY=your_secret_key
COS_BUCKET=your_bucket
```

## 运行

```bash
python3 main.py
```

按 `Ctrl+C` 可优雅退出。

## 项目结构

```
runner/
├── main.py              # 主程序入口
├── settings.py          # 配置文件
├── settings.py.example  # 配置示例
├── requirements.txt     # 依赖包
├── tools/               # 工具模块
│   ├── mq_consumer.py   # RabbitMQ 消费者
│   ├── redis_publisher.py # Redis 发布者
│   ├── cos_upload.py    # COS 文件上传
│   ├── db_client.py     # 数据库客户端
│   └── aliyun_oss.py    # 阿里云 OSS
└── WebEngine/           # Web 测试引擎
    ├── core/            # Core 模式
    ├── keyword/         # Keyword 模式
    └── tests/           # 测试用例
```

## License

MIT
