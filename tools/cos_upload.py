from qcloud_cos import CosConfig, CosS3Client
import settings
from datetime import datetime
from urllib.parse import quote


def upload_cos(filename, file_bytes: bytes):
    """
    上传文件到腾讯云COS
    :param filename: 文件名
    :param file_bytes: 文件内容(bytes)
    :return: 文件访问URL
    """
    config = CosConfig(
        Region=settings.COS_CONFIG['region'],
        SecretId=settings.COS_CONFIG['secret_id'],
        SecretKey=settings.COS_CONFIG['secret_key'],
    )
    client = CosS3Client(config)
    
    bucket = settings.COS_CONFIG['bucket']
    # 按日期组织目录
    today = datetime.now().strftime('%Y%m%d')
    # 对文件名进行URL编码，处理中文字符
    encoded_filename = quote(filename, safe='')
    key = f"test-results/{today}/{encoded_filename}"
    
    try:
        response = client.put_object(
            Bucket=bucket,
            Body=file_bytes,
            Key=key,
        )
        # 生成带签名的临时URL（有效期7天）
        url = client.get_presigned_url(
            Method='GET',
            Bucket=bucket,
            Key=key,
            Expired=604800  # 7天 = 7 * 24 * 60 * 60
        )
        return url
    except Exception as e:
        print(f"上传COS失败: {e}")
        return None
