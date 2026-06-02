"""接口测试执行器 - 支持数据驱动"""
import time
import json
import os
import httpx
from WebEngine.api.assertions import AssertionEngine
from WebEngine.api.extractor import VariableExtractor, replace_variables_in_dict
from tools.redis_publisher import redis_pub, device_id
from common.data_parser import parse_data_file


class ApiRunner:
    """接口测试执行器"""
    
    def __init__(self, config):
        """
        初始化执行器
        :param config: 配置信息
        """
        self.record_id = config.get("record_id")
        self.env_config = config.get("env_config", {})
        self.scenario = config.get("scenario")
        self.cases = config.get("cases", [])
        self.variables = {}
        self.assertion_engine = AssertionEngine()
        self.extractor = VariableExtractor()
        self.results = []
        
        # 初始化变量
        self._init_variables()
    
    def _init_variables(self):
        """初始化变量"""
        # 环境变量
        if self.env_config:
            self.variables.update(self.env_config.get("variables", {}))
            if "base_url" in self.env_config:
                self.variables["base_url"] = self.env_config["base_url"]
        
        # 场景变量
        if self.scenario:
            self.variables.update(self.scenario.get("variables", {}))
    
    def run(self):
        """
        串行执行所有用例
        :return: 执行结果
        """
        start_time = time.time()
        total = len(self.cases)
        success = 0
        fail = 0
        error = 0
        skip = 0
        
        self._log("info", f"开始执行接口测试，共 {total} 个用例")
        
        for i, case in enumerate(self.cases):
            self._log("info", f"执行用例 [{i+1}/{total}]: {case.get('name')}")
            
            # 检查是否有数据源配置
            data_source = case.get("data_source", {})
            if data_source and data_source.get("file_path"):
                # 数据驱动执行
                case_results = self.run_case_with_data(case, data_source)
                for result in case_results:
                    self.results.append(result)
                    if result["status"] == "success":
                        success += 1
                    elif result["status"] == "fail":
                        fail += 1
                    else:
                        error += 1
            else:
                # 普通执行
                try:
                    result = self.run_case(case)
                    self.results.append(result)
                    
                    if result["status"] == "success":
                        success += 1
                        self._log("info", f"用例 {case.get('name')} 执行成功")
                    elif result["status"] == "fail":
                        fail += 1
                        self._log("error", f"用例 {case.get('name')} 断言失败")
                    else:
                        error += 1
                        self._log("error", f"用例 {case.get('name')} 执行异常: {result.get('error_message')}")
                
                except Exception as e:
                    error += 1
                    result = {
                        "case_detail_id": case.get("case_detail_id"),
                        "case_id": case.get("case_id"),
                        "status": "error",
                        "request_data": {},
                        "response_data": {},
                        "assertions_result": [],
                        "extract_result": {},
                        "duration": 0,
                        "error_message": str(e)
                    }
                    self.results.append(result)
                    self._log("error", f"用例 {case.get('name')} 执行异常: {str(e)}")
        
        duration = time.time() - start_time
        
        self._log("info", f"接口测试执行完成，耗时 {duration:.2f}s，成功 {success}，失败 {fail}，错误 {error}")
        
        return {
            "record_id": self.record_id,
            "status": "success" if fail == 0 and error == 0 else "fail",
            "total": total,
            "success": success,
            "fail": fail,
            "error": error,
            "skip": skip,
            "duration": duration,
            "results": self.results
        }
    
    def run_case_with_data(self, case, data_source):
        """
        使用数据驱动执行用例
        :param case: 用例配置
        :param data_source: 数据源配置
        :return: 执行结果列表
        """
        results = []
        file_path = data_source.get("file_path")
        file_type = data_source.get("file_type", "csv")
        encoding = data_source.get("encoding", "utf-8")
        
        # 读取数据文件
        if not os.path.exists(file_path):
            self._log("error", f"数据文件不存在: {file_path}")
            return [{
                "case_detail_id": case.get("case_detail_id"),
                "case_id": case.get("case_id"),
                "status": "error",
                "request_data": {},
                "response_data": {},
                "assertions_result": [],
                "extract_result": {},
                "duration": 0,
                "error_message": f"数据文件不存在: {file_path}"
            }]
        
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            data_rows = parse_data_file(file_content, file_type, encoding)
        except Exception as e:
            self._log("error", f"读取数据文件失败: {str(e)}")
            return [{
                "case_detail_id": case.get("case_detail_id"),
                "case_id": case.get("case_id"),
                "status": "error",
                "request_data": {},
                "response_data": {},
                "assertions_result": [],
                "extract_result": {},
                "duration": 0,
                "error_message": f"读取数据文件失败: {str(e)}"
            }]
        
        self._log("info", f"数据驱动执行，共 {len(data_rows)} 条数据")
        
        for i, row in enumerate(data_rows):
            self._log("info", f"执行第 {i+1}/{len(data_rows)} 条数据")
            
            # 将行数据合并到变量中
            case_copy = case.copy()
            case_copy["variables"] = {**case.get("variables", {}), **row}
            
            try:
                result = self.run_case(case_copy)
                result["data_index"] = i
                result["data_row"] = row
                results.append(result)
                
                if result["status"] == "success":
                    self._log("info", f"第 {i+1} 条数据执行成功")
                elif result["status"] == "fail":
                    self._log("error", f"第 {i+1} 条数据断言失败")
                else:
                    self._log("error", f"第 {i+1} 条数据执行异常: {result.get('error_message')}")
            
            except Exception as e:
                results.append({
                    "case_detail_id": case.get("case_detail_id"),
                    "case_id": case.get("case_id"),
                    "status": "error",
                    "data_index": i,
                    "data_row": row,
                    "request_data": {},
                    "response_data": {},
                    "assertions_result": [],
                    "extract_result": {},
                    "duration": 0,
                    "error_message": str(e)
                })
                self._log("error", f"第 {i+1} 条数据执行异常: {str(e)}")
        
        return results
    
    def run_case(self, case):
        """
        执行单个用例
        :param case: 用例配置
        :return: 执行结果
        """
        case_detail_id = case.get("case_detail_id")
        request_config = case.get("request", {})
        case_variables = case.get("variables", {})
        extract_rules = case.get("extract", {})
        assertions = case.get("assertions", [])
        
        # 合并变量
        current_variables = {**self.variables, **case_variables}
        
        # 变量替换
        method = request_config.get("method", "GET")
        url = self._replace_variables(request_config.get("url", ""), current_variables)
        headers = replace_variables_in_dict(request_config.get("headers", {}), current_variables)
        body_type = request_config.get("body_type", "none")
        body = replace_variables_in_dict(request_config.get("body", {}), current_variables)
        
        # 构建完整 URL
        if not url.startswith(("http://", "https://")):
            base_url = current_variables.get("base_url", "")
            if base_url:
                url = f"{base_url}{url if url.startswith('/') else '/' + url}"
        
        # 发送请求
        request_data = {
            "method": method,
            "url": url,
            "headers": headers,
            "body_type": body_type,
            "body": body
        }
        
        response_data = {}
        duration = 0
        error_message = ""
        
        try:
            start_time = time.time()
            response = self._send_request(method, url, headers, body_type, body)
            duration = int((time.time() - start_time) * 1000)
            
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": self._parse_response_body(response)
            }
        
        except httpx.TimeoutException:
            error_message = "请求超时"
            return {
                "case_detail_id": case_detail_id,
                "case_id": case.get("case_id"),
                "status": "error",
                "request_data": request_data,
                "response_data": response_data,
                "assertions_result": [],
                "extract_result": {},
                "duration": duration,
                "error_message": error_message
            }
        
        except Exception as e:
            error_message = str(e)
            return {
                "case_detail_id": case_detail_id,
                "case_id": case.get("case_id"),
                "status": "error",
                "request_data": request_data,
                "response_data": response_data,
                "assertions_result": [],
                "extract_result": {},
                "duration": duration,
                "error_message": error_message
            }
        
        # 提取变量
        extract_result = self.extractor.extract(extract_rules, response_data)
        
        # 更新全局变量
        self.variables.update(extract_result)
        
        # 筛选需要保存到环境的变量
        env_variables = {}
        for var_name, rule in extract_rules.items():
            if rule.get("save_to_env") and var_name in extract_result:
                env_variables[var_name] = extract_result[var_name]
        
        # 执行断言
        assertions_result = self.assertion_engine.run_assertions(assertions, response_data, duration)
        
        # 判断用例状态
        all_passed = all(r.get("pass", False) for r in assertions_result) if assertions_result else True
        status = "success" if all_passed else "fail"
        
        return {
            "case_detail_id": case_detail_id,
            "case_id": case.get("case_id"),
            "status": status,
            "request_data": request_data,
            "response_data": response_data,
            "assertions_result": assertions_result,
            "extract_result": extract_result,
            "env_variables": env_variables,
            "duration": duration,
            "error_message": error_message
        }
    
    def _send_request(self, method, url, headers, body_type, body):
        """
        发送 HTTP 请求
        :param method: 请求方法
        :param url: 请求 URL
        :param headers: 请求头
        :param body_type: 请求体类型
        :param body: 请求体
        :return: 响应对象
        """
        with httpx.Client(timeout=60.0, verify=False) as client:
            kwargs = {
                "method": method,
                "url": url,
                "headers": headers
            }
            
            if body_type == "json" and body:
                kwargs["json"] = body
            elif body_type == "form-data" and body:
                kwargs["data"] = body
            elif body_type == "raw" and body:
                kwargs["content"] = str(body)
            
            return client.request(**kwargs)
    
    def _parse_response_body(self, response):
        """
        解析响应体
        :param response: 响应对象
        :return: 解析后的响应体
        """
        try:
            return response.json()
        except:
            return response.text
    
    def _replace_variables(self, text, variables):
        """
        替换字符串中的变量
        :param text: 包含变量的字符串
        :param variables: 变量字典
        :return: 替换后的字符串
        """
        if not text or not variables:
            return text
        
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            if placeholder in str(text):
                text = str(text).replace(placeholder, str(value))
        
        return text
    
    def _log(self, level, message):
        """
        推送日志
        :param level: 日志级别
        :param message: 日志消息
        """
        import json
        log_data = json.dumps({
            "type": "log",
            "level": level.upper(),
            "message": message
        }, ensure_ascii=False)
        redis_pub.publish_log(log_data)
