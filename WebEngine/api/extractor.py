"""变量提取器 - 支持多种提取方式"""
import re
import json
import xml.etree.ElementTree as ET


class VariableExtractor:
    """变量提取器"""
    
    def extract(self, extract_rules, response_data):
        """
        根据规则提取变量
        :param extract_rules: 提取规则字典
        :param response_data: 响应数据
        :return: 提取的变量字典
        """
        result = {}
        for variable_name, rule in extract_rules.items():
            try:
                value = self.extract_single(rule, response_data)
                if value is not None:
                    result[variable_name] = value
            except Exception as e:
                print(f"提取变量 {variable_name} 失败: {e}")
        return result
    
    def extract_single(self, rule, response_data):
        """
        提取单个变量
        :param rule: 提取规则
        :param response_data: 响应数据
        :return: 提取的值
        """
        extract_type = rule.get("type", "jsonpath")
        expression = rule.get("expression", "")
        
        if extract_type == "jsonpath":
            body = response_data.get("body", {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    return None
            return self.extract_jsonpath(body, expression)
        
        elif extract_type == "response_json":
            body = response_data.get("body", {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    return None
            return self.extract_jsonpath(body, expression)
        
        elif extract_type == "response_text":
            body = response_data.get("body", "")
            if isinstance(body, dict):
                body = json.dumps(body, ensure_ascii=False)
            return self.extract_regex(str(body), expression)
        
        elif extract_type == "response_xml":
            body = response_data.get("body", "")
            if isinstance(body, dict):
                body = json.dumps(body, ensure_ascii=False)
            return self.extract_xml(str(body), expression)
        
        elif extract_type == "response_header":
            headers = response_data.get("headers", {})
            return self.extract_header(headers, expression)
        
        elif extract_type == "response_cookie":
            headers = response_data.get("headers", {})
            return self.extract_cookie(headers, expression)
        
        elif extract_type == "regex":
            body = response_data.get("body", "")
            if isinstance(body, dict):
                body = json.dumps(body, ensure_ascii=False)
            return self.extract_regex(str(body), expression)
        
        elif extract_type == "header":
            headers = response_data.get("headers", {})
            return headers.get(expression)
        
        else:
            return None
    
    def extract_jsonpath(self, data, expression):
        """
        JSONPath 提取
        :param data: 数据
        :param expression: JSONPath 表达式
        :return: 提取的值
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
                    # 支持通配符 [*]
                    if part == "*":
                        return current
                    return None
            else:
                return None
        
        return current
    
    def extract_regex(self, text, pattern):
        """
        正则提取
        :param text: 文本
        :param pattern: 正则表达式
        :return: 提取的值
        """
        if not pattern:
            return None
        
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # 如果有分组，返回第一个分组
            if match.groups():
                return match.group(1)
            return match.group(0)
        
        return None
    
    def extract_xml(self, xml_text, xpath_expression):
        """
        XML XPath 提取
        :param xml_text: XML 文本
        :param xpath_expression: XPath 表达式
        :return: 提取的值
        """
        if not xpath_expression:
            return None
        
        try:
            root = ET.fromstring(xml_text)
            # 简单的 XPath 支持
            # 例如: /root/data/token 或 ./data/token
            parts = xpath_expression.strip("/").split("/")
            current = root
            
            for part in parts:
                if part == "." or part == "":
                    continue
                # 查找子元素
                found = current.find(part)
                if found is not None:
                    current = found
                else:
                    return None
            
            return current.text
        except ET.ParseError:
            # 如果不是有效的 XML，尝试用正则提取
            return self.extract_regex(xml_text, xpath_expression)
        except Exception as e:
            print(f"XML 提取失败: {e}")
            return None
    
    def extract_header(self, headers, header_name):
        """
        响应头提取
        :param headers: 响应头字典
        :param header_name: 头部名称
        :return: 提取的值
        """
        if not header_name:
            return None
        
        # 不区分大小写查找
        header_name_lower = header_name.lower()
        for key, value in headers.items():
            if key.lower() == header_name_lower:
                return value
        
        return None
    
    def extract_cookie(self, headers, cookie_name):
        """
        Cookie 提取
        :param headers: 响应头字典
        :param cookie_name: Cookie 名称
        :return: 提取的值
        """
        if not cookie_name:
            return None
        
        # 获取 Set-Cookie 头
        set_cookie = headers.get("set-cookie", "")
        if not set_cookie:
            set_cookie = headers.get("Set-Cookie", "")
        
        if not set_cookie:
            return None
        
        # 解析 Cookie
        # 格式: name=value; name2=value2
        cookies = set_cookie.split(";")
        for cookie in cookies:
            cookie = cookie.strip()
            if "=" in cookie:
                name, value = cookie.split("=", 1)
                if name.strip() == cookie_name:
                    return value.strip()
        
        # 也检查多个 Set-Cookie
        cookies_list = headers.get("set-cookie", [])
        if isinstance(cookies_list, list):
            for cookie_header in cookies_list:
                if cookie_name in cookie_header:
                    match = re.search(rf'{cookie_name}=([^;]+)', cookie_header)
                    if match:
                        return match.group(1)
        
        return None


def replace_variables(text, variables):
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


def replace_variables_in_dict(data, variables):
    """
    替换字典中的变量
    :param data: 数据字典
    :param variables: 变量字典
    :return: 替换后的字典
    """
    if not data or not variables:
        return data
    
    if isinstance(data, str):
        return replace_variables(data, variables)
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = replace_variables_in_dict(value, variables)
        return result
    
    if isinstance(data, list):
        return [replace_variables_in_dict(item, variables) for item in data]
    
    return data
