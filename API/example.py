from API import *

mysql_info = MySQLInfo(**{
    "host": "114.51.41.91",
    "port": 9810,
    "user": "payment",
    "password": "PyIsTheBestLangInTheWorld",
    "database": "payment"
})

a = Query(mysql_info).by_id(114)[0].change_finished_state(True)
print(a.as_dict())
