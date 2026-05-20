import time
from tools.redis_publisher import redis_pub


class LoggerHandler:

    def save_log(self, message, level):
        """
        日志保存的方法
        :param message: 日志的内容
        :param level: 日志级别
        :return:
        """
        # 获取当前时间
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # 拼接日志
        log = f"{now} {message}"
        # 判断是否存在log_data属性
        if not hasattr(self, "log_data"):
            # 如果不存在，则创建一个属性
            setattr(self, "log_data", [])
        # 将日志保存到log_data属性中
        getattr(self, "log_data").append((level, log))
        # 发布日志保存到订阅中心
        redis_pub.publish_log(f'【{level}】:{log}')
        # 控制台输出日志
        # print((level, log))

    def info(self, *args):
        """
        保存info级别的日志
        :param args: 日志内容
        :return:
        """
        message = " ".join([str(i) for i in args])
        self.save_log(message, "INFO")

    def error(self, *args):
        """
        保存error级别的日志
        :param args: 日志内容
        :return:
        """
        message = " ".join([str(i) for i in args])
        self.save_log(message, "ERROR")

    def warning(self, *args):
        """
        保存warning级别的日志
        :param args: 日志内容
        :return:
        """
        message = " ".join([str(i) for i in args])
        self.save_log(message, "WARNING")

    def debug(self, *args):
        """
        保存debug级别的日志
        :param args: 日志内容
        :return:
        """
        message = " ".join([str(i) for i in args])
        self.save_log(message, "DEBUG")

    def critical(self, *args):
        """
        保存critical级别的日志
        :param args: 日志内容
        :return:
        """
        message = " ".join([str(i) for i in args])
        self.save_log(message, "CRITICAL")
