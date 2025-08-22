import hashlib
import websocket
import threading
import json
import time
from typing import Union, Callable
from decimal import Decimal

class Bills:
    def __init__(self, ws_url: str, token: str):
        self.tk = token
        self.url = ws_url
        self.bills = {}
        self.recvs = []
        self.cb_threads = []
        self.connect()
    
    def auth(self):
        self.ws.send(json.dumps({
            "action": "auth"
        }))
        data = json.loads(self.ws.recv())
        if data.get("code") != 200:
            return False
        self.ws.send(json.dumps({
            "action": "auth",
            "sign": ws_md5_sign(data.get("str", ""), self.tk)
        }))
        data = json.loads(self.ws.recv())
        if data.get("code") != 200:
            return False
        return True
    
    def reconnect(self):
        self.disconnect()
        self.connect()
    
    def connect(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.url)
        if not self.auth():
            raise ConnectionError
        self.handler()
    
    def disconnect(self):
        if self.ws:
            self.ws.close()
        self.ws = None
        self.handler_thread = None
        self.bills = {}
        self.recvs = []
        self.cb_threads = []
    
    def handler(self):
        def ws_handler(self):
            while True:
                try:
                    data = json.loads(self.ws.recv())
                    print(data)
                    if data.get("action") == "callback":
                        try:
                            callback_thread = threading.Thread(
                                target=self.bills.get(data.get("id"), {}).get("function"),
                                args=(
                                    data.get("success"),
                                    *self.bills.get(data.get("id"), {}).get("args")
                                )
                            )
                            callback_thread.start()
                            self.cb_threads.append(callback_thread)
                            del self.bills[data.get("id")]
                        except Exception:
                            pass
                    else:
                        self.recvs.append(data)
                except Exception:
                    time.sleep(0.1)
                    if self.ws:
                        self.reconnect()
                    return
        
        self.handler_thread = threading.Thread(target=ws_handler, args=(self,))
        self.handler_thread.start()
    
    def create(self, amount: Decimal, channel: Union[int, str], callback: Callable, args: tuple = (), timeout: int = 180):
        if type(channel) == int:
            self.ws.send(json.dumps({
                "action": "submit",
                "amount": float(amount),
                "channel": channel,
                "timeout": timeout
            }))
        elif type(channel) == str:
            self.ws.send(json.dumps({
                "action": "submit",
                "amount": float(amount),
                "type": channel,
                "timeout": timeout
            }))
        else:
            raise TypeError
        while True:
            try:
                data = self.recvs[-1]
                if data.get("action") != "submit":
                    continue
                if data.get("code") != 200:
                    raise TypeError
                self.bills[data.get("id", "")] = {
                    "function": callback,
                    "args": args
                }
                self.recvs.pop()
                return {
                    "real_amount": data.get("real_amount"),
                    "channel_id": data.get("channel")
                }
            except Exception:
                pass

def ws_md5_sign(param, key):
    param += key
    md5=hashlib.md5(param.encode())
    return md5.hexdigest()

if __name__ == "__main__":
    # 回调函数
    def cb(succ, *args):
        print(succ)
        print(args)
    # 连接到支付网关服务器
    # 服务器地址, 网关密钥
    bills = Bills("ws://114.51.41.91:9810/ws", "1145141919810")
    print("初始化成功")
    # 创建 1 元的爱发电订单, 回调函数为 cb , 传递参数 (是否成功, 1, 2, 3), 支付超时时间 2 秒
    # 金额, 支付方式或通道 ID (传入str则为支付方式, int则为通道 ID), 回调函数, 业务参数(非必填), 超时秒数(默认 180 秒)
    res = bills.create(Decimal("1"), "afdian", cb, (1, 2, 3), 2)
    # 打印含有真实金额与通道 ID 的服务器回传数据
    print(res)
    #bills.disconnect()
    try:
        # 保持主线程活跃
        while True:
            pass
    except KeyboardInterrupt:
        # 处理用户按下 Ctrl+C 后退出程序
        bills.disconnect()
        import sys
        sys.exit(0)
