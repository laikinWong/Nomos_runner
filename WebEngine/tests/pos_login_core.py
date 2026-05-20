from WebEngine.core.runner import Runner

# 执行环境数据
env_config = {
    "is_debug": False,
    "browser_type": "chromium",
    "host": "https://pos.ysy123.cn",
    "global_variable": {
        "store_no": "WJ-HZ-001",
        "phone": "13900010001",
        "password": "123456"
    }
}

# 测试套件数据
suite = {
    'id': "pos-login-001",
    'name': "POS系统登录功能测试",
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
            "desc": "打开登录页面",
            "method": "open_url",
            "params": {
                "url": "/login"
            }
        },
        {
            "desc": "等待页面加载",
            "method": "wait_for_time",
            "params": {
                "timeout": 3000
            }
        },
    ],
    # 用例
    "cases": [
        {
            'id': "TC-LOGIN-001",
            'name': "登录页面元素完整性检查",
            "skip": False,
            "steps": [
                {
                    "desc": "断言门店编号输入框可见",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"门店编号")]]'
                    }
                },
                {
                    "desc": "断言手机号输入框可见",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"手机号")]]'
                    }
                },
                {
                    "desc": "断言密码输入框可见",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"密码")]]'
                    }
                },
                {
                    "desc": "断言登录按钮可见",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//button[contains(text(),"登") and contains(text(),"录")]'
                    }
                }
            ]
        },
        {
            'id': "TC-LOGIN-002",
            'name': "店长账号密码登录成功",
            "skip": False,
            "steps": [
                {
                    "desc": "输入门店编号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"门店编号")]]',
                        "value": "${{store_no}}"
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
                    "desc": "输入手机号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"手机号")]]',
                        "value": "${{phone}}"
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
                        "locator": '//input[@placeholder[contains(.,"密码")]]',
                        "value": "${{password}}"
                    }
                },
                {
                    "desc": "点击登录按钮",
                    "method": "click_ele",
                    "params": {
                        "locator": '//button[contains(text(),"登") and contains(text(),"录")]'
                    }
                },
                {
                    "desc": "等待页面跳转",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 5000
                    }
                },
                {
                    "desc": "断言登录成功后跳转到dashboard",
                    "method": "assert_page_url",
                    "params": {
                        "expect_results": "/dashboard"
                    }
                }
            ]
        },
        {
            'id': "TC-LOGIN-003",
            'name': "密码错误登录失败",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {}
                },
                {
                    "desc": "打开登录页面",
                    "method": "open_url",
                    "params": {
                        "url": "/login"
                    }
                },
                {
                    "desc": "等待页面加载",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "输入门店编号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"门店编号")]]',
                        "value": "WJ-HZ-001"
                    }
                },
                {
                    "desc": "输入手机号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"手机号")]]',
                        "value": "13900010001"
                    }
                },
                {
                    "desc": "输入错误密码",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"密码")]]',
                        "value": "wrongpassword"
                    }
                },
                {
                    "desc": "点击登录按钮",
                    "method": "click_ele",
                    "params": {
                        "locator": '//button[contains(text(),"登") and contains(text(),"录")]'
                    }
                },
                {
                    "desc": "等待错误提示",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "断言显示错误提示",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//*[contains(@class,"el-message--error") or contains(@class,"error-message") or contains(@class,"toast")]'
                    }
                }
            ]
        },
        {
            'id': "TC-LOGIN-004",
            'name": "门店编号为空登录失败",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {}
                },
                {
                    "desc": "打开登录页面",
                    "method": "open_url",
                    "params": {
                        "url": "/login"
                    }
                },
                {
                    "desc": "等待页面加载",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "输入手机号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"手机号")]]',
                        "value": "13900010001"
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"密码")]]',
                        "value": "123456"
                    }
                },
                {
                    "desc": "点击登录按钮",
                    "method": "click_ele",
                    "params": {
                        "locator": '//button[contains(text(),"登") and contains(text(),"录")]'
                    }
                },
                {
                    "desc": "等待错误提示",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "断言显示错误提示",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//*[contains(@class,"el-message") or contains(@class,"error") or contains(@class,"form-item__error")]'
                    }
                }
            ]
        },
        {
            'id': "TC-LOGIN-005",
            'name': "手机号为空登录失败",
            "skip": False,
            "steps": [
                {
                    "desc": "重置浏览器上下文",
                    "method": "reset_browser_context",
                    "params": {}
                },
                {
                    "desc": "打开登录页面",
                    "method": "open_url",
                    "params": {
                        "url": "/login"
                    }
                },
                {
                    "desc": "等待页面加载",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "输入门店编号",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"门店编号")]]',
                        "value": "WJ-HZ-001"
                    }
                },
                {
                    "desc": "输入密码",
                    "method": "fill_value",
                    "params": {
                        "locator": '//input[@placeholder[contains(.,"密码")]]',
                        "value": "123456"
                    }
                },
                {
                    "desc": "点击登录按钮",
                    "method": "click_ele",
                    "params": {
                        "locator": '//button[contains(text(),"登") and contains(text(),"录")]'
                    }
                },
                {
                    "desc": "等待错误提示",
                    "method": "wait_for_time",
                    "params": {
                        "timeout": 3000
                    }
                },
                {
                    "desc": "断言显示错误提示",
                    "method": "assert_element_visible",
                    "params": {
                        "locator": '//*[contains(@class,"el-message") or contains(@class,"error") or contains(@class,"form-item__error")]'
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
