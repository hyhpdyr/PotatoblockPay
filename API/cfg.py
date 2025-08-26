# Config File

# MySQL 数据库信息
mysql_info = {
    "host": "114.51.41.91",
    "port": 9810,
    "user": "payment",
    "password": "PyIsTheBestLangInTheWorld",
    "database": "payment"
}

# 支付网关密钥
secret_key = "1145141919810"

# WebAPI 服务器端口
webapi_port = 9810

# 支付方式可用通道
channels = {
    "wxpay": [0,],
    "alipay": [1,],
    "afdian": [2,],
    "trc20.usdt": [3,],
}

# 通道展示信息
channels_info = {
    0: "qrcode/0",
    1: "qrcode/1",
    2: "https://afdian.com/item/9284152e768311f092ca5254001e7c00",
    3: "TQEHNZSy9aEyr1YYvRJfRZspTS59PK5HK9",
}

# USDT 原子颗粒度(使用 USDT 支付时保留的小数位数)
usdt_atom = 0.01

# 支付网关外网 URL
base_url = "http://114.51.4.191:9810"
