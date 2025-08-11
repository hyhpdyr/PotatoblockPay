from API import *

# 这个要改成实际的数据库信息
mysql_info = MySQLInfo(**{
    "host": "114.51.41.91",
    "port": 9810,
    "user": "payment",
    "password": "PyIsTheBestLangInTheWorld",
    "database": "payment"
})

query_bills = QueryBills(mysql_info)
bills = Bills(query_bills)

bill = bills.create(0.01, 0)  # 金额, 通道ID
# 阻塞直到完成支付(异步或线程才能用, 否则堵到你喊妈妈)
print("start")
# 账单实例, 超时秒数(不填就是180秒)
# 超时引发 TimeoutError
bills.wait(bill, 30)
print("success")

bill = bills.create(0.01, 0)  # 金额, 通道ID
# 支付后回调，否则回调另一个函数(不阻塞)
def cb():
    print("success")
def sb():
    print("failed")
print("start")
# 创建回调函数进程
# 账单实例, 成功回调, 超时回调(不填超时就报错), 需要给回调函数传递的参数(不填就不传), 超时秒数(不填就是180秒)
# 超时引发 TimeoutError 或执行超时回调
# 返回监听器进程
bills.callback(bill, cb, sb, (), 60)
# 保持进程活跃
while True:
    pass
