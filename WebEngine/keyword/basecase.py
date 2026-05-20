import re
import time
from playwright.sync_api import sync_playwright, expect
import inspect

pw = sync_playwright().start()


class KeyWordManage:
    # 关键字的映射关系
    maps = {}

    @staticmethod
    def register(keyword):
        """关键字注册的方法"""
        def wrapper(func):
            KeyWordManage.maps[keyword] = func
            return func
        return wrapper

    @staticmethod
    def register_keyword(key, func):
        maps = {}
        exec(func, maps)
        for k, v in maps.items():
            # 判断v是否为函数
            if inspect.isfunction(v):
                # 注册关键字到映射表maps中
                KeyWordManage.maps[key] = v
                setattr(BaseCase, k, v)

    @classmethod
    def get_keyword_maps(cls, keyword):
        return cls.maps.get(keyword, None)


class BaseBrowser:

    def __init__(self, config, logger, browser=None, context=None, page=None):
        self.config = config
        self.log = logger
        self.pages = {}
        if all([browser, context, page]):
            self.browser = browser
            self.context = context
            self.page = page
            self.pages['default'] = self.page

    def __getattr__(self, item):
        """当浏览器没创建时，自动创建浏览器"""
        if item in ["browser", "context", "page"]:
            self.log.info(f"当前浏览器没有启动，{item}属性不存在，正在为您启动浏览器！")
            self.open_browser(self.config.get("browser_type"))
            return getattr(self, item)
        else:
            raise AttributeError(f"{item}属性不存在")

    @KeyWordManage.register("打开浏览器")
    def open_browser(self, browser_type):
        """打开浏览器"""
        try:
            browser_type = browser_type or self.config.get("browser_type")
            self.browser, self.context, self.page = self.create_browser(browser_type,
                                                                        headless=self.config.get("is_debug"))
        except Exception as e:
            self.log.info("浏览器启动失败！")
            self.log.info(e)
        else:
            self.log.info("浏览器启动成功！")

    @staticmethod
    def create_browser(browser_type, headless):
        """创建浏览器"""
        browser_type = getattr(pw, browser_type)
        browser = browser_type.launch(headless=headless, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        return browser, context, page

    @KeyWordManage.register("清空Cookie")
    def reset_browser_context(self):
        """重置浏览器运行环境：清除cookie和浏览器的缓存信息"""
        self.context.close()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.log.info("浏览器环境已经重置")

    @KeyWordManage.register("关闭浏览器")
    def close(self):
        """关闭浏览器"""
        self.browser.close()
        self.browser = None
        self.log.info("浏览器已经关闭")

    @KeyWordManage.register("新建窗口页面")
    def open_new_page(self, tag):
        """
        打开新页面
        :param tag: 页面标签
        :return:
        """
        # 判断url是否为完整的地址，如果不是完整的地址，则需要根据测试环境的host拼接成完整的地址
        self.pages[tag] = self.context.new_page()
        self.log.info("页面已经打开")

    def _find_page(self, tag='', index='', title='', url=''):
        """
        查找页面
        :param tag: 页面标签
        :param index:
        :param title:
        :param url:
        :return:
        """
        if tag:
            return self.pages[tag]
        elif index:
            return self.context.pages[int(index)]
        elif title:
            for page in self.context.pages:
                if page.title() == title:
                    return page
        elif url:
            for page in self.context.pages:
                if re.search(url, self.page.url):
                    return page
        else:
            return self.context.pages[0]

    @KeyWordManage.register("切换页面")
    def switch_to_page(self, tag='', index='', title='', url=''):
        """
        切换到指定页面: 默认切换到最新的窗口页面
        :param tag: 页面标签
        :param index: 页面打开的顺序
        :param title: 页面标题
        :param url: 页面的url
        :return:
        """
        page = self._find_page(tag, index, title, url)
        self.log.info(f"切换到页面：{page.title()}")
        self.page = page

    @KeyWordManage.register("关闭页面")
    def close_page(self, tag='', index='', title='', url='') -> None:
        """
        关闭页面: 默认关闭最新打开的页面
        :param tag: 页面标签
        :param index: 页面打开的顺序
        :param title: 页面标题
        :param url: 页面的url
        :return:
        """
        page = self._find_page(tag, index, title, url)
        # 判断删除的是否为当前激活页面
        if page == self.page and len(self.context.pages) > 1:
            page.close()
            self.log.info("切换到第一个页面")
            # 切换第一个页面为当前选中的页面
            self.page = self.context.pages[0]
        else:
            self.log.info("页面已经关闭")
            page.close()


class PageMixin(BaseBrowser):
    """封装页面对象的常用操作"""
    case_image_path = './files'

    @KeyWordManage.register("访问页面url")
    def open_url(self, url, wait_until='load', timeout=3000):
        """
        打开url
        :param url: 网页地址
        :param wait_until: 等待的状态
        :param timeout:  超时时间
        :return:
        """
        # 判断url是否为完整的地址，如果不是完整的地址，则需要根据测试环境的host拼接成完整的地址
        if all([not url.startswith("http"), not url.startswith("https")]):
            url = self.config.get("host") + url
        self.log.info(f"正在打开页面：{url}")
        self.page.goto(url, wait_until=wait_until)
        self.log.info(f"成功打开页面：{url}")

    @KeyWordManage.register("刷新网页")
    def refresh(self):
        """刷新页面"""
        self.log.info("正在刷新页面")
        self.page.reload()

    @KeyWordManage.register("返回上一页")
    def go_back(self):
        """返回上一页"""
        self.log.info("正在返回上一页")
        self.page.go_back()

    @KeyWordManage.register("页面截图")
    def save_page_img(self, name='001', path=None):
        """
        保存页面截图
        :param name: 截图的名称
        :param path: 截图保存的路径
        :return:
        """
        try:
            if not path:
                path = self.case_image_path
            t = time.strftime("%Y-%m-%d_%H_%M_%S", time.localtime())
            # 进行截图操作
            filename = f"{path}/{name}_{t}.png"
            self.log.info(f'正在对页面进行截图，保存路径为：{filename}')
            self.page.screenshot(path=filename)
            return filename
        except Exception as e:
            self.log.info(f"保存页面截图失败，失败原因：")
            self.log.info(e)
            return ''

    @KeyWordManage.register("滚动到指定高度位置")
    def scroll_to_height(self, height):
        """
        滚动到指定位置
        :param height:高度
        :return:
        """
        self.log.info(f"正在滚动到指定位置：{height}")
        self.page.evaluate(f"window.scrollTo(0, {height})")

    @KeyWordManage.register("执行JavaScript脚本")
    def execute_script(self, script, args: list):
        """执行JavaScript脚本"""
        self.log.info("正在执行JavaScript脚本！")
        return self.page.evaluate(script, *args)


class LocatorMixin(BaseBrowser):
    """页面元素相关的操作"""

    @KeyWordManage.register("元素输入")
    def fill_value(self, locator, value, timeout=20000):
        """
        :param locator: 输入框的定位表达式
        :param value: 输入的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在元素输入，输入框元素：{locator}，输入值：{value}")
        self.page.locator(locator).fill(value, timeout=timeout)

    @KeyWordManage.register("点击元素")
    def click_ele(self, locator, button='left', count=1, timeout=20000):
        """
        点击元素
        :param locator: 元素的定位表达式
        :param button: 鼠标按键 : "left", "middle", "right"
        :param count: 点击次数
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在点击元素：{locator}")
        loc = self.page.locator(locator)
        # 如果点击次数为1，并且是左键，则使用evaluate方法执行点击操作
        if count == 1 and button == 'left':
            loc.evaluate('el => el.click()')
        else:
            loc.click(button=button, click_count=count, timeout=timeout)

    @KeyWordManage.register("清空输入框内容")
    def clear_value(self, locator, timeout=3000):
        """清空输入框的值"""
        self.log.info(f"正在清空输入框的值:{locator}")
        self.page.locator(locator).clear(timeout=timeout)

    @KeyWordManage.register("选中复选框")
    def set_checked(self, locator, timeout=3000):
        """
        设置选中状态
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在设置选中状态:{locator}")
        self.page.locator(locator).set_checked(True, timeout=timeout)

    @KeyWordManage.register("鼠标悬停到元素上方")
    def hover(self, locator, timeout=20000):
        """悬停到元素上方"""
        self.log.info(f"正在悬停到元素:{locator}")
        self.page.locator(locator).hover(timeout=timeout)

    @KeyWordManage.register("聚焦元素")
    def focus_element(self, locator, timeout=20000):
        """
        聚焦元素
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在聚焦元素:{locator}")
        self.page.locator(locator).focus(timeout=timeout)

    @KeyWordManage.register("选择下拉框的选项")
    def select_option(self, locator, value, timeout=20000):
        """
        选择下拉框的选项
        :param locator: 下拉框的定位表达式
        :param value: 选项的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在选择下拉框:{locator}，选项的值:{value}")
        self.page.locator(locator).select_option(value, timeout=timeout)

    @KeyWordManage.register("键盘输入值")
    def type_value(self, locator, value, timeout=20000):
        """模拟键盘输入"""
        self.log.info(f"正在输入元素:{locator}，输入的值:{value}")
        self.page.locator(locator).type(value, timeout=timeout)

    @KeyWordManage.register("长按元素")
    def long_click_element(self, locator, delay=0.1):
        """
        长按元素
        :param locator: 元素定位
        :param delay: 按住时间
        :return:
        """
        self.log.info(f"正在长按元素：{locator}，按住时间：{delay}")
        self.page.click(locator, delay=float(delay))

    @KeyWordManage.register("拖拽元素")
    def drag_and_drop(self, start_selector, end_selector, timeout=20000):
        """
        拖拽元素
        :param start_selector: 拖拽的元素
        :param end_selector: 拖拽到的元素
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在拖拽元素:{start_selector}，拖拽到的元素:{end_selector}")
        s_ele = self.page.locator(start_selector, timeout=timeout)
        e_ele = self.page.locator(end_selector, timeout=timeout)
        s_ele.drag_to(e_ele)


class WaitMixin(BaseBrowser):
    """等待相关的操作"""

    @KeyWordManage.register("默认等待时间")
    def set_default_timeout(self, timeout=200000):
        """
        设置page全局默认的等待时间
        :param timeout:
        :return:
        """
        self.log.info(f"正在设置默认等待，等待时间：{timeout}ms")
        self.page.set_default_timeout(timeout)

    @KeyWordManage.register("强制等待时间")
    def wait_for_time(self, timeout=20000):
        """设置强制等待时间"""
        self.log.info(f"正在进行强制等待，等待时间：{timeout}ms")
        self.page.wait_for_timeout(timeout)

    @KeyWordManage.register("等待页面加载完成")
    def wait_for_load(self):
        """等待页面加载完成"""
        self.log.info("正在等待页面加载完成")
        self.page.wait_for_load_state(state='load')

    @KeyWordManage.register("等待网络请求完成")
    def wait_for_network(self):
        """等待网络请求完成"""
        self.log.info("正在等待网络请求完成")
        self.page.wait_for_load_state(state='networkidle')

    @KeyWordManage.register("等待元素可见")
    def wait_for_element(self, locator, timeout=20000):
        """
        等待元素可见
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在等待元素:{locator}，可见")
        self.page.wait_for_selector(locator, state='visible', timeout=timeout)


class MouseMixin(BaseBrowser):
    """鼠标键盘相关的操作"""

    @KeyWordManage.register("鼠标点击")
    def mouse_click(self, x, y, button='left', count=1):
        """
        模拟鼠标点击
        :param x: x轴坐标
        :param y: y轴坐标
        :param button: 鼠标按键 : "left", "middle", "right"
        :param count: 点击次数
        :return:
        """
        self.log.info(f"正在模拟鼠标点击：({x}, {y})")
        self.page.mouse.click(int(x), int(y), button=button, click_count=int(count))

    @KeyWordManage.register("鼠标移动")
    def move_mouse(self, x, y):
        """模拟鼠标移动"""
        self.log.info(f"正在模拟鼠标移动：({x}, {y})")
        self.page.mouse.move(int(x), int(y))

    @KeyWordManage.register("鼠标按下")
    def mouse_down(self, button='left'):
        """模拟鼠标按下"""
        self.log.info(f"正在模拟鼠标按下：{button}")
        self.page.mouse.down(button=button)

    @KeyWordManage.register("鼠标抬起")
    def mouse_up(self, button='left'):
        """模拟鼠标抬起"""
        self.log.info(f"正在模拟鼠标抬起：{button}")
        self.page.mouse.up(button=button)

    @KeyWordManage.register("键盘按键")
    def press_key(self, key):
        """模拟键盘按键"""
        self.log.info(f"正在模拟键盘按键：{key}")
        self.page.keyboard.press(key)

    @KeyWordManage.register("键盘输入文本")
    def press_type(self, keys):
        """模拟键盘输入文本"""
        self.log.info(f"正在模拟键盘输入：{keys}")
        self.page.keyboard.type(keys)

    @KeyWordManage.register("鼠标滚动")
    def mouse_wheel(self, x, y):
        """
        模拟鼠标滚动
        :param x: x轴坐标
        :param y: y轴坐标
        :return:
        """
        self.log.info(f"正在模拟鼠标滚动：滚动距离：({x}, {y})")
        self.page.mouse.wheel(int(x), int(y))


class IFrameMixin(BaseBrowser):
    """iframe相关的操作"""

    @KeyWordManage.register("iframe内元素输入")
    def frame_fill_value(self, frame, locator, value, timeout=20000):
        """
        :param frame: iframe定位表达式
        :param locator: 输入框的定位表达式
        :param value: 输入的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在定位元素：{locator}，输入值：{value}")
        self.page.frame_locator(frame).locator(locator).fill(value, timeout=timeout)

    @KeyWordManage.register("iframe内元素点击")
    def frame_click_element(self, frame, locator, button='left', count=1, timeout=20000):
        """
        点击iframe内元素
        :param frame: iframe定位表达式
        :param locator: 元素的定位表达式
        :param button: 鼠标按键 : "left", "middle", "right"
        :param count: 点击次数
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        count = int(count)
        self.log.info(f"正在点击元素：{locator}")
        loc = self.page.frame_locator(frame).locator(locator)
        # 如果点击次数为1，并且是左键，则使用evaluate方法执行点击操作
        if count == 1 and button == 'left':
            loc.evaluate('el => el.click()')
        else:
            loc.click(button=button, click_count=count, timeout=timeout)

    @KeyWordManage.register("iframe内元素悬停")
    def frame_hover(self, frame, locator, timeout=20000):
        """
        悬停到元素上方
        :param frame:
        :param locator:
        :param timeout:
        :return:
        """
        self.log.info(f"正在悬停到元素:{locator}")
        self.page.frame_locator(frame).locator(locator).hover(timeout=timeout)

    @KeyWordManage.register("iframe内元素聚焦")
    def frame_focus_element(self, frame, locator, timeout=20000):
        """
        聚焦元素
        :param frame: iframe定位表达式
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在聚焦元素:{locator}")
        self.page.frame_locator(frame)
        locator(locator).focus(timeout=timeout)

    @KeyWordManage.register("iframe内下拉选择框选择")
    def frame_select_option(self, frame, locator, value, timeout=20000):
        """
        选择下拉框的选项
        :param frame: iframe定位表达式
        :param locator: 下拉框的定位表达式
        :param value: 选项的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在选择下拉框：{locator}，选项的值：{value}")
        self.page.frame_locator(frame).locator(locator).select_option(value, timeout=timeout)

    @KeyWordManage.register("iframe内元素键盘输入")
    def frame_type_value(self, frame, locator, value, timeout=20000):
        """
        模拟键盘输入
        :param frame:
        :param locator:
        :param value:
        :param timeout:
        :return:
        """
        self.log.info(f"正在输入元素：{locator}，输入的值：{value}")
        self.page.frame_locator(frame).locator(locator).type(value, timeout=timeout)

    @KeyWordManage.register("iframe内元素长按")
    def frame_long_click_element(self, frame, locator, delay=0.1):
        """
        长按元素
        :param frame: iframe定位表达式
        :param locator: 元素定位
        :param delay: 按住时间
        :return:
        """
        self.log.info(f"正在长按元素：{locator}，按住时间：{delay}")
        self.page.frame_locator(frame).click(locator, delay=float(delay))

    @KeyWordManage.register("iframe内元素拖拽")
    def frame_drag_and_drop(self, frame, start_selector, end_selector, timeout=20000):
        """
        拖拽元素
        :param frame: iframe定位表达式
        :param start_selector: 拖拽的元素
        :param end_selector: 拖拽到的元素
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在拖拽元素：{start_selector}，拖拽到的元素：{end_selector}")
        s_ele = self.page.frame_locator(frame).locator(start_selector, timeout=timeout)
        e_ele = self.page.frame_locator(frame).locator(end_selector, timeout=timeout)
        s_ele.drag_to(e_ele)


class AssertMixin(BaseBrowser):
    """
    断言相关的方法封装
    """

    @KeyWordManage.register("断言页面标题")
    def assert_page_title(self, expect_results, is_equal=1):
        """
        断言页面的标题
        :param expect_results: 期望结果
        :param is_equal: 是否相等
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言页面标题，预期结果：{expect_results}，实际结果：{self.page.title()}")
            expect(self.page).to_have_title(re.compile(expect_results))
            self.log.info(f"断言页面标题，预期结果=实际结果")
        else:
            expect(self.page).not_to_have_title(re.compile(expect_results))
            self.log.info(f"断言页面标题，预期结果!=实际结果")

    @KeyWordManage.register("断言页面url地址")
    def assert_page_url(self, expect_results, is_equal=1):
        """
        断言页面的url地址
        :param expect_results: 期望结果
        :param is_equal: 是否相等
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言页面url地址，预期结果：{expect_results}，实际结果：{self.page.url}")
            expect(self.page).to_have_url(re.compile(expect_results))
            self.log.info(f"断言页面url地址，预期结果=实际结果")
        else:
            expect(self.page).not_to_have_url(re.compile(expect_results))
            self.log.info(f"断言页面url地址，预期结果!=实际结果")

    @KeyWordManage.register("断言元素value属性")
    def except_to_have_value(self, locator, expect_results, is_equal=1):
        """
        断言元素的value
        :param locator:
        :param expect_results:
        :param is_equal:
        :return:
        """
        self.log.info(f"正在断言元素{locator}的value属性，预期结果：{expect_results}")
        if is_equal:
            expect(self.page.locator(locator)).to_have_value(re.compile(expect_results))
            self.log.info(f"断言元素的value，预期结果=实际结果")
        else:
            expect(self.page.locator(locator)).not_to_have_value(re.compile(expect_results))
            self.log.info(f"断言元素的value，预期结果!=实际结果")

    @KeyWordManage.register("断言元素文本值")
    def except_to_have_text(self, locator, expect_results, is_equal=1):
        """
        断言元素的文本
        :param locator:
        :param expect_results:
        :param is_equal:
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言元素{locator}的文本，预期结果：{expect_results}")
            expect(self.page.locator(locator)).to_have_text(re.compile(expect_results), timeout=5000)
            self.log.info(f"断言元素的文本，预期结果=实际结果")
        else:
            expect(self.page.locator(locator)).not_to_have_text(expect_results, timeout=5000)
            self.log.info(f"断言元素的文本，预期结果!=实际结果")

    @KeyWordManage.register("断言元素属性值")
    def except_to_have_attribute(self, locator, attr_name, expect_results, is_equal=1):
        """
        断言元素的属性值
        :param locator:定位表达式
        :param attr_name: 属性名称
        :param expect_results: 属性值
        :param is_equal: 是否相等
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言元素{locator}的属性值，属性名称：{attr_name}，属性值：{expect_results}")
            expect(self.page.locator(locator)).to_have_attribute(attr_name, expect_results)
            self.log.info(f"断言元素的属性值，预期结果=实际结果")
        else:
            expect(self.page.locator(locator)).not_to_have_attribute(attr_name, expect_results)
            self.log.info(f"断言元素的属性值，预期结果!=实际结果")

    @KeyWordManage.register("断言元素可见")
    def except_to_be_visible(self, locator, index=1):
        """
        断言元素是否可见
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index}个元素是否可见")
            expect(self.page.locator(locator).nth(index - 1)).to_be_visible()
            self.log.info(f"断言元素可见，预期结果=实际结果")

        else:
            expect(self.page.locator(locator).first).to_be_visible()
            self.log.info(f"断言元素可见，预期结果!=实际结果")

    @KeyWordManage.register("断言元素隐藏")
    def except_to_be_hidden(self, locator, index=1):
        """
        断言元素不可见
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index}个元素是否可见")
            expect(self.page.locator(locator).nth(index - 1)).to_be_hidden()
            self.log.info(f"断言元素不可见，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_hidden()
            self.log.info(f"断言元素不可见，预期结果!=实际结果")

    @KeyWordManage.register("断言元素可用")
    def except_to_be_enabled(self, locator, index=1):
        """
        断言元素是否可用
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index}个元素是否可用")
            expect(self.page.locator(locator).nth(index - 1)).to_be_enabled()
            self.log.info(f"断言元素是否可用，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_enabled()
            self.log.info(f"断言元素是否可用，预期结果!=实际结果")

    @KeyWordManage.register("断言元素被禁用")
    def except_to_be_disabled(self, locator, index=1):
        """
        断言元素是否不可用
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index}个元素是否可用")
            expect(self.page.locator(locator).nth(index - 1)).to_be_disabled()
            self.log.info(f"断言元素是否不可用，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_disabled()
            self.log.info(f"断言元素是否不可用，预期结果!=实际结果")

    @KeyWordManage.register("断言元素被选中")
    def except_to_be_checked(self, locator, index=1):
        """
        断言元素是否被选中
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index - 1}个元素是否被选中")
            expect(self.page.locator(locator).nth(index - 1)).to_be_checked()
            self.log.info(f"断言元素是否被选中，预期结果=实际结果")
        else:

            expect(self.page.locator(locator).first).to_be_checked()
            self.log.info(f"断言元素是否被选中，预期结果!=实际结果")

    @KeyWordManage.register("断言元素是否为空")
    def except_to_be_empty(self, locator, index=1):
        """
        断言元素是否为空
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index - 1}个元素是否为空")
            expect(self.page.locator(locator).nth(index - 1)).to_be_empty()
            self.log.info(f"断言元素是否为空，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_empty()
            self.log.info(f"断言元素是否为空，预期结果!=实际结果")

    @KeyWordManage.register("断言元素可编辑")
    def except_to_be_editable(self, locator, index=1):
        """
        断言元素是否可编辑
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index - 1}个元素是否可编辑")
            expect(self.page.locator(locator).nth(index - 1)).to_be_editable()
            self.log.info(f"断言元素是否可编辑，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_editable()
            self.log.info(f"断言元素是否可编辑，预期结果!=实际结果")

    @KeyWordManage.register("断言元素是否获取焦点")
    def except_to_be_focused(self, locator, index=1):
        """
        断言元素是否获取焦点
        :param locator:
        :param index: 定位到的第几个元素
        :return:
        """
        if index > 1:
            self.log.info(f"正在断言元素{locator}，第{index - 1}个元素是否获取焦点")
            expect(self.page.locator(locator).nth(index - 1)).to_be_focused()
            self.log.info(f"断言元素是否获取焦点，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_focused()
            self.log.info(f"断言元素是否获取焦点，预期结果!=实际结果")


class BaseCase(PageMixin, LocatorMixin, MouseMixin, WaitMixin, IFrameMixin, AssertMixin):
    """
    封装了页面对象，元素对象，鼠标键盘对象，断言对象
    """

    def perform(self, step):
        """执行关键字的测试步骤的方法"""
        keyword = step.get("keyword")
        method_name = step.get("method")
        self.log.info(f"正在执行关键字：{keyword}")
        # 判断关键字是否存在
        if KeyWordManage.get_keyword_maps(keyword):
            # 获取关键字对应的方法
            method = KeyWordManage.get_keyword_maps(keyword)
            # 获取关键字执行的参数
            params = step.get("params", {})
            params = self.replace_params(params)
            # 执行关键字
            method(self, **params)
        elif hasattr(self, method_name):
            method = getattr(self, method_name)
            # 获取关键字执行的参数
            params = step.get("params", {})
            params = self.replace_params(params)
            method(self, **params)
        else:
            raise AttributeError(f"{step['desc']}执行的{keyword}关键字不存在！")

    def replace_params(self, value: dict) -> dict:
        """
        替换参数中的变量
        :param value: 要进行替换的参数
        :return:
        """
        # 匹配变量的正则表达式
        pattern = re.compile(r'\${{(.+?)}}')
        data = str(value)
        while pattern.search(data):
            # 获取要替换的内容
            old_value = pattern.search(data).group()
            # 提取变量成名
            key = pattern.search(data).group(1)
            self.log.info(f"检测到参数中有变量需要替换，变量为：{old_value}")
            # 获取变量的值
            new_value = self.config.get('global_variable', {}).get(key)
            if new_value:
                # 替换变量
                data = data.replace(old_value, new_value)
                self.log.info(f"成功将变量：{old_value}，替换成：{new_value}")
            else:
                self.log.info(f"测试环境的全局变量中没有：{key}，变量替换失败！")
        return eval(data)
