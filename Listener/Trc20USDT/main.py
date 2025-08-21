import time
import mysql.connector
from decimal import Decimal
from cfg import channel_id, mysql_info, wallet_address
import requests

def get_time():
    return int(requests.post("http://api.potatoblock.top/api/time/timestamp").json())

def check_reception():
    print("USDT收款持续监听中...")
    global last_transactions_in
    global last_usdt_balance
    res = requests.get(f"https://apilist.tronscanapi.com/api/accountv2?address={wallet_address}").json()
    if last_transactions_in == res.get("transactions_in", 0):
        print(f"USDT收款量: {last_transactions_in}")
        return False
    last_transactions_in = res.get("transactions_in", 0)
    for coin in res.get("withPriceTokens", []):
        if coin["tokenId"] == "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t":
            balance = Decimal(coin["balance"]) / (10 ** coin["tokenDecimal"])
            receiving_amount = balance - last_usdt_balance
            last_usdt_balance = balance
            print(f"USDT余额: {balance}")
            print(f"USDT收款: {receiving_amount}")
            return receiving_amount

def notify_server(amount):
    try:
        with mysql.connector.connect(**mysql_info) as db:
            with db.cursor() as cursor:
                cursor.execute(f"INSERT INTO bills (amount, time, channel_id, channel_type) VALUES ({str(amount)}, {str(get_time())}, {str(channel_id)}, 'TrUSDT');")
                db.commit()
    except Exception as e:
        # 通知失败
        print(f"通知服务器失败...: {str(e)}")

def main():
    global last_transactions_in
    global last_usdt_balance
    first_request = requests.get(f"https://apilist.tronscanapi.com/api/accountv2?address={wallet_address}").json()
    last_transactions_in = first_request.get("transactions_in", 0)
    for coin in first_request.get("withPriceTokens", []):
        if coin["tokenId"] == "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t":
            last_usdt_balance = Decimal(coin["balance"]) / (10 ** coin["tokenDecimal"])
            print(f"USDT余额: {last_usdt_balance}")
            print(f"USDT收款量: {last_transactions_in}")
    
    while True:
        try:
            balance_chance = check_reception()
        except Exception:
            time.sleep(5)
            continue
        if balance_chance:
            notify_server(balance_chance)
        time.sleep(15)

if __name__ == "__main__":
    main()
