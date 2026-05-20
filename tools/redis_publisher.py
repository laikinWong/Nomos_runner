import time
from PIL import ImageGrab
import io
import base64
import redis
import settings

"""
设备状态：{device_id}:state
设备快照：{device_id}:screen
设备日志：{device_id}:log
设备历史日志: {device_id}:history_logs
"""
device_id = settings.DEVICE_ID


class RedisPublisher:
    """发布者"""
    redis_cli = redis.StrictRedis(host=settings.REDIS_CONFIG['host'],
                                  port=settings.REDIS_CONFIG['port'],
                                  db=settings.REDIS_CONFIG['db'],
                                  password=settings.REDIS_CONFIG['password'],
                                  decode_responses=True)

    def clear_history(self, device_id):
        """清空历史日志记录"""
        self.redis_cli.delete(f"{device_id}:history_logs")

    def publish_log(self, log):
        """发布日志"""
        self.redis_cli.publish(f"{device_id}:log", log)
        self.redis_cli.rpush(f"{device_id}:history_logs", log)

    def publish_node_screen_view(self, device_id):
        """发布节点屏幕快照"""
        print("-------------开始发布节点屏幕快照-----------------")
        i = 0
        while True:
            # 判断是否开始执行任务
            if settings.START_STREAM:
                encoded_data = self.get_screen_capture()
                self.redis_cli.publish(f"{device_id}:screen", encoded_data)
            elif i == 100:
                # 没有任务执行，10秒更新一次画面
                encoded_data = self.get_screen_capture()
                self.redis_cli.publish(f"{device_id}:screen", encoded_data)
                # 缓存画面
                self.redis_cli.set(f'{device_id}:cached_image', encoded_data)
                i = 0
            # 每隔0.1秒发布一次
            time.sleep(0.1)
            i += 1

    def publish_node_state(self, device_id, state):
        """发布节点状态"""
        if state in ['在线', '离线', '任务执行中']:
            self.redis_cli.publish(f"{device_id}:state", state)

    @staticmethod
    def get_screen_capture():
        """
        获取屏幕快照并转换为Base64编码消息
        如果想要高清画面就不要对页面进行压缩，前提是服务器的带宽4M以上，带宽太低，图片体积又大，画面就会又延迟，而且卡顿
        :return:
        """
        try:
            screenshot = ImageGrab.grab()
        except Exception as e:
            # 如果截屏失败，返回一个空白图片
            print(f"截屏失败: {e}")
            from PIL import Image
            screenshot = Image.new('RGB', (800, 600), color='black')
        
        with io.BytesIO() as output:
            if settings.BANDWIDTH < 2:
                # -----------带宽差的用这个(小于等于2M)----------------
                width, height = screenshot.size
                new_size = (width // 2, height // 2)  # 示例: 缩小到原始尺寸的一半
                screenshot = screenshot.resize(new_size)
                # 转换为WEBP格式，减少传输大小
                screenshot.save(output, format='WEBP', quality=30, optimize=True)
            elif 2 < settings.BANDWIDTH < 4:
                # -----------带宽差的用这个(大于2M，用这个)----------------
                screenshot.save(output, format='WEBP', quality=50, optimize=True)
            else:
                # -----------带宽差的用这个(带宽大于4M，用这个)----------------
                screenshot.save(output, format='WEBP', optimize=True)
            screen_data = output.getvalue()
        encoded_data = base64.b64encode(screen_data).decode('utf-8')
        return encoded_data

    def close(self):
        """关闭连接"""
        self.redis_cli.close()

# 创建发布者
redis_pub = RedisPublisher()
