from API import *
from cfg import mysql_info, secret_key, webapi_port, channels, channels_info, base_url
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import asyncio
import uvicorn
from decimal import Decimal
import string
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

app = FastAPI()
templates = Jinja2Templates(directory="templates")

mysql_info = MySQLInfo(**mysql_info)
query_bills = QueryBills(mysql_info)
bills = Bills(query_bills)

@app.post("/submit")
async def submit(data: Request):
    data = await data.body()
    data = data.decode("utf-8")
    data = json.loads(data)
    return_data = {}
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
        usdt_price = await asyncio.to_thread(get_usdt_price)
        data["real_amount"] = int((data["real_amount"] * 1000000) / usdt_price) / 1000000
        timeout_time = 600
    bill = bills.create(float(data.get("real_amount")), int(data.get("channel")))
    bills.callback(bill, success_callback, failed_callback, (data,), timeout_time)
    data["real_amount"] = bill.amount
    return_data["status_code"] = 200
    return_data["message"] = "ok"
    return_data["payment_url"] = f"{base_url}/pay?method={data.get('trade_type', 'afdian')}&channel={data.get('channel')}&amount={data.get('real_amount')}&timeout={timeout_time}&trade={data.get('order_id')}&redirect={data.get('redirect_url')}"
    return return_data

@app.get("/pay")
async def pay(request: Request, amount: float, method: str, channel: int, timeout: str, trade: str, redirect: str):
    context = {
        "request": request,
        "amount": str(amount) + " " + ("USDT" if "usdt" in method else "CNY"),
        "pay_info": channels_info.get(channel) or "无",
        "pay_method": method,
        "timeout_time": timeout,
        "trade_no": trade,
        "redirect_url": redirect
    }
    return templates.TemplateResponse(name="pay.html", context=context)

@app.get("/qrcode/{channel}")
async def qrcode(channel: int):
    try:
        qrcode_img = await asyncio.to_thread(get_qrcode, int(channel))
        return qrcode_img
    except Exception:
        return ""

@app.get("/favicon.ico")
async def favicon():
    try:
        if Path("favicon.ico").exists():
            return FileResponse("favicon.ico")
    except Exception:
        return ""

@app.websocket("/ws")
async def ws_handler(ws: WebSocket):
    try:
        await ws.accept()
        
        auth_data = await ws.receive_text()
        auth_data = json.loads(auth_data)
        if auth_data.get("action") != "auth":
            await ws.send_text(json.dumps({
                "code": 403,
                "action": "auth",
                "msg": "No auth."
            }))
            raise WebSocketDisconnect
        sign_str = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        await ws.send_text(json.dumps({
            "code": 200,
            "action": "auth",
            "str": sign_str
        }))
        auth_data = await ws.receive_text()
        auth_data = json.loads(auth_data)
        if (auth_data.get("action") != "auth") or (auth_data.get("sign") != ws_md5_sign(sign_str, secret_key)):
            await ws.send_text(json.dumps({
                "code": 403,
                "action": "auth",
                "msg": "Sign error."
            }))
            raise WebSocketDisconnect
        await ws.send_text(json.dumps({
            "code": 200,
            "action": "auth",
            "msg": "Auth accept."
        }))
        del auth_data
        
        while True:
            data = await ws.receive_text()
            data = json.loads(data)
            if data.get("action") == "auth":
                await ws.send_text(json.dumps({
                    "code": 200,
                    "action": "auth",
                    "msg": "Auth accept."
                }))
                continue
            
            if data.get("action") == "submit":
                if (float(data.get("amount", "0.0")) > 0.0) and ((int(data.get("channel", "-1")) >= 0) or data.get("type", "")):
                    bill_id = "".join(random.choice(string.digits) for _ in range(16))
                    if int(data.get("channel", "-1")) >= 0:
                        channel_id = int(data.get("channel"))
                    else:
                        if len(channels.get(data.get("type"), [])) > 0:
                            channel_id = random.choice(channels.get(data.get("type"), []))
                        else:
                            await ws.send_text(json.dumps({
                                "code": 404,
                                "action": "submit",
                                "msg": "Type is not available."
                            }))
                            continue
                    bill = bills.create(
                        float(data.get("amount", "0.0")),
                        int(data.get("channel", "-1"))
                    )
                    bills.async_callback(
                        bill,
                        ws_success_callback,
                        ws_failed_callback,
                        (
                            ws,
                            {
                                "id": bill_id,
                                "channel": channel_id,
                                "amount": float(data.get("amount", "0.0")),
                                "real_amount": bill.amount
                            }
                        ),
                        int(data.get("timeout", "180"))
                    )
                    await ws.send_text(json.dumps({
                        "code": 200,
                        "action": "submit",
                        "id": bill_id,
                        "channel": channel_id,
                        "amount": float(data.get("amount", "0.0")),
                        "real_amount": bill.amount,
                        "msg": "Success."
                    }))
                else:
                    await ws.send_text(json.dumps({
                        "code": 404,
                        "action": "submit",
                        "msg": "Missing param."
                    }))
                continue
            
            await ws.send_text(json.dumps({
                "code": 404,
                "action": str(data.get("action")),
                "msg": "API not exists."
            }))
    except WebSocketDisconnect:
        print("WS连接已断开")
    except Exception as e:
        print(f"WS连接发生错误: {str(e)}")
    finally:
        await ws.close()

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

async def ws_success_callback(ws: WebSocket, data):
    print(f"订单 {data.get('id')} 回调成功")
    try:
        await ws.send_text(json.dumps({
            "code": 200,
            "action": "callback",
            "success": True,
            "id": data.get("id"),
            "channel": data.get("channel"),
            "amount": data.get("amount"),
            "real_amount": data.get("real_amount"),
            "msg": "Success."
        }))
        print(f"订单 {data.get('id')} 通知成功")
    except Exception as e:
        print(f"订单 {data.get('id')} 通知失败: {str(e)}")

async def ws_failed_callback(ws: WebSocket, data):
    print(f"订单 {data.get('id')} 超时")
    try:
        await ws.send_text(json.dumps({
            "code": 200,
            "action": "callback",
            "success": False,
            "id": data.get("id"),
            "channel": data.get("channel"),
            "amount": data.get("amount"),
            "real_amount": data.get("real_amount"),
            "msg": "Timeout."
        }))
        print(f"订单 {data.get('id')} 通知成功")
    except Exception as e:
        print(f"订单 {data.get('id')} 通知失败: {str(e)}")

def ws_md5_sign(param, key):
    param += key
    md5=hashlib.md5(param.encode())
    return md5.hexdigest()

def get_qrcode(channel_id):
    try:
        paths = [
            Path(f"qrcodes/{channel_id}.png"),
            Path(f"qrcodes/{channel_id}.jpg"),
            Path("favicon.ico")
        ]
        for path in paths:
            if path.exists():
                return FileResponse("favicon.ico")
        return ""
    except Exception:
        return ""

def run_server():
    uvicorn.run(app, host='0.0.0.0', port=webapi_port)

def main():
    run_server()

if __name__ == "__main__":
    main()
