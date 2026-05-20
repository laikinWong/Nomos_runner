from WebEngine.core.runner import Runner

# 执行环境数据
env_config = {
    "is_debug": False,
    "browser_type": "chromium",
    "host": "https://www.ketangpai.com",
    "global_variable": {
        "username": "1144961647@qq.com",
        "password": "8142354py"
    }
}
# 测试套件数据
suite = {
    'id': "编号1",
    'name': "登录功能测试",
    # 测试套件的公共前置操作
    'setup_step': [
        {
            "desc": "打开浏览器",
            "method": "open_browser",
            "params": {
                "browser_type": "chromium"
            }
        },
        {
            "desc": "打开网页",
            "method": "open_url",
            "params": {
                "url": "/#/login"
            }
        },
        {
            "desc": "等待2秒",
            "method": "wait_for_time",
            "params": {
                "timeout": 2000
            }
        },
    ],
    # 用例
    "cases": [
        {
            'id': "编号1",
            'name': "登录成功",
            "skip": False,
            "steps": [
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入账号",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "${{username}}"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "${{password}}"
                    }
                },
                {
                    "desc": "点击登录",
                    "method": "click_ele",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "method": "assert_page_url",
                    "params": {
                        "expect_results": "https://www.ketangpai.com/#/bindwechat"
                    }
                }
            ]
        },
        {
            'id': "编号2",
            'name': "登录密码错误",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "method": "open_url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入账号",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "1144961647@qq.com"
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "12345234"
                    }
                },
                {
                    "desc": "等待2秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "method": "click_ele",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "method": "except_to_have_text",
                    "params": {
                        "locator": '//p[@class="el-message__content"]',
                        "expect_results": "用户不存在"
                    }
                }

            ]
        },
        {
            'id': "编号3",
            'name': "登录用户名为空",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "method": "open_url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "8142354py"
                    }
                },
                {
                    "desc": "等待2秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "method": "click_ele",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "method": "except_to_have_text",
                    "params": {
                        "locator": '//p[@class="el-message__content"]',
                        "expect_results": "用户名不能为空"
                    }
                }

            ]
        },
        {
            'id': "编号4",
            'name': "登录密码为空",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "method": "open_url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入账号",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "1144961647@qq.com"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "method": "click_ele",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "method": "except_to_have_text",
                    "params": {
                        "locator": '//div[@class="el-form-item__error"]',
                        "expect_results": "请输入密码"
                    }
                }

            ]
        },
        {
            'id': "编号5",
            'name': "登录成功，下次自动登录",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {
                    }
                },
                {
                    "desc": "打开网页",
                    "method": "open_url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入账号",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "${{username}}"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "${{password}}"
                    }
                },
                {
                    "desc": "勾选下次自动登录",
                    "method": "click_ele",
                    "params": {
                        'locator': '//span[text()="下次自动登录"]',
                    }
                },
                {
                    "desc": "点击登录",
                    "method": "click_ele",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "method": "assert_page_url",
                    "params": {
                        "expect_results": "/#/bindwechat"
                    }
                },
                {
                    "desc": "打开一个新页面窗口",
                    "method": "open_new_page",
                    "params": {
                        "tag": "page2"
                    }
                },
                {
                    "desc": "关闭原登录成功的页面",
                    "method": "close_page",
                    "params": {
                        "index": "0"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "新窗口访问登录后才能打开页面",
                    "method": "open_url",
                    "params": {
                        'url': "/#/bindwechat"
                    }
                },
                {
                    "desc": "等待1秒",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "method": "assert_page_url",
                    "params": {
                        "expect_results": "/#/bindwechat"
                    }
                },
            ]
        }
    ]
}

if __name__ == '__main__':
    runner = Runner(env_config, suite)
    res = runner.run()
    print(res)
