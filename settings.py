import uuid
import platform
import socket
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 后端服务运行地址
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8001')

# 消息队列配置
MQ_CONFIG = {
    "host": os.getenv('MQ_HOST', '127.0.0.1'),
    "port": int(os.getenv('MQ_PORT', 5672)),
    'DEFAULT_USERNAME': os.getenv('MQ_USERNAME', 'guest'),
    'DEFAULT_PASSWORD': os.getenv('MQ_PASSWORD', 'guest'),
    "queue": os.getenv('MQ_QUEUE', 'fastapi')
}

# 数据库配置
DATABASE = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here'),
    'database': os.getenv('DB_NAME', 'fastapi')
}

# redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', '127.0.0.1'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 1)),
    'password': os.getenv('REDIS_PASSWORD', '')
}

# 腾讯云COS配置
COS_CONFIG = {
    'region': os.getenv('COS_REGION', 'ap-guangzhou'),
    'secret_id': os.getenv('COS_SECRET_ID', 'your_secret_id_here'),
    'secret_key': os.getenv('COS_SECRET_KEY', 'your_secret_key_here'),
    'bucket': os.getenv('COS_BUCKET', 'your_bucket_here'),
}


def get_name():
    """
    获取设备名称
    :return:
    """
    system = platform.system()
    if system == "Linux":
        return "无头模式"
    elif system in ["Windows", "Darwin"]:
        return "执行设备"

DEVICE_ID = str(uuid.getnode())
# 执行器设备信息
DEVICE = {
    "id": DEVICE_ID,
    "name": get_name(),
    "system": platform.system(),
    "username": 'test',
    "status": '在线',
    "ip": socket.gethostbyname(socket.gethostname()),
    "version": platform.version(),
    "hostname": socket.gethostname()
}

# 注册节点的地址
REGISTER_NODE_URL = f'{BASE_URL}/device'

# 服务器的带宽，单位/M，根据服务器性能如实配置，带宽越高，监控画面越清晰
BANDWIDTH = 1

# 是否开始推流
START_STREAM = False

# 性能优化配置
# 心跳上报间隔（秒）
HEARTBEAT_INTERVAL = 30

# 截屏配置
SCREENSHOT_IDLE_INTERVAL = 50  # 空闲时截屏间隔（单位：0.1秒）
SCREENSHOT_ACTIVE_INTERVAL = 10  # 执行任务时截屏间隔（单位：0.1秒）
SCREENSHOT_CACHE_TTL = 300  # 截屏缓存过期时间（秒）

# 数据库连接配置
DB_POOL_SIZE = 5  # 数据库连接池大小
DB_CONNECT_TIMEOUT = 10  # 数据库连接超时时间（秒）

# Redis连接配置
REDIS_MAX_CONNECTIONS = 10  # Redis最大连接数
REDIS_SOCKET_TIMEOUT = 5  # Redis socket超时时间（秒）
REDIS_CONNECT_TIMEOUT = 5  # Redis连接超时时间（秒）
