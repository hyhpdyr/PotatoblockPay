import mysql.connector
from .defines import BillData, MySQLInfo

class QueryBills:
    def __init__(self, mysql_info: MySQLInfo):
        self.mysql_info = mysql_info
    
    def by_amount(self, amount, finished=False):
        try:
            with mysql.connector.connect(**self.mysql_info.as_dict()) as db:
                with db.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM bills WHERE amount = {str(amount)} AND finished = {'1' if finished else '0'};")
                    # 获取所有结果
                    bills = cursor.fetchall()
                    results = []
                    for row in bills:
                        row = list(row)
                        row[1] = float(row[1])
                        row[6] = bool(row[6])
                        row.append(self.mysql_info)
                        results.append(BillData(*row))
                    return results
        except Exception as e:
            print(f"查询数据库失败...: {str(e)}")
            return []
    
    def by_id(self, bill_id, finished=False):
        try:
            with mysql.connector.connect(**self.mysql_info.as_dict()) as db:
                with db.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM bills WHERE bill_id = {str(bill_id)} AND finished = {'1' if finished else '0'};")
                    # 获取所有结果
                    bills = cursor.fetchall()
                    results = []
                    for row in bills:
                        row = list(row)
                        row[6] = bool(row[6])
                        row.append(self.mysql_info)
                        results.append(BillData(*row))
                    return results
        except Exception as e:
            print(f"查询数据库失败...: {str(e)}")
            return []
    
    def by_notes(self, notes, finished=False):
        try:
            with mysql.connector.connect(**self.mysql_info.as_dict()) as db:
                with db.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM bills WHERE notes = '{str(notes)}' AND finished = {'1' if finished else '0'};")
                    # 获取所有结果
                    bills = cursor.fetchall()
                    results = []
                    for row in bills:
                        row = list(row)
                        row[6] = bool(row[6])
                        row.append(self.mysql_info)
                        results.append(BillData(*row))
                    return results
        except Exception as e:
            print(f"查询数据库失败...: {str(e)}")
            return []
