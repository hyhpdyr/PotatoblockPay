from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import requests
import mysql.connector
from cfg import channel_id, mysql_info
import time
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import random

def get_time():
    return int(requests.post("https://api.potatoblock.com/api/time/timestamp").json())

payment_methods = {
    "微信": "WeChat",
    "支付宝": "Alipay",
}

def notify_server(amount, method, notes):
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                if not notes:
                    notes = None
                cursor.execute(
                    "INSERT INTO bills (amount, time, channel_id, channel_type, notes) VALUES (%s, %s, %s, %s, %s);",
                    (amount, get_time(), channel_id, payment_methods.get(method), notes)
                )
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

def driver_init():
    """初始化浏览器对象"""
    # 启动浏览器实例
    service = EdgeService(executable_path="msedgedriver.exe")
    options = webdriver.EdgeOptions()
    #options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Edge(service=service, options=options)
    driver.implicitly_wait(1)
    
    # 访问拉卡拉缴费易管理页面
    url = f"https://jfyui.lakala.com/#/login?redirect=/order/cashier"
    driver.get(url)
    
    # 初始化曲奇
    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = f.read().strip()
    cookies = json.loads(cookies)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(random.uniform(0.5, 1))
    try:
        driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/div[1]/div[1]')
    except NoSuchElementException:
        cookies = []
    if not cookies:
        input("请登录后按下回车键继续")
        cookies = driver.get_cookies()
        cookies = json.dumps(cookies)
        with open("cookies.json", "w") as f:
            f.write(cookies)
    driver.get("https://jfyui.lakala.com/#/order/cashier")
    
    return driver

def globals_init():
    """初始化全局变量"""
    # 设置全局变量
    global driver, last_collection_serial
    
    # 初始化浏览器
    driver = driver_init()
    
    # 初始化最后一笔交易
    last_collection_serial = None

def refresh_account():
    # 设置全局变量
    global latest_collection_note, latest_collection_method, latest_collection_serial, latest_collection_time, latest_collection_amount
    
    # 刷新账单
    driver.find_element(By.XPATH, '//*[@id="app"]/div/div[2]/section/div/form/div/div[9]/div/button[2]').click()
    time.sleep(0.2)
    
    # 获取最近一条账单的备注
    latest_collection_note = driver.find_element(By.XPATH, '//*[@id="cashierTable"]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[12]/div/div/div').text
    # 获取最近一条账单的备注
    latest_collection_method = driver.find_element(By.XPATH, '//*[@id="cashierTable"]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[11]/div/div/div/div/span').text
    latest_collection_method = latest_collection_method.strip()
    # 获取最近一条账单的流水号
    latest_collection_serial = driver.find_element(By.XPATH, '//*[@id="cashierTable"]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[9]/div/div/div').text
    latest_collection_serial = int(latest_collection_serial)
    # 获取最近一条账单的时间戳
    latest_collection_time = driver.find_element(By.XPATH, '//*[@id="cashierTable"]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[5]/div/div/div').text
    latest_collection_time = datetime.strptime(latest_collection_time, "%Y-%m-%d %H:%M:%S")
    latest_collection_time = latest_collection_time.replace(tzinfo=timezone(timedelta(hours=8)))
    latest_collection_time = latest_collection_time.astimezone(timezone.utc)
    latest_collection_time = int(latest_collection_time.timestamp())
    # 获取最近一条账单的金额
    latest_collection_amount = driver.find_element(By.XPATH, '//*[@id="cashierTable"]/div[1]/div[3]/div/div[1]/div/table/tbody/tr[1]/td[4]/div/div/div').text
    latest_collection_amount = Decimal(latest_collection_amount)

def listen_collection():
    global last_collection_serial
    while True:
        try:
            time.sleep(random.uniform(3.5, 5.5))
            refresh_account()
            if not last_collection_serial:
                last_collection_serial = latest_collection_serial
            if latest_collection_serial == last_collection_serial:
                print(f"流水号无变动: {latest_collection_serial}")
                continue
            last_collection_serial = latest_collection_serial
            print(f"监听到收款")
            print(f"金额: {latest_collection_amount},\n时间戳: {latest_collection_time},\n流水号: {latest_collection_serial},\n支付方式: {latest_collection_method},\n留言: '{latest_collection_note}'.")
            notify_server(latest_collection_amount, latest_collection_method, latest_collection_note)
        except KeyboardInterrupt:
            # 停止监听
            break
        except Exception:
            raise
    # 关闭浏览器
    driver.quit()

def main():
    globals_init()
    print("初始化完成, 开始监听收款")
    listen_collection()

if __name__ == "__main__":
    main()
