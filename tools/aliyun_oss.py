import oss2
import settings


def upload_oss(filename, file_bytes: bytes):
    """OSS配置项"""
    auth = oss2.Auth(**settings.OSS_CONFIG)
    bucket = oss2.Bucket(auth, settings.OOS_UPLOAD.get('endpoint'), settings.OOS_UPLOAD.get('bucket_name'))
    res = bucket.put_object(filename, file_bytes)
    if res.status == 200:
        return res.resp.response.url
    else:
        return None
