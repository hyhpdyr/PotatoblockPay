from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
import time
import sys
import mysql.connector
from cfg import channel_id, mysql_info

service = EdgeService(executable_path="msedgedriver.exe")
options = webdriver.EdgeOptions()
driver = webdriver.Edge(service=service, options=options)

url = "https://personalweb.alipay.com/portal/i.htm"
driver.get(url)

# 等待手动登录完成
input("完成登录后按下任意键继续")

def get_balance():
    # 点击"显示余额"
    element = driver.find_element(By.CLASS_NAME, "show-text")
    element.click()
    # 等待元素加载完成
    time.sleep(0.8)
    # 读取"账户余额"
    element = driver.find_element(By.CLASS_NAME, "df-integer")
    return float(element.text)

def hide_balance():
    element = driver.find_element(By.CLASS_NAME, "hide-text")
    element.click()

def notify_server(amount):
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type) VALUES ({str(amount)}, {str(int(time.time()))}, {str(channel_id)}, 'Alipay');")
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

def main():
    try:
        last_balance = get_balance()
    except Exception as e:
        print(f"发生错误: {e}")
        input("如果遇到扫码, 请手动扫描, 排除故障后按任意键继续")
        print("已刷新页面")
        driver.refresh()
        try:
            last_balance = get_balance()
        except Exception as e:
            print(f"发生错误: {e}")
            print("程序已结束")
            sys.exit()
    
    while True:
        try:
            time.sleep(5)
            hide_balance()
            time.sleep(0.2)
            balance = get_balance()
            print(f"账户余额: {str(balance)}")
            if balance != last_balance:
                balance_chance = balance - last_balance
                last_balance = balance
                if balance_chance < 0:
                    continue
                print(f"支付宝到账: {balance_chance}")
                notify_server(balance_chance)
        except KeyboardInterrupt:
            driver.quit()
            sys.exit()
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
