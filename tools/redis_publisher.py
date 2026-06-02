import time
import threading
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
    
    def __init__(self):
        # 使用连接池管理连接，避免连接泄漏
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_CONFIG['host'],
            port=settings.REDIS_CONFIG['port'],
            db=settings.REDIS_CONFIG['db'],
            password=settings.REDIS_CONFIG['password'],
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT
        )
        self.redis_cli = redis.StrictRedis(connection_pool=self.pool)
        # 停止事件，用于控制屏幕截图线程
        self._stop_event = threading.Event()
        self._screen_thread = None

    def clear_history(self, device_id):
        """清空历史日志记录"""
        try:
            self.redis_cli.delete(f"{device_id}:history_logs")
        except Exception as e:
            print(f"清空历史日志失败: {e}")

    def publish_log(self, log):
        """发布日志"""
        try:
            self.redis_cli.publish(f"{device_id}:log", log)
            self.redis_cli.rpush(f"{device_id}:history_logs", log)
        except Exception as e:
            print(f"发布日志失败: {e}")

    def publish_node_screen_view(self, device_id):
        """发布节点屏幕快照"""
        print("-------------开始发布节点屏幕快照-----------------")
        i = 0
        # 根据带宽设置截屏间隔
        if settings.BANDWIDTH < 2:
            idle_interval = settings.SCREENSHOT_IDLE_INTERVAL  # 5秒更新一次（空闲时）
            active_interval = settings.SCREENSHOT_ACTIVE_INTERVAL  # 1秒更新一次（执行任务时）
        elif settings.BANDWIDTH < 4:
            idle_interval = 30  # 3秒更新一次
            active_interval = 5  # 0.5秒更新一次
        else:
            idle_interval = 20  # 2秒更新一次
            active_interval = 2  # 0.2秒更新一次
        
        while not self._stop_event.is_set():
            try:
                # 判断是否开始执行任务
                if settings.START_STREAM:
                    encoded_data = self.get_screen_capture()
                    if encoded_data:
                        self.redis_cli.publish(f"{device_id}:screen", encoded_data)
                    time.sleep(0.1 * active_interval)
                elif i >= idle_interval:
                    # 没有任务执行，按空闲间隔更新画面
                    encoded_data = self.get_screen_capture()
                    if encoded_data:
                        self.redis_cli.publish(f"{device_id}:screen", encoded_data)
                        # 缓存画面
                        self.redis_cli.set(f'{device_id}:cached_image', encoded_data, ex=settings.SCREENSHOT_CACHE_TTL)
                    i = 0
                    time.sleep(0.1)
                else:
                    time.sleep(0.1)
                    i += 1
            except Exception as e:
                print(f"屏幕快照发布异常: {e}")
                time.sleep(1)  # 异常时等待1秒再重试

    def stop_screen_view(self):
        """停止屏幕截图线程"""
        self._stop_event.set()
        if self._screen_thread and self._screen_thread.is_alive():
            self._screen_thread.join(timeout=5)

    def publish_node_state(self, device_id, state):
        """发布节点状态"""
        if state in ['在线', '离线', '任务执行中']:
            try:
                self.redis_cli.publish(f"{device_id}:state", state)
            except Exception as e:
                print(f"发布节点状态失败: {e}")

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
            # 如果截屏失败，返回None而不是空白图片，减少内存消耗
            print(f"截屏失败: {e}")
            return None
        
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
        try:
            self.stop_screen_view()
            self.redis_cli.close()
            self.pool.disconnect()
        except Exception as e:
            print(f"关闭Redis连接失败: {e}")

# 创建发布者
redis_pub = RedisPublisher()
