import time
from WebEngine.core.basecase import BaseCase
from WebEngine.core.logger import LoggerHandler
from tools.cos_upload import upload_cos as upload_oss


class TestResult:
    """测试结果"""

    def __init__(self, suite, config):
        self.suite = suite  # 执行的测试套件数据
        self.test_env = config  # 测试环境配置
        self.all = len(suite.get('cases', []))
        self.success = 0  # 成功数量
        self.fail = 0  # 失败数量
        self.error = 0  # 错误数量
        self.skip = 0  # 跳过的数量
        self.no_run = 0  # 未执行数量
        self.start_time = None  # 开始执行时间
        self.duration = None  # 执行时长
        self.suite_log = []  # 套件执行日志
        self.run_cases = []  # 执行用例详情
        self.no_run_cases = []  # 未执行用例详情

    def add_success(self, _case, _log, images):
        """
        :param _case: 执行成功的用来
        :param _log:  用例的执行日志
        :param images: 用例执行结果的截图列表
        :return:
        """
        self.success += 1
        _case['status'] = 'success'
        _case['log_data'] = _log
        _case['images'] = images if isinstance(images, list) else [images] if images else []
        _case['img'] = _case['images'][0] if _case['images'] else None
        self.run_cases.append(_case)

    def add_fail(self, _case, _log, images):
        """
        :param _case: 执行失败的用例
        :param _log: 失败的用例日志
        :param images: 执行结果的截图列表
        :return:
        """
        self.fail += 1
        _case['status'] = 'fail'
        _case['log_data'] = _log
        _case['images'] = images if isinstance(images, list) else [images] if images else []
        _case['img'] = _case['images'][0] if _case['images'] else None
        self.run_cases.append(_case)

    def add_error(self, _case, _log, images):
        """
        :param _case: 执行错误的用例
        :param _log: 错误的用例日志
        :param images: 执行结果的截图列表
        :return:
        """
        self.error += 1
        _case['status'] = 'error'
        _case['log_data'] = _log
        _case['images'] = images if isinstance(images, list) else [images] if images else []
        _case['img'] = _case['images'][0] if _case['images'] else None
        self.run_cases.append(_case)

    def add_skip(self, _case):
        """
        :param _case: 跳过的用例
        :return:
        """
        self.skip += 1
        _case['status'] = 'skip'
        self.run_cases.append(_case)

    def add_no_run(self, _case):
        """
        :param _case: 未执行的用例
        :return:
        """
        self.no_run += 1
        _case['status'] = 'no_run'
        self.no_run_cases.append(_case)

    def suite_run_start(self):
        """套件开始执行"""
        self.start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self._time = time.time()

    def suite_run_end(self, suite_log):
        """测试套件执行结束"""
        # 获取运行的总时长
        self.duration = time.time() - self._time
        # 保存测试套件的日志
        self.suite_log = suite_log
        # 判断执行的用例总数，如果不相等，则说明有用例未执行
        if not (self.all == self.success + self.fail + self.error + self.skip):
            # 获取所有已经执行过的用例总
            run_case_ids = [i.get('id') for i in self.run_cases]
            # 遍历套件中的所有用例
            for case_ in self.suite.get('cases', []):
                # 如果用例不在执行过的用例列表中，则说明该用例未执行
                if case_.get('id') not in run_case_ids:
                    # 记录一条未执行的用例
                    self.add_no_run(case_)

    def get_result(self):
        """获取执行结果的方法"""
        return {
            'suite_id': self.suite.get('id'),
            'suite_name': self.suite.get('name'),
            'all': self.all,
            'success': self.success,
            'fail': self.fail,
            'error': self.error,
            'skip': self.skip,
            'no_run': self.no_run,
            'start_time': self.start_time,
            'duration': self.duration,
            'suite_log': self.suite_log,
            'run_cases': self.run_cases,
            'no_run_cases': self.no_run_cases,
            'test_env': self.test_env
        }


class Runner:
    """测试执行器"""

    def __init__(self, config, suite):
        """
        :param config: 执行的环境配置
        :param suite: 执行的测试套件数据
        """
        self.config = config
        self.suite = suite
        self.browser = None
        self.context = None
        self.page = None
        # 创建一个记录测试套件的日志的对象
        self.log = LoggerHandler()
        self.result = TestResult(suite, config)

    def run(self):
        """执行的入口函数"""
        # 开始执行测试套件, 记录开始执行时间
        self.result.suite_run_start()
        try:
            # 执行测试套件的公共前置步骤证
            self.run_suite_setup()
            # 执行测试套件中的用例
            self.run_suite()
        except Exception as e:
            self.log.error('执行测试套件出错啦,本次执行结束!')
            self.log.error(e)
        finally:
            if self.browser:
                # 关闭浏览器
                self.browser.close()
        # 测试套件执行, 记录执行结束时间
        self.result.suite_run_end(getattr(self.log, 'log_data'))
        # 返回测试执行的结果
        return self.result.get_result()

    def run_suite_setup(self):
        """执行测试套件的公共前置步骤"""
        try:
            if self.suite.get("setup_step"):
                self.log.info('====================检测到测试套件的公共前置步骤，准备开始执行！====================')
                suite_setup_steps = self.suite.get("setup_step")
                run = BaseCase(self.config, self.log)
                for step in suite_setup_steps:
                    self.log.info('执行前置步骤：', step['desc'])
                    run.perform(step)
                # 保存前置步骤创建的浏览器对象
                self.browser = run.browser
                self.context = run.context
                self.page = run.page
            else:
                self.log.info('没有检测到测试套件的公共前置步骤！')
        except Exception as e:
            self.log.error('执行测试套件的公共前置步骤失败，本次执行结束！')
            self.log.error(e)

    def run_suite(self):
        """执行测试套件"""
        # 遍历用例，执行用例
        cases = self.suite.get("cases", [])
        if not cases:
            self.log.info('当前测试套件中，没有检测到测试用例！')
            return
        # 遍历套件中所有的用例
        for case_ in cases:
            # 判断用例是否需要跳过执行
            if case_.get('skip'):
                self.log.info(f"测试用例【{case_.get('name')}】，跳过执行！")
                self.result.add_skip(case_)
            else:
                self.run_case(case_)

    def run_case(self, case_):
        """执行单条用例"""
        # 获取用例的执行步骤
        steps = case_.get("steps", [])
        # 记录单条用例执行结果的日志对象
        case_log = LoggerHandler()
        run = BaseCase(self.config, case_log, self.browser, self.context, self.page)
        self.log.info(f"==============开始执行测试用例：【{case_.get('name')}】===============")
        try:
            for step in steps:
                # 执行步骤
                case_log.info("正在执行用例步骤：", step.get('desc'))
                run.perform(step)
        except AssertionError as e:
            # 保存页面的截图
            img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', run.page.screenshot())
            self.result.add_fail(case_, getattr(case_log, 'log_data'), [img])
            self.log.error(f"用例【{case_.get('name')}】断言失败，失败原因：{e}")
        except Exception as e:
            # 保存页面的截图
            img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', run.page.screenshot())
            self.result.add_error(case_, getattr(case_log, 'log_data'), [img])
            self.log.error(f"用例【{case_.get('name')}】执行出现错误，错误原因：{e}")
        else:
            # 保存页面的截图
            img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', run.page.screenshot())
            self.result.add_success(case_, getattr(case_log, 'log_data'), [img])
            self.log.info(f"==============测试用例：【{case_.get('name')}】，执行通过！==============")

        # 保存前置步骤创建的浏览器对象
        self.browser = run.browser
        self.context = run.context
        self.page = run.page
