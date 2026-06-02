"""断言引擎"""
import re
import json
import xml.etree.ElementTree as ET


class AssertionEngine:
    """断言引擎"""
    
    def run_assertions(self, assertions, response_data, duration):
        """
        执行所有断言
        :param assertions: 断言规则列表
        :param response_data: 响应数据
        :param duration: 响应时间(ms)
        :return: 断言结果列表
        """
        results = []
        for assertion in assertions:
            result = self.run_assertion(assertion, response_data, duration)
            results.append(result)
        return results
    
    def run_assertion(self, assertion, response_data, duration):
        """
        执行单个断言
        :param assertion: 断言规则
        :param response_data: 响应数据
        :param duration: 响应时间(ms)
        :return: 断言结果
        """
        assertion_type = assertion.get("type", "")
        operator = assertion.get("operator", "eq")
        expected = assertion.get("expected", "")
        expression = assertion.get("expression", "")
        
        try:
            if assertion_type == "status_code":
                actual = response_data.get("status_code", 0)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "pass": pass_result,
                    "description": f"状态码 {actual} {operator} {expected}"
                }
            
            elif assertion_type == "jsonpath":
                body = response_data.get("body", {})
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except:
                        return {
                            "type": assertion_type,
                            "pass": False,
                            "description": f"响应体不是有效的 JSON"
                        }
                actual = self.evaluate_jsonpath(body, expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"JSON {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_json":
                body = response_data.get("body", {})
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except:
                        return {
                            "type": assertion_type,
                            "pass": False,
                            "description": f"响应体不是有效的 JSON"
                        }
                actual = self.evaluate_jsonpath(body, expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"JSON {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_text":
                body = response_data.get("body", "")
                if isinstance(body, dict):
                    body = json.dumps(body, ensure_ascii=False)
                actual = self.evaluate_regex(str(body), expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"Text 匹配 {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_xml":
                body = response_data.get("body", "")
                if isinstance(body, dict):
                    body = json.dumps(body, ensure_ascii=False)
                actual = self.evaluate_xml(str(body), expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"XML {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_header":
                headers = response_data.get("headers", {})
                actual = self.get_header(headers, expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"Header {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_cookie":
                headers = response_data.get("headers", {})
                actual = self.get_cookie(headers, expression)
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"Cookie {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "response_time":
                pass_result = self.compare(duration, operator, int(expected) if expected else 0)
                return {
                    "type": assertion_type,
                    "pass": pass_result,
                    "description": f"响应时间 {duration}ms {operator} {expected}ms"
                }
            
            elif assertion_type == "header":
                headers = response_data.get("headers", {})
                actual = headers.get(expression, "")
                pass_result = self.compare(actual, operator, expected)
                return {
                    "type": assertion_type,
                    "expression": expression,
                    "pass": pass_result,
                    "description": f"响应头 {expression} = {actual}, {operator} {expected}"
                }
            
            elif assertion_type == "body":
                body = response_data.get("body", "")
                if isinstance(body, dict):
                    body = json.dumps(body, ensure_ascii=False)
                pass_result = self.compare(str(body), operator, str(expected))
                return {
                    "type": assertion_type,
                    "pass": pass_result,
                    "description": f"响应体 {operator} {expected}"
                }
            
            else:
                return {
                    "type": assertion_type,
                    "pass": False,
                    "description": f"未知的断言类型: {assertion_type}"
                }
        
        except Exception as e:
            return {
                "type": assertion_type,
                "pass": False,
                "description": f"断言执行异常: {str(e)}"
            }
    
    def compare(self, actual, operator, expected):
        """
        比较操作
        :param actual: 实际值
        :param operator: 操作符
        :param expected: 预期值
        :return: 比较结果
        """
        # 类型转换
        if isinstance(expected, str):
            try:
                expected = int(expected)
            except ValueError:
                try:
                    expected = float(expected)
                except ValueError:
                    pass
        
        if isinstance(actual, str):
            try:
                actual = int(actual)
            except ValueError:
                try:
                    actual = float(actual)
                except ValueError:
                    pass
        
        if operator == "eq":
            return actual == expected
        elif operator == "ne":
            return actual != expected
        elif operator == "gt":
            return float(actual) > float(expected)
        elif operator == "lt":
            return float(actual) < float(expected)
        elif operator == "gte":
            return float(actual) >= float(expected)
        elif operator == "lte":
            return float(actual) <= float(expected)
        elif operator == "contains":
            return str(expected) in str(actual)
        elif operator == "not_contains":
            return str(expected) not in str(actual)
        elif operator == "empty":
            return not actual or actual == "" or actual == [] or actual == {}
        elif operator == "not_empty":
            return actual and actual != "" and actual != [] and actual != {}
        elif operator == "match":
            return bool(re.match(str(expected), str(actual)))
        elif operator == "not_match":
            return not bool(re.match(str(expected), str(actual)))
        else:
            return False
    
    def evaluate_jsonpath(self, data, expression):
        """
        简单的 JSONPath 解析
        :param data: 数据
        :param expression: JSONPath 表达式
        :return: 解析结果
        """
        if not expression:
            return data
        
        # 移除 $ 前缀
        if expression.startswith("$"):
            expression = expression[1:]
        
        # 分割路径
        parts = expression.replace("[", ".").replace("]", "").split(".")
        parts = [p for p in parts if p]
        
        current = data
        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return None
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return None
                except ValueError:
                    return None
            else:
                return None
        
        return current
    
    def evaluate_regex(self, text, pattern):
        """
        正则表达式匹配
        :param text: 文本
        :param pattern: 正则表达式
        :return: 匹配结果
        """
        if not pattern:
            return None
        
        match = re.search(pattern, text, re.DOTALL)
        if match:
            if match.groups():
                return match.group(1)
            return match.group(0)
        
        return None
    
    def evaluate_xml(self, xml_text, xpath_expression):
        """
        XML XPath 解析
        :param xml_text: XML 文本
        :param xpath_expression: XPath 表达式
        :return: 解析结果
        """
        if not xpath_expression:
            return None
        
        try:
            root = ET.fromstring(xml_text)
            parts = xpath_expression.strip("/").split("/")
            current = root
            
            for part in parts:
                if part == "." or part == "":
                    continue
                found = current.find(part)
                if found is not None:
                    current = found
                else:
                    return None
            
            return current.text
        except ET.ParseError:
            return self.evaluate_regex(xml_text, xpath_expression)
        except Exception:
            return None
    
    def get_header(self, headers, header_name):
        """
        获取响应头
        :param headers: 响应头字典
        :param header_name: 头部名称
        :return: 头部值
        """
        if not header_name:
            return None
        
        header_name_lower = header_name.lower()
        for key, value in headers.items():
            if key.lower() == header_name_lower:
                return value
        
        return None
    
    def get_cookie(self, headers, cookie_name):
        """
        获取 Cookie
        :param headers: 响应头字典
        :param cookie_name: Cookie 名称
        :return: Cookie 值
        """
        if not cookie_name:
            return None
        
        set_cookie = headers.get("set-cookie", "")
        if not set_cookie:
            set_cookie = headers.get("Set-Cookie", "")
        
        if not set_cookie:
            return None
        
        cookies = set_cookie.split(";")
        for cookie in cookies:
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                if name.strip() == cookie_name:
                    return value.strip()
        
        cookies_list = headers.get("set-cookie", [])
        if isinstance(cookies_list, list):
            for cookie_header in cookies_list:
                if cookie_name in cookie_header:
                    match = re.search(rf'{cookie_name}=([^;]+)', cookie_header)
                    if match:
                        return match.group(1)
        
        return None
