import json
import pika
from pika.exceptions import AMQPConnectionError
import time
from WebEngine.keyword.runner import Runner
from WebEngine.api.runner import ApiRunner
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
            self.channel.queue_declare(queue=settings.DEVICE_ID, durable=True)
            # 获取当前设备专属队列的消息
            self.channel.basic_consume(queue=settings.DEVICE_ID, on_message_callback=self.run_test, auto_ack=True)
            # 声明公共队列并获取消息
            self.channel.queue_declare(queue=settings.MQ_CONFIG.get('queue'), durable=True)
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
            
            # 判断测试类型
            test_type = datas.get("type", "ui_test")
            
            if test_type == "api_test":
                # 接口测试
                self.run_api_test(datas)
            else:
                # UI 测试
                self.run_ui_test(datas)
            
            # 确认消息已经处理
            # channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print("节点执行测试计划报错啦:", e)
        finally:
            # 暂停推流
            settings.START_STREAM = False
            # 清理日志
            redis_pub.clear_history(device_id)
    
    def run_ui_test(self, datas):
        """执行 UI 测试"""
        env_config = datas.get("env_config")
        run_suite = datas.get("run_suite")
        # 执行测试用例
        runner = Runner(env_config, run_suite)
        result = runner.run()
        # 保存测试结果
        db = None
        try:
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
        finally:
            if db:
                db.close()
    
    def run_api_test(self, datas):
        """执行接口测试"""
        try:
            runner = ApiRunner(datas)
            result = runner.run()
            # 保存测试结果
            self.save_api_result(result)
        except Exception as e:
            print("接口测试执行失败:", e)
    
    def save_api_result(self, result):
        """保存接口测试结果"""
        db = db_client.DB()
        try:
            record_id = result.get("record_id")
            
            # 更新执行记录
            sql = """
                UPDATE api_run_record
                SET status = %s, success = %s, fail = %s, error = %s, duration = %s
                WHERE id = %s
            """
            params = (
                result.get("status", "success"),
                result.get("success", 0),
                result.get("fail", 0),
                result.get("error", 0),
                result.get("duration", 0),
                record_id
            )
            db.execute(sql, params)
            print(f"更新接口执行记录 {record_id} 完成")
            
            # 收集所有需要保存到环境的变量
            all_env_variables = {}
            
            # 更新用例执行详情
            for case_result in result.get("results", []):
                case_detail_id = case_result.get("case_detail_id")
                if case_detail_id:
                    sql = """
                        UPDATE api_case_run_detail
                        SET status = %s, request_data = %s, response_data = %s,
                            assertions_result = %s, extract_result = %s, 
                            duration = %s, error_message = %s
                        WHERE id = %s
                    """
                    params = (
                        case_result.get("status", "error"),
                        json.dumps(case_result.get("request_data", {}), ensure_ascii=False),
                        json.dumps(case_result.get("response_data", {}), ensure_ascii=False),
                        json.dumps(case_result.get("assertions_result", []), ensure_ascii=False),
                        json.dumps(case_result.get("extract_result", {}), ensure_ascii=False),
                        case_result.get("duration", 0),
                        case_result.get("error_message", ""),
                        case_detail_id
                    )
                    db.execute(sql, params)
                    print(f"更新用例执行详情 {case_detail_id} 完成")
                    
                    # 收集 env_variables
                    env_vars = case_result.get("env_variables", {})
                    if env_vars:
                        all_env_variables.update(env_vars)
            
            # 如果有需要保存到环境的变量，更新环境
            if all_env_variables:
                self.save_env_variables(record_id, all_env_variables, db)
        finally:
            db.close()
    
    def save_env_variables(self, record_id, env_variables, db):
        """保存提取的变量到环境"""
        try:
            # 获取执行记录关联的用例，再获取用例关联的环境ID
            sql = """
                SELECT t2.env_id 
                FROM api_case_run_detail t1
                JOIN api_testcase t2 ON t1.case_id = t2.id
                WHERE t1.record_id = %s AND t2.env_id IS NOT NULL
                LIMIT 1
            """
            db.execute(sql, (record_id,))
            record = db.fetch_one()
            
            if record and record.get("env_id"):
                env_id = record["env_id"]
                # 获取当前环境的全局变量
                sql = "SELECT global_vars FROM environment WHERE id = %s"
                db.execute(sql, (env_id,))
                env = db.fetch_one()
                
                if env:
                    current_vars = env.get("global_vars") or {}
                    if isinstance(current_vars, str):
                        current_vars = json.loads(current_vars)
                    
                    # 合并变量
                    current_vars.update(env_variables)
                    
                    # 更新环境
                    sql = "UPDATE environment SET global_vars = %s WHERE id = %s"
                    db.execute(sql, (json.dumps(current_vars, ensure_ascii=False), env_id))
                    print(f"更新环境 {env_id} 的变量: {env_variables}")
        except Exception as e:
            print(f"保存环境变量失败: {e}")

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
        
        # 计算各项指标
        new_success = task_data['success'] + result.get("success", 0)
        new_fail = task_data['fail'] + result.get("fail", 0)
        new_error = task_data['error'] + result.get("error", 0)
        new_skip = task_data['skip'] + result.get("skip", 0)
        new_run_all = task_data['run_all'] + len(result.get("run_cases"))
        new_no_run = task_data['no_run'] + result.get("no_run", 0)
        new_duration = task_data['duration'] + result.get("duration", 0)
        
        # 计算通过率
        total_executed = new_success + new_fail + new_error + new_skip
        if total_executed > 0:
            pass_rate = round(new_success / total_executed * 100, 2)
        else:
            pass_rate = 0
        
        # 判断状态
        if task_data['all'] == new_run_all + new_no_run:
            status = "执行完成"
        else:
            status = "执行中"
        
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
            skip = %s,
            duration = %s,
            pass_rate = %s
            WHERE id=%s  
        """
        
        # 执行sql修改测试计划的执行记录
        res = db.execute(sql, (status, new_run_all, new_no_run,
                               new_success, new_fail, new_error,
                               new_skip, new_duration, pass_rate, task_record_id))
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
