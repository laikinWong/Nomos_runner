import signal
import sys
from tools.mq_consumer import MQConsumer
from tools.redis_publisher import redis_pub
import settings
import requests
from threading import Thread

device_id = settings.DEVICE_ID


class Node:
    register_node_url = settings.REGISTER_NODE_URL

    def __init__(self):
        # 注册节点
        self.register_node()
        # 创建消费者
        self.consumer = MQConsumer()

    def register_node(self):
        """注册节点"""
        print("--------------开始注册执行设备-----------------")
        response = requests.post(self.register_node_url, json=settings.DEVICE)
        if response.status_code == 200:
            print(f'用户设备{device_id}已经上线！')
        else:
            print(f'用户设备{device_id}注册失败！错误信息：{response.text}')
            # 退出程序
            sys.exit(0)
        print('设备注册结果：', response.text)

    def start(self):
        """启动节点"""
        # 发布节点状态
        redis_pub.publish_node_state(device_id, '在线')
        # 发布节点屏幕画面
        Thread(target=redis_pub.publish_node_screen_view, args=(device_id,)).start()
        # 启动消费者
        self.consumer.main()

    def stop(self):
        """关闭节点"""
        try:
            # 关闭 RabbitMQ 连接
            self.consumer.stop()
        except Exception as e:
            print(f"关闭RabbitMQ连接时出错: {e}")
        
        try:
            # 设置节点状态为已停止
            redis_pub.publish_node_state(device_id, '离线')
            # 清理设备执行日志
            redis_pub.clear_history(device_id)
            # 关闭 Redis 连接
            redis_pub.close()
        except Exception as e:
            print(f"关闭Redis连接时出错: {e}")
        
        print("-------------节点关闭，清理资源完毕-----------------")
        # 退出程序
        sys.exit(0)

    def handle_exit(self, signum, frame):
        """处理节点退出信号并执行清理"""
        # 只处理SIGINT（Ctrl+C），忽略SIGTERM
        if signum == signal.SIGINT:
            print(f"收到退出信号{signum}，开始清理...")
            self.stop()
        else:
            # 忽略SIGTERM信号
            pass


def main():
    node = Node()
    # 绑定信号处理函数，确保节点能够优雅退出
    signal.signal(signal.SIGTERM, node.handle_exit)
    signal.signal(signal.SIGINT, node.handle_exit)
    # 启动节点并开始任务监听
    node.start()


if __name__ == '__main__':
    main()
