import json
import pika
from pika.exceptions import AMQPConnectionError
import time
from WebEngine.keyword.runner import Runner
import settings
from tools import db_client
from tools.redis_publisher import redis_pub, device_id
from settings import MQ_CONFIG


class MQConsumer:

    def __init__(self):
        self.connection = None
        self.channel = None
        self.connected = False
        self.connect()

    def connect(self):
        """连接到 RabbitMQ，并初始化频道"""
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=settings.MQ_CONFIG.get('host'),
                port=settings.MQ_CONFIG.get('port'),
                credentials=pika.credentials.PlainCredentials(username=MQ_CONFIG.get('DEFAULT_USERNAME'),
                                                              password=MQ_CONFIG.get('DEFAULT_PASSWORD')),
                heartbeat=600,  # 设置心跳检测
                blocked_connection_timeout=300,  # 设置阻塞连接超时时间
                )
            )
            # 连接到通道
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.DEVICE_ID, )
            # 获取当前设备专属队列的消息
            self.channel.basic_consume(queue=settings.DEVICE_ID, on_message_callback=self.run_test, auto_ack=True)
            # 获取公共队列中的消息
            self.channel.basic_consume(queue=settings.MQ_CONFIG.get('queue'), on_message_callback=self.run_test, auto_ack=True)
            print("成功连接到RabbitMQ")
            self.connected = True
        except pika.exceptions.AMQPConnectionError as e:
            print(f"连接RabbitMQ失败: {e}")
            print("请确保RabbitMQ服务已启动。Runner将无法接收测试任务。")
            self.connected = False

    def run_test(self, channel, method, properties, body):
        """执行测试计划"""
        # 开始推流
        settings.START_STREAM = True
        try:
            datas = json.loads(body.decode())
            env_config = datas.get("env_config")
            run_suite = datas.get("run_suite")
            # 执行测试用例
            runner = Runner(env_config, run_suite)
            result = runner.run()
            # 保存测试结果
            db = db_client.DB()
            if run_suite.get("task_record_id"):
                self.save__task_result(run_suite.get("task_record_id"), result, db)
                self.save__suite_result(run_suite.get("suite_record_id"), result, db)
            elif run_suite.get("suite_record_id"):
                self.save__suite_result(run_suite.get("suite_record_id"), result, db)
            else:
                if len(result['run_cases']):
                    self.save_case_result(result['run_cases'][0], db)
                elif len(result['no_run_cases']):
                    self.save_case_result(result['no_run_cases'][0], db)
            # 确认消息已经处理
            # channel.basic_ack(delivery_tag=method.delivery_tag)
            db.close()
        except Exception as e:
            print("节点执行测试计划报错啦:", e)
        finally:
            # 暂停推流
            settings.START_STREAM = False
            # 清理日志
            redis_pub.clear_history(device_id)

    def main(self):
        """启动消费者，处理消息"""
        if not self.connected:
            print("未连接到RabbitMQ，无法启动消费者")
            return
            
        while True:
            try:
                self.channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker:
                print("连接被RabbitMQ服务器关闭，尝试重新连接...")
                self.connect()
                if not self.connected:
                    break
            except pika.exceptions.StreamLostError:
                print("连接丢失，尝试重新连接...")
                self.connect()
                if not self.connected:
                    break
            except KeyboardInterrupt:
                print("手动中断，停止消费者")
                self.stop()
                break

    def stop(self):
        """关闭RabbitMQ连接"""
        try:
            if self.connection and self.connection.is_open:
                if self.channel:
                    self.channel.stop_consuming()
                self.connection.close()
        except Exception as e:
            print(f"关闭RabbitMQ连接时出错: {e}")

    def save__task_result(self, task_record_id, result, db):
        """保存任务测试执行的结果"""
        # 通过任务执行记录的id，查找到当前这条任务记录的数据
        query_sql = "SELECT * FROM task_record WHERE id=%s"
        # 执行查询的sql
        db.execute(query_sql, (task_record_id,))
        # 获取查询结果
        task_data = db.fetch_one()
        # 准备sql
        sql = """
            UPDATE task_record
            SET 
            status = %s,
            run_all = %s,
            no_run = %s,
            success = %s,
            fail = %s,
            error = %s,
            skip = %s
            WHERE id=%s  
        """
        params = {
            "run_all": task_data['run_all'] + len(result.get("run_cases")),
            "no_run": task_data['no_run'] + result.get("no_run", 0),
            "success": task_data['success'] + result.get("success", 0),
            "fail": task_data['fail'] + result.get("fail", 0),
            "error": task_data['error'] + result.get("error", 0),
            "skip": task_data['skip'] + result.get("skip", 0),
        }
        if task_data['all'] == params["run_all"] + params["no_run"]:
            params["status"] = "执行完成"
        else:
            params["status"] = "执行中"
        # 执行sql修改测试计划的执行记录
        res = db.execute(sql, (params.get("status"), params.get("run_all"), params.get("no_run"),
                               params.get("success"), params.get("fail"), params.get("error"),
                               params.get("skip"), task_record_id))
        print("执行任务记录中的数据修改结果：", res)

    def save__suite_result(self, suite_record_id, result, db):
        """保存测试套件执行的结果"""
        # 准备sql
        sql = """
        UPDATE suite_record
        SET 
        status = %s,
        run_all = %s,
        no_run = %s,
        success = %s,
        fail = %s,
        error = %s,
        skip = %s,
        duration = %s,
        suite_log = %s,
        pass_rate = %s
        WHERE id=%s  
        """
        # 计算执行的通过率
        if result['all'] > 0:
            pass_rate = round((result.get("success") + result.get("skip")) / result.get("all"), 2) * 100
        else:
            pass_rate = 0
        params = {
            "status": "执行完成",
            "run_all": len(result.get("run_cases")),
            "no_run": result.get("no_run", 0),
            "success": result.get("success", 0),
            "fail": result.get("fail", 0),
            "error": result.get("error", 0),
            "skip": result.get("skip", 0),
            "duration": result.get("duration", 0),
            "suite_log": json.dumps(result.get("suite_log"), ensure_ascii=False),
            "pass_rate": pass_rate,
        }
        res = db.execute(sql, (params.get("status"), params.get("run_all"), params.get("no_run"),
                               params.get("success"), params.get("fail"), params.get("error"),
                               params.get("skip"), params.get("duration"), params.get("suite_log"),
                               params.get("pass_rate"), suite_record_id))
        print("套件执行记录sql执行结果:", res)
        # 保存套件中用例执行的结果
        for case_result in result['run_cases']:
            self.save_case_result(case_result, db)
        for case_result in result['no_run_cases']:
            self.save_case_result(case_result, db)

    def save_case_result(self, result, db):
        """保存测试用例执行的结果"""
        # 准备sql
        sql = 'UPDATE case_record SET status = %s,run_info = %s WHERE id=%s'
        # 执行sql
        params = (result.get('status'), json.dumps(result, ensure_ascii=False), result.get('record_id'))
        res = db.execute(sql, params)
        print(f"用例{result.get('id')}执行保存结果:", res)
