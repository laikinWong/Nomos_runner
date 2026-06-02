import re
import time
from playwright.sync_api import sync_playwright, expect


class BaseBrowser:

    def __init__(self, pw_instance, config, logger, browser=None, context=None, page=None):
        self.pw = pw_instance
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
            self.log.info(f"当前浏览器没有启动，{item}属性不存在，正在启动浏览器！")
            self.open_browser(self.config.get("browser_type"))
            return getattr(self, item)
        else:
            raise AttributeError(f"{item}属性不存在！")

    def open_browser(self, browser_type):
        """打开浏览器"""
        try:
            browser_type = browser_type or self.config.get("browser_type")
            self.browser, self.context, self.page = self.create_browser(self.pw, browser_type,
                                                                        headless=self.config.get("is_debug"))
        except Exception as e:
            self.log.info("浏览器启动失败！")
            self.log.info(e)
        else:
            self.log.info("浏览器启动成功！")

    @staticmethod
    def create_browser(pw_instance, browser_type, headless):
        """创建浏览器"""
        browser_type_obj = getattr(pw_instance, browser_type)
        launch_args = ['--start-maximized'] if not headless else []
        browser = browser_type_obj.launch(headless=headless, args=launch_args)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        return browser, context, page

    def reset_browser_context(self):
        """重置浏览器运行环境：清除cookie和浏览器的缓存信息"""
        self.context.close()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def close(self):
        """关闭浏览器"""
        self.browser.close()
        self.browser = None

    def open_new_page(self, tag):
        """
        打开新页面
        :param tag: 页面标签
        :return:
        """
        # 判断url是否为完整的地址，如果不是完整的地址，则需要根据测试环境的host拼接成完整的地址
        self.pages[tag] = self.context.new_page()
        self.log.info("页面已经打开！")

    def find_page(self, tag='', index='', title='', url=''):
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

    def switch_to_page(self, tag='', index='', title='', url=''):
        """
        切换到指定页面:默认切换到最新的窗口页面
        :param tag: 页面标签
        :param index: 页面打开的顺序
        :param title: 页面标题
        :param url: 页面的url
        :return:
        """
        page = self.find_page(tag, index, title, url)
        self.page = page

    def close_page(self, tag='', index='', title='', url='') -> None:
        """
        关闭页面:默认关闭最新打开的页面
        :param tag: 页面标签
        :param index: 页面打开的顺序
        :param title: 页面标题
        :param url: 页面的url
        :return:
        """
        page = self.find_page(tag, index, title, url)
        # 判断删除的是否为当前激活页面
        if page == self.page and len(self.context.pages) > 1:
            page.close()
            # 切换第一个页面为当前选中的页面
            self.page = self.context.pages[0]
        else:
            page.close()


class PageMixin(BaseBrowser):
    """封装页面对象的常用操作"""
    case_image_path = './files'

    def open_url(self, url, wait_until='networkidle', timeout=30000):
        """
        打开url
        :param url: 网页地址
        :param wait_until: 等待的状态，可选值: 'load', 'domcontentloaded', 'networkidle', 'commit'
        :param timeout:  超时时间（毫秒）
        :return:
        """
        # 判断url是否为完整的地址，如果不是完整的地址，则需要根据测试环境的host拼接成完整的地址
        if all([not url.startswith("http"), not url.startswith("https")]):
            url = self.config.get("host") + url
        self.log.info(f"正在打开页面：{url}", )
        self.page.goto(url, wait_until=wait_until, timeout=timeout)
        self.log.info(f"成功打开页面：{url}", )

    def refresh(self):
        """刷新页面"""
        self.log.info("正在刷新页面！")
        self.page.reload()

    def go_back(self):
        """返回上一页"""
        self.log.info("正在返回上一页")
        self.page.go_back()

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

    def scroll_to_height(self, height):
        """
        滚动到指定位置
        :param height:高度
        :return:
        """
        self.page.evaluate(f"window.scrollTo(0, {height})")

    def execute_script(self, script, *args):
        """执行JavaScript脚本"""
        self.log.info("正在执行JavaScript脚本")
        return self.page.evaluate(script, *args)


class LocatorMixin(BaseBrowser):
    """页面元素相关的操作"""

    def fill_value(self, locator, value, timeout=20000):
        """
        :param locator: 输入框的定位表达式
        :param value: 输入的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在元素输入，输入框元素：{locator}，输入值：{value}")
        self.page.locator(locator).fill(value, timeout=timeout)

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

    def clear_value(self, locator, timeout=3000):
        """清空输入框的值"""
        self.log.info(f"正在清空输入框的值：{locator}")
        self.page.locator(locator).clear(timeout=timeout)

    def set_checked(self, locator, timeout=3000):
        """
        设置选中状态
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在设置选中状态：{locator}")
        self.page.locator(locator).set_checked(True, timeout=timeout)

    def hover(self, locator, timeout=20000):
        """悬停到元素上方"""
        self.log.info(f"正在悬停到元素：{locator}")
        self.page.locator(locator).hover(timeout=timeout)

    def focus_element(self, locator, timeout=20000):
        """
        聚焦元素
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在聚焦元素：{locator}")
        self.page.locator(locator).focus(timeout=timeout)

    def select_option(self, locator, value, timeout=20000):
        """
        选择下拉框的选项
        :param locator: 下拉框的定位表达式
        :param value: 选项的值
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在选择下拉框：{locator}，选项的值：{value}")
        self.page.locator(locator).select_option(value, timeout=timeout)

    def type_value(self, locator, value, timeout=20000):
        """模拟键盘输入"""
        self.log.info(f"正在输入元素：{locator}，输入的值：{value}")
        self.page.locator(locator).type(value, timeout=timeout)

    def long_click_element(self, locator, delay=0.1):
        """
        长按元素
        :param locator: 元素定位
        :param delay: 按住时间
        :return:
        """
        self.log.info(f"正在长按元素：{locator},按住时间：{delay}")
        self.page.click(locator, delay=delay)

    def drag_and_drop(self, start_selector, end_selector, timeout=20000):
        """
        拖拽元素
        :param start_selector: 拖拽的元素
        :param end_selector: 拖拽到的元素
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在拖拽元素：{start_selector}，拖拽到的元素：{end_selector}")
        s_ele = self.page.locator(start_selector, timeout=timeout)
        e_ele = self.page.locator(end_selector, timeout=timeout)
        s_ele.drag_to(e_ele)


class WaitMixin(BaseBrowser):
    """等待相关的操作"""

    def set_default_timeout(self, timeout=200000):
        """
        设置page全局默认的等待时间
        :param timeout:
        :return:
        """
        self.log.info(f"正在设置默认等待时间：{timeout}")
        self.page.set_default_timeout(timeout)

    def wait_for_time(self, timeout=20000):
        """设置强制等待时间"""
        self.log.info(f"正在进行强制等待，等待时间：{timeout}ms")
        self.page.wait_for_timeout(timeout)

    def wait_for_load(self):
        """等待页面加载完成"""
        self.log.info("正在等待页面加载完成")
        self.page.wait_for_load_state(state='load')

    def wait_for_network(self):
        """等待网络请求完成"""
        self.log.info("正在等待网络请求完成")
        self.page.wait_for_load_state(state='networkidle')

    def wait_for_element(self, locator, timeout=20000):
        """
        等待元素可见
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在等待元素：{locator}，可见")
        self.page.wait_for_selector(locator, state='visible', timeout=timeout)


class MouseMixin(BaseBrowser):
    """鼠标键盘相关的操作"""

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
        self.page.mouse.click(x, y, button=button, click_count=count)

    def move_mouse(self, x, y):
        """模拟鼠标移动"""
        self.log.info(f"正在模拟鼠标移动：({x}, {y})")
        self.page.mouse.move(x, y)

    def mouse_down(self, button='left'):
        """模拟鼠标按下"""
        self.log.info(f"正在模拟鼠标按下：{button}")
        self.page.mouse.down(button=button)

    def mouse_up(self, button='left'):
        """模拟鼠标抬起"""
        self.log.info(f"正在模拟鼠标抬起：{button}")
        self.page.mouse.up(button=button)

    def press_key(self, key):
        """模拟键盘按键"""
        self.log.info(f"正在模拟键盘按键：{key}")
        self.page.keyboard.press(key)

    def press_type(self, keys):
        """模拟键盘输入文本"""
        self.log.info(f"正在模拟键盘输入：{keys}")
        self.page.keyboard.type(keys)


class IFrameMixin(BaseBrowser):
    """iframe相关的操作"""

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

    def frame_click_element(self, frame, locator, button='left', click_count=1, timeout=20000):
        """
        点击iframe内元素
        :param frame: iframe定位表达式
        :param locator: 元素的定位表达式
        :param button: 鼠标按键 : "left", "middle", "right"
        :param click_count: 点击次数
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在点击元素：{locator}")
        loc = self.page.frame_locator(frame).locator(locator)
        # 如果点击次数为1，并且是左键，则使用evaluate方法执行点击操作
        if click_count == 1 and button == 'left':
            loc.evaluate('el => el.click()')
        else:
            loc.click(button=button, click_count=click_count, timeout=timeout)

    def frame_hover(self, frame, locator, timeout=20000):
        """
        悬停到元素上方
        :param frame:
        :param locator:
        :param timeout:
        :return:
        """
        self.log.info(f"正在悬停到元素：{locator}")
        self.page.frame_locator(frame).locator(locator).hover(timeout=timeout)

    def frame_focus_element(self, frame, locator, timeout=20000):
        """
        聚焦元素
        :param frame: iframe定位表达式
        :param locator: 元素的定位表达式
        :param timeout: 等待元素可见的最大超时时间
        :return:
        """
        self.log.info(f"正在聚焦元素：{locator}")
        self.page.frame_locator(frame)
        locator(locator).focus(timeout=timeout)

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

    def frame_long_click_element(self, frame, locator, delay=0.1):
        """
        长按元素
        :param frame: iframe定位表达式
        :param locator: 元素定位
        :param delay: 按住时间
        :return:
        """
        self.log.info(f"正在长按元素：{locator}，按住时间：{delay}")
        self.page.frame_locator(frame).click(locator, delay=delay)

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

    def assert_page_url(self, expect_results, is_equal=1):
        """
        断言页面的url地址
        :param expect_results: 期望结果
        :param is_equal: 是否相等，0：代表不相等，1：代表相等
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言页面url地址，预期结果：{expect_results}，实际结果：{self.page.url}")
            expect(self.page).to_have_url(re.compile(expect_results))
            self.log.info(f"断言页面url地址，预期结果=实际结果")
        else:
            expect(self.page).not_to_have_url(re.compile(expect_results))
            self.log.info(f"断言页面url地址，预期结果!=实际结果")

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

    def except_to_have_attribute(self, locator, name, value, is_equal=1):
        """
        断言元素的属性值
        :param locator:定位表达式
        :param name: 属性名称
        :param value: 属性值
        :param is_equal: 是否相等
        :return:
        """
        if is_equal:
            self.log.info(f"正在断言元素{locator}的属性值，属性名称：{name}，属性值：{value}")
            expect(self.page.locator(locator)).to_have_attribute(name, value)
            self.log.info(f"断言元素的属性值，预期结果=实际结果")
        else:
            expect(self.page.locator(locator)).not_to_have_attribute(name, value)
            self.log.info(f"断言元素的属性值，预期结果!=实际结果")

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
            self.log.info(f"断言元素是否可见，预期结果=实际结果")
        else:
            expect(self.page.locator(locator).first).to_be_visible()
            self.log.info(f"断言元素是否可见，预期结果=实际结果")

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
        """执行测试步骤的方法"""

        method = step.get("method")
        if hasattr(self, method):
            params = step.get("params", {})
            params = self.replace_params(params)
            # 移除前端临时字段 element_id
            params.pop("element_id", None)
            getattr(self, method)(**params)
        else:
            raise AttributeError(f"{step['desc']}执行的，{method}方法不存在！")

    def replace_params(self, value):
        """
        递归替换参数中的变量，移除不安全的 eval
        :param value: 要进行替换的参数
        :return: 替换后的参数
        """
        if isinstance(value, str):
            pattern = re.compile(r'\${{(.+?)}}')
            # 循环替换字符串中所有的变量
            while pattern.search(value):
                old_value = pattern.search(value).group()
                key = pattern.search(value).group(1)
                self.log.info(f"检测到参数中有变量需要替换，变量为：{old_value}")
                
                new_value = self.config.get('global_variable', {}).get(key)
                if new_value is not None:
                    # 如果整个字符串就是一个变量，直接返回其真实类型值（如 dict, int 等）
                    if value == old_value:
                        self.log.info(f"成功将变量：{old_value}，替换成：{new_value}")
                        return new_value
                    
                    # 否则进行字符串替换
                    value = value.replace(old_value, str(new_value))
                    self.log.info(f"成功将变量：{old_value}，替换成：{new_value}")
                else:
                    self.log.info(f"测试环境的全局变量中没有{key}，变量替换失败！")
                    break  # 防止死循环
            return value
        elif isinstance(value, dict):
            return {k: self.replace_params(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.replace_params(v) for v in value]
        else:
            return value
