"""数据文件解析器 - 支持 CSV 和 Excel"""
import csv
import io
from typing import List, Dict, Any


def parse_csv(file_content: bytes, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """
    解析 CSV 文件内容
    :param file_content: 文件内容（bytes）
    :param file_encoding: 文件编码
    :return: 数据列表，每行为一个字典
    """
    try:
        text = file_content.decode(encoding)
    except UnicodeDecodeError:
        # 尝试其他编码
        text = file_content.decode("gbk")
    
    reader = csv.DictReader(io.StringIO(text))
    data = []
    for row in reader:
        # 去除键值的空格
        cleaned_row = {k.strip(): v.strip() if v else "" for k, v in row.items()}
        data.append(cleaned_row)
    
    return data


def parse_excel(file_content: bytes, sheet_name: str = None) -> List[Dict[str, Any]]:
    """
    解析 Excel 文件内容
    :param file_content: 文件内容（bytes）
    :param sheet_name: 工作表名称，默认为第一个工作表
    :return: 数据列表，每行为一个字典
    """
    try:
        import openpyxl
    except ImportError:
        raise ImportError("需要安装 openpyxl 库才能解析 Excel 文件: pip install openpyxl")
    
    wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
    
    if sheet_name:
        ws = wb[sheet_name]
    else:
        ws = wb.active
    
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    
    # 第一行作为表头
    headers = [str(h).strip() if h else f"column_{i}" for i, h in enumerate(rows[0])]
    
    data = []
    for row in rows[1:]:
        row_dict = {}
        for i, value in enumerate(row):
            if i < len(headers):
                row_dict[headers[i]] = str(value) if value is not None else ""
        data.append(row_dict)
    
    wb.close()
    return data


def parse_data_file(file_content: bytes, file_type: str, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """
    解析数据文件
    :param file_content: 文件内容（bytes）
    :param file_type: 文件类型（csv/xlsx/xls）
    :param encoding: 文件编码（仅 CSV 有效）
    :return: 数据列表
    """
    if file_type == "csv":
        return parse_csv(file_content, encoding)
    elif file_type in ("xlsx", "xls"):
        return parse_excel(file_content)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


def validate_data_source(data: List[Dict[str, Any]], required_columns: List[str] = None) -> Dict[str, Any]:
    """
    验证数据源
    :param data: 数据列表
    :param required_columns: 必需的列名
    :return: 验证结果
    """
    if not data:
        return {
            "valid": False,
            "message": "数据为空",
            "columns": [],
            "row_count": 0
        }
    
    columns = list(data[0].keys())
    
    if required_columns:
        missing_columns = [col for col in required_columns if col not in columns]
        if missing_columns:
            return {
                "valid": False,
                "message": f"缺少必需的列: {', '.join(missing_columns)}",
                "columns": columns,
                "row_count": len(data)
            }
    
    return {
        "valid": True,
        "message": "验证通过",
        "columns": columns,
        "row_count": len(data)
    }
