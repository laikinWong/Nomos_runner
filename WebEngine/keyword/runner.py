import asyncio
import sys
import time

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright
from tools.cos_upload import upload_cos as upload_oss
from WebEngine.keyword.basecase import BaseCase
from WebEngine.keyword.logger import LoggerHandler
def _log_storage_state(logger, state, label='storage_state'):
    if not state:
        logger.info(f'{label} 为空')
        return
    cookies = state.get('cookies', [])
    origins = state.get('origins', [])
    logger.info(f'{label} 已提取，cookies={len(cookies)} 条, origins={len(origins)} 条')
    for cookie in cookies:
        if isinstance(cookie, dict):
            logger.info(f'{label} cookie: name={cookie.get("name")}, domain={cookie.get("domain")}, path={cookie.get("path")}, expires={cookie.get("expires")}, httpOnly={cookie.get("httpOnly")}, secure={cookie.get("secure")}, sameSite={cookie.get("sameSite")}')
    for origin in origins:
        if isinstance(origin, dict):
            origin_url = origin.get('origin', '')
            local_storage = origin.get('localStorage') or {}
            local_keys = list(local_storage.keys()) if isinstance(local_storage, dict) else []
            logger.info(f'{label} origin: {origin_url}, localStorage keys={local_keys}')

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
        with sync_playwright() as pw:
            self.pw = pw
            try:
                # 执行测试套件的公共前置步骤证
                self.run_suite_setup()
                # 执行测试套件中的用例
                self.run_suite()
            except Exception as e:
                self.log.error('执行测试套件失败，本次执行结束！', e)
            finally:
                # 确保所有页面和上下文都被关闭
                try:
                    if self.page and not self.page.is_closed():
                        self.page.close()
                except Exception as e:
                    self.log.error(f'关闭页面失败: {e}')
                try:
                    if self.context:
                        self.context.close()
                except Exception as e:
                    self.log.error(f'关闭上下文失败: {e}')
                try:
                    if self.browser:
                        self.browser.close()
                except Exception as e:
                    self.log.error(f'关闭浏览器失败: {e}')
        # 测试套件执行, 记录执行结束时间
        self.result.suite_run_end(getattr(self.log, 'log_data'))
        # 返回测试执行的结果
        return self.result.get_result()

    def run_suite_setup(self):
        """执行测试套件的公共前置步骤"""
        self.setup_state = None
        self.setup_url = None
        try:
            if self.suite.get("setup_step"):
                self.log.info('===========检测到测试套件的公共前置步骤，准备开始执行！============')
                suite_setup_steps = self.suite.get("setup_step")
                run = BaseCase(self.pw, self.config, self.log)
                for step in suite_setup_steps:
                    self.log.info('执行前置步骤：', step['desc'])
                    run.perform(step)
                # 保存前置步骤结束时的页面URL
                if run.page and not run.page.is_closed():
                    self.setup_url = run.page.url
                    self.log.info(f'前置步骤结束时的页面URL: {self.setup_url}')
                # 提取前置步骤的登录态 (storage_state = cookies + localStorage)
                if run.context:
                    self.setup_state = run.context.storage_state()
                    _log_storage_state(self.log, self.setup_state, label='前置登录态')
                # 保存前置步骤创建的浏览器对象供后续复用
                self.browser = run.browser
                # 关闭前置步骤的页面和上下文，防止污染
                if run.context:
                    run.context.close()
                self.log.info('前置步骤执行完成，已提取登录态并关闭前置上下文')
            else:
                self.log.info('没有检测到测试套件的公共前置步骤！')
        except Exception as e:
            self.log.error('执行测试套件的公共前置步骤失败，本次执行结束！')
            self.log.error(e)
            # 确保浏览器被关闭
            if run.browser:
                try:
                    run.browser.close()
                except Exception:
                    pass
            raise e

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
        retry_count = int(self.config.get("retry_count", 0))
        
        for attempt in range(retry_count + 1):
            # 记录单条用例执行结果的日志对象
            case_log = LoggerHandler()
            case_context = None
            
            if attempt > 0:
                self.log.info(f"=============测试用例：【{case_.get('name')}】正在进行第 {attempt} 次重试==============")
            else:
                self.log.info(f"=============开始执行测试用例：【{case_.get('name')}】================")
            
            try:
                case_start_time = time.time()
                # 确保 browser 对象存在
                if not self.browser:
                    browser_type_obj = getattr(self.pw, self.config.get("browser_type", "chromium"))
                    headless = self.config.get("is_debug", False)
                    launch_args = ['--start-maximized'] if not headless else []
                    self.browser = browser_type_obj.launch(headless=headless, args=launch_args)

                # 为当前用例创建全新的、隔离的 Context
                context_args = {"no_viewport": True}
                # 如果有前置步骤的登录态，注入到新 context
                if hasattr(self, 'setup_state') and self.setup_state:
                    context_args["storage_state"] = self.setup_state
                    self.log.info(f'已注入登录态到用例上下文，cookies数量: {len(self.setup_state.get("cookies", []))}')
                case_context = self.browser.new_context(**context_args)
                case_page = case_context.new_page()
                
                # 如果有前置步骤的URL，自动导航到该URL
                if hasattr(self, 'setup_url') and self.setup_url:
                    case_page.goto(self.setup_url)
                    self.log.info(f'已自动导航到前置步骤页面: {self.setup_url}')

                run = BaseCase(self.pw, self.config, case_log, self.browser, case_context, case_page)
                self.log.info(f'当前用例环境 host={self.config.get("host")}')
                
                for step in steps:
                    # 执行步骤
                    case_log.info("正在执行用例步骤：", step.get('desc'))
                    run.perform(step)
                
                # 等待页面稳定后再截图
                try:
                    if run.page and not run.page.is_closed():
                        run.page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
                
                # 成功执行，保存截图
                img = None
                try:
                    if run.page and not run.page.is_closed():
                        img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', run.page.screenshot())
                except Exception as screenshot_err:
                    self.log.error(f"截图失败: {screenshot_err}")
                case_['duration'] = round(time.time() - case_start_time, 2)
                self.result.add_success(case_, getattr(case_log, 'log_data'), [img] if img else [])
                self.log.info(f"==============测试用例：【{case_.get('name')}】，执行通过！=================")
                break
                
            except AssertionError as e:
                if attempt < retry_count:
                    self.log.info(f"断言失败，准备重试...")
                    continue
                # 等待页面稳定后再截图
                try:
                    if case_context:
                        page = case_context.pages[0] if case_context.pages else None
                        if page and not page.is_closed():
                            page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    pass
                # 保存页面的截图
                img = None
                try:
                    if case_context:
                        page = case_context.pages[0] if case_context.pages else None
                        if page and not page.is_closed():
                            img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', page.screenshot())
                except Exception as screenshot_err:
                    self.log.error(f"截图失败: {screenshot_err}")
                case_['duration'] = round(time.time() - case_start_time, 2)
                self.result.add_fail(case_, getattr(case_log, 'log_data'), [img] if img else [])
                self.log.error(f"测试用例【{case_.get('name')}】断言失败，失败原因：{e}")
                break
                
            except Exception as e:
                if attempt < retry_count:
                    self.log.info(f"执行异常，准备重试... 异常信息: {e}")
                    continue
                # 等待页面稳定后再截图
                try:
                    if case_context:
                        page = case_context.pages[0] if case_context.pages else None
                        if page and not page.is_closed():
                            page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    pass
                # 保存页面的截图
                img = None
                try:
                    if case_context:
                        page = case_context.pages[0] if case_context.pages else None
                        if page and not page.is_closed():
                            img = upload_oss(f'{str(time.time() * 1000) + case_.get("name")}.png', page.screenshot())
                except Exception as screenshot_err:
                    self.log.error(f"截图失败: {screenshot_err}")
                case_['duration'] = round(time.time() - case_start_time, 2)
                self.result.add_error(case_, getattr(case_log, 'log_data'), [img] if img else [])
                self.log.error(f"测试用例【{case_.get('name')}】执行出现错误，错误原因：{e}")
                break
                
            finally:
                # 关闭用例创建的上下文
                if case_context:
                    try:
                        case_context.close()
                    except Exception as e:
                        self.log.error(f"关闭上下文失败: {e}")
