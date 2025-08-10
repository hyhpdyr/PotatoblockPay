from API import *

mysql_info = MySQLInfo(**{
    "host": "114.51.41.91",
    "port": 9810,
    "user": "payment",
    "password": "PyIsTheBestLangInTheWorld",
    "database": "payment"
})

query_bills = QueryBills(mysql_info)
bills = Bills(query_bills)
bill = bills.create(0.01, "Alipay")
print("start")
bills.wait(bill)
print("success")
