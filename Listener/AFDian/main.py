from flask import Flask, request
import mysql.connector
from cfg import channel_id, mysql_info, webhook_path, webhook_port, good_name
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

import requests
def get_time():
    return int(requests.post("http://api.potatoblock.top/api/time/timestamp").json())

app = Flask(__name__)

def notify_server(amount, notes):
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                if notes:
                    cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type, notes) VALUES ({str(amount)}, {str(get_time())}, {str(channel_id)}, 'AFDian', %s);", (notes,))
                else:
                    cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type) VALUES ({str(amount)}, {str(get_time())}, {str(channel_id)}, 'AFDian');")
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

@app.route(webhook_path, methods=["POST"])
def webhook():
    data = request.get_json()
    data = data.get("data", {})
    order = data.get("order", {})
    if not verify_sign(f"{order.get('out_trade_no')}{order.get('user_id')}{order.get('plan_id')}{order.get('total_amount')}", data.get('sign', '')):
        print("签名验证失败")
        return '{"ec":403,"em":"sign error"}'
    print("签名验证成功")
    print(data)
    if data.get("type") == "order":
        data = data.get("order", {})
        amount = float(data.get("total_amount", "0.0"))
        notes = data.get("remark")
        plan_title = data.get("plan_title")
        if plan_title == good_name:
            if amount:
                notify_server(amount, notes)
                print("订单已入库")
    return '{"ec":200,"em":""}'

def verify_sign(sign_str, sign):
    """
    验证 RSA 签名
    
    Args:
        sign_str (str): 需要验证的原始字符串
        sign (str): Base64 编码的签名
    
    Returns:
        bool: 验证结果，True 表示签名有效，False 表示无效
    """
    # 公钥字符串
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwwdaCg1Bt+UKZKs0R54y
lYnuANma49IpgoOwNmk3a0rhg/PQuhUJ0EOZSowIC44l0K3+fqGns3Ygi4AfmEfS
4EKbdk1ahSxu7Zkp2rHMt+R9GarQFQkwSS/5x1dYiHNVMiR8oIXDgjmvxuNes2Cr
8fw9dEF0xNBKdkKgG2qAawcN1nZrdyaKWtPVT9m2Hl0ddOO9thZmVLFOb9NVzgYf
jEgI+KWX6aY19Ka/ghv/L4t1IXmz9pctablN5S0CRWpJW3Cn0k6zSXgjVdKm4uN7
jRlgSRaf/Ind46vMCm3N2sgwxu/g3bnooW+db0iLo13zzuvyn727Q3UDQ0MmZcEW
MQIDAQAB
-----END PUBLIC KEY-----"""
    
    try:
        # 加载公钥
        public_key = load_pem_public_key(PUBLIC_KEY.encode())
        
        # 解码 Base64 签名
        signature = base64.b64decode(sign)
        
        # 验证签名
        public_key.verify(
            signature,
            sign_str.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        return True
        
    except InvalidSignature:
        print("签名验证失败")
        return False
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=webhook_port)
