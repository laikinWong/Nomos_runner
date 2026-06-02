import pymysql.cursors
import settings


class DB:
    """mysql数据库操作类"""
    def __init__(self):
        # 连接到数据库
        self.conn = pymysql.connect(
            host=settings.DATABASE.get('host'),
            port=settings.DATABASE.get('port'),
            user=settings.DATABASE.get('user'),
            password=settings.DATABASE.get('password'),
            database=settings.DATABASE.get('database'),
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=settings.DB_CONNECT_TIMEOUT,
            read_timeout=30,
            write_timeout=30
        )
        # 创建游标
        self.cursor = self.conn.cursor()

    def execute(self, sql, args=None):
        """执行sql"""
        try:
            # 执行sql，查询数据
            result = self.cursor.execute(sql, args)
            return result
        except Exception as e:
            # 如果出错，回滚事务
            try:
                self.conn.rollback()
            except Exception:
                pass
            print(f"SQL执行错误: {e}")
            return False

    def fetch_one(self):
        """获取一条数据"""
        try:
            # 获取一条数据
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(f"单条数据查询错误！错误为：{e}")
            return None

    def fetch_all(self):
        """获取所有数据"""
        try:
            # 获取所有数据
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"所有数据查询错误！错误为：{e}")
            return []

    def close(self):
        """关闭连接的方法"""
        try:
            # 判断游标对象是否存在
            if self.cursor is not None:
                # 关闭游标
                self.cursor.close()
        except Exception as e:
            print(f"关闭游标失败: {e}")
        
        try:
            # 判断数据库对象是否存在
            if self.conn is not None:
                # 关闭连接
                self.conn.close()
        except Exception as e:
            print(f"关闭数据库连接失败: {e}")
