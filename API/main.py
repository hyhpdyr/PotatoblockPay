from API import *
from cfg import mysql_info, secret_key, webapi_port, channels, channels_info, base_url
from flask import Flask, request, render_template
from decimal import Decimal
import requests
import random
import hashlib
import json
import time

def get_usdt_price():
    try:
        return Decimal(requests.post(f"http://api.potatoblock.top/api/okx/usdt-rmb-price?ts={int(time.time())}").json())
    except Exception:
        return Decimal("7.0")

app = Flask(__name__)

mysql_info = MySQLInfo(**mysql_info)
query_bills = QueryBills(mysql_info)
bills = Bills(query_bills)

@app.route("/submit", methods=["GET", "POST"])
def submit():
    data = None
    return_data = {}
    if request.method == "POST":
        try:
            data = request.get_json()
        except Exception:
            data = request.form.to_dict()
    else:
        data = request.args.to_dict()
    signature = data.get("signature")
    if not signature:
        return_data["status_code"] = 403
        return_data["message"] = "sign not found"
        return json.dumps(return_data)
    del data["signature"]
    if signature != md5_sign(data, secret_key):
        return_data["status_code"] = 403
        return_data["message"] = "sign error"
        return json.dumps(return_data)
    data["channel"] = random.choice(channels.get(data.get("trade_type", "afdian"), []))
    timeout_time = 180
    data["real_amount"] = data["amount"]
    if "usdt" in data.get("trade_type", ""):
        data["real_amount"] = int((data["real_amount"] * 1000000) / get_usdt_price()) / 1000000
        timeout_time = 600
    bill = bills.create(float(data.get("real_amount")), int(data.get("channel")))
    bills.callback(bill, success_callback, failed_callback, (data,), timeout_time)
    data["real_amount"] = bill.amount
    return_data["status_code"] = 200
    return_data["message"] = "ok"
    return_data["payment_url"] = f"{base_url}/pay?method={data.get('trade_type', 'afdian')}&channel={data.get('channel')}&amount={data.get('real_amount')}&timeout={timeout_time}&trade={data.get('order_id')}&redirect={data.get('redirect_url')}"
    return json.dumps(return_data)

@app.route("/pay", methods=["GET"])
def pay():
    data = request.args.to_dict()
    return render_template("pay.html", amount=(data.get("amount") + " " + ("USDT" if "usdt" in data.get("method") else "元")), pay_info=(channels_info.get(int(data.get("channel"))) or "无"), pay_method=data.get("method"), timeout_time=data.get("timeout"), trade_no=data.get("trade"), redirect_url=data.get("redirect"))

@app.route("/qrcode/<channel>", methods=["GET"])
def qrcode(channel):
    try:
        return get_qrcode(int(channel))
    except Exception:
        return ""

@app.route("/favicon.ico", methods=["GET"])
def favicon():
    try:
        with open("favicon.ico", "rb") as f:
            return f.read()
    except Exception:
        return ""

def success_callback(data):
    return_data = {}
    return_data["trade_status"] = "TRADE_SUCCESS"
    return_data["order_id"] = data["order_id"]
    return_data["amount"] = data["amount"]
    return_data["status"] = 2
    return_data["signature"] = md5_sign(return_data, secret_key)
    if data.get("notify_url"):
        res = requests.get(data.get("notify_url"), json=return_data, timeout=5)
        if res.text != "ok":
            print(f"订单 {data['order_id']} 回调失败: {res.json().get('msg')}")
        else:
            print(f"订单 {data['order_id']} 回调成功")

def failed_callback(data):
    print(f"订单 {data['order_id']} 超时")

def md5_sign(params, key):
    txt = ""
    for k in sorted(params):
        v = params[k]
        if not v:
            continue
        txt += f"{str(k)}={str(v)}&"
    if txt:
        txt = txt[:-1]
    txt += key
    md5=hashlib.md5(txt.encode())
    return md5.hexdigest()

def get_qrcode(channel_id):
    try:
        with open(f"qrcodes/{channel_id}.png", "rb") as f:
            return f.read()
    except Exception:
        try:
            with open(f"qrcodes/{channel_id}.jpg", "rb") as f:
                return f.read()
        except Exception:
            with open(f"favicon.ico", "rb") as f:
                return f.read()

def main():
    app.run(host='0.0.0.0', port=webapi_port)

if __name__ == "__main__":
    main()
