import re
import time
import uiautomation as automation
import os
import mysql.connector
from cfg import channel_id, mysql_info

last_matched_info = None
start_up = True

def explore_control(control, depth, target_depth):
    global last_matched_info
    try:
        name = control.Name
        if name:
            if depth == target_depth:
                # 匹配收款金额信息
                last_matched_info = ""
                match = re.search(r'收款金额￥([\d.]+)', name)
                if match:
                    global amount
                    amount = match.group(1)
                    amount = float(amount)
                    last_matched_info += f"\n收款金额: {amount}"
                
                match = re.search(r'付款方备注(.*)汇总(.*)备注(.*)', name)
                global ps
                if match:
                    ps = match.group(1)
                    last_matched_info += f"\n收款备注: {ps}"
                else:
                    ps = None

                # 匹配收款备注与汇总信息
                match = re.search(r'汇总(.*)备注(.*)', name)
                if match:
                    global summary
                    summary = match.group(1)
                    match = re.search(r'今日第(\d+)笔收款，共计￥([\d.]+)', name)
                    if match:
                        total_receipts = match.group(1)
                        total_receipts = int(total_receipts)
                        total_amount = match.group(2)
                        total_amount = float(total_amount)
                        summary = {
                            "total_receipts": total_receipts,
                            "total_amount": total_amount
                        }
                        last_matched_info += f"\n收款总笔: {total_receipts}\n收款总额: {total_amount}"
                return
        # 递归处理子控件
        for child in control.GetChildren():
            explore_control(child, depth + 4, target_depth)
    except Exception as e:
        print(f"发生错误: {str(e)}")

def process_wechat_window(wechat_window, prev_info):
    global last_matched_info
    global start_up
    if wechat_window.Exists(0):
        explore_control(wechat_window, 0, 60)
        if last_matched_info and last_matched_info != prev_info:
            prev_info = last_matched_info
            if start_up:
                start_up = False
                if os.path.exists("not_first_use.sig"):
                    return prev_info
                else:
                    with open("not_first_use.sig", "w") as f:
                        pass
            print(last_matched_info)
            print("持续监听中...")
            
            # 向服务器发送请求
            notify_server()

    else:
        print("无法获取到窗口，请保持微信支付窗口显示...")
    return prev_info

def notify_server():
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type, notes) VALUES ({str(amount)}, {str(int(time.time()))}, {str(channel_id)}, 'WeChat', %s);", (ps,))
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

def main():
    global last_matched_info
    prev_info = None
    try:
        # 获取微信窗口
        wechat_window = automation.WindowControl(searchDepth=1, ClassName='ChatWnd')
        prev_info = process_wechat_window(wechat_window, prev_info)
        print("已获取到微信窗口")
    except Exception as e:
        print(f"发生错误: {str(e)}")
    
    while True:
        try:
            # 持续监听微信窗口
            wechat_window = automation.WindowControl(searchDepth=1, ClassName='ChatWnd')
            prev_info = process_wechat_window(wechat_window, prev_info)
        except Exception as e:
            print(f"发生错误: {str(e)}")
    
        time.sleep(1)

if __name__ == "__main__":
    print("程序已启动...")
    main()
