from flask import Flask, request
import mysql.connector
from cfg import channel_id, mysql_info, webhook_port, good_name

import requests
def get_time():
    return int(requests.post("http://api.potatoblock.top/api/time/timestamp").json())

app = Flask(__name__)

def notify_server(amount):
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type) VALUES ({str(amount)}, {str(get_time())}, {str(channel_id)}, 'AFDian');")
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data)
    data = data.get("data", {})
    if data.get("type") == "order":
        data = data.get("order", {})
        amount = float(data.get("total_amount", "0"))
        plan_title = data.get("plan_title")
        if plan_title == good_name:
            if amount:
                notify_server(amount)
    return '{"ec":200,"em":""}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=webhook_port)
