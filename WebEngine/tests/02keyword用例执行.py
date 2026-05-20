from WebEngine.keyword.runner import Runner

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
            "keyword": "打开浏览器",
            "params": {
                "browser_type": "chromium"
            }
        },
        {
            "desc": "打开网页",
            "keyword": "访问页面url",
            "params": {
                'url': "/#/login"
            }
        },
        {
            "desc": "等待2秒",
            "keyword": "强制等待时间",
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
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入账号",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "${{username}}"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入密码",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "${{password}}"
                    }
                },
                {
                    "desc": "点击登录",
                    "keyword": "点击元素",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "keyword": "断言页面url地址",
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
                    "keyword": "清空Cookie",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "keyword": "访问页面url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入账号",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "1144961647@qq.com"
                    }
                },
                {
                    "desc": "输入密码",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "12345234"
                    }
                },
                {
                    "desc": "等待2秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "keyword": "元素点击",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "keyword": "断言元素文本值",
                    "params": {
                        "locator": '//p[@class="el-message__content"]',
                        "expect_results": "密码错误"
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
                    "keyword": "清空Cookie",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "keyword": "访问页面url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入密码",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "8142354py"
                    }
                },
                {
                    "desc": "等待2秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "keyword": "元素点击",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "keyword": "断言元素文本值",
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
                    "keyword": "清空Cookie",
                    "params": {
                    }

                },
                {
                    "desc": "打开网页",
                    "keyword": "访问页面url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待2秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 2000
                    }
                },
                {
                    "desc": "输入账号",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "1144961647@qq.com"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "点击登录",
                    "keyword": "元素点击",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "断言页面错误提示信息",
                    "keyword": "断言元素文本值",
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
                    "keyword": "清空Cookie",
                    "params": {
                    }
                },
                {
                    "desc": "打开网页",
                    "keyword": "访问页面url",
                    "params": {
                        'url': "/#/login"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入账号",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入邮箱/手机号/账号"]',
                        'value': "${{username}}"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "输入密码",
                    "keyword": "元素输入",
                    "params": {
                        'locator': '//input[@placeholder="请输入密码"]',
                        'value': "${{password}}"
                    }
                },
                {
                    "desc": "勾选下次自动登录",
                    "keyword": "元素点击",
                    "params": {
                        'locator': '//span[text()="下次自动登录"]',
                    }
                },
                {
                    "desc": "点击登录",
                    "keyword": "元素点击",
                    "params": {
                        "locator": '//div[@class="margin-top"]/button'
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "keyword": "断言页面url地址",
                    "params": {
                        "expect_results": "/#/bindwechat"
                    }
                },
                {
                    "desc": "打开一个新页面窗口",
                    "keyword": "新建窗口页面",
                    "params": {
                        "tag": "page2"
                    }
                },
                {
                    "desc": "关闭原登录成功的页面",
                    "keyword": "关闭页面",
                    "params": {
                        "index": "0"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "新窗口访问登录后才能打开页面",
                    "keyword": "访问页面url",
                    "params": {
                        'url': "/#/bindwechat"
                    }
                },
                {
                    "desc": "等待1秒",
                    "keyword": "强制等待时间",
                    "params": {
                        "timeout": 1000
                    }
                },
                {
                    "desc": "断言是否跳转登录成功后的页面",
                    "keyword": "断言页面url地址",
                    "params": {
                        "expect_results": "/#/bindwechat"
                    }
                }
            ]
        }
    ]
}

if __name__ == '__main__':
    runner = Runner(env_config, suite)
    res = runner.run()
    print(res)