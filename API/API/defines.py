from dataclasses import dataclass
import mysql.connector

@dataclass(frozen=True)
class MySQLInfo:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306

    def as_dict(self):
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database
        }

@dataclass(frozen=True)
class BillData:
    bill_id: int
    amount: float
    notes: str
    timestamp: int
    channel_id: int
    channel_type: str
    finished: bool
    mysql_info: MySQLInfo

    def as_dict(self):
        return {
            "bill_id": self.bill_id,
            "amount": self.amount,
            "notes": self.notes,
            "timestamp": self.timestamp,
            "channel_id": self.channel_id,
            "channel_type": self.channel_type,
            "finished": self.finished
        }
    
    def change_finished_state(self, finished):
        try:
            with mysql.connector.connect(**self.mysql_info.as_dict()) as db:
                with db.cursor() as cursor:
                    cursor.execute(f"UPDATE bills SET finished = {'1' if finished else '0'} WHERE bill_id = {str(self.bill_id)};")
                    db.commit()
                    new_bill_data = self.as_dict()
                    new_bill_data["finished"] = finished
                    new_bill_data["mysql_info"] = self.mysql_info
                    return BillData(**new_bill_data)
        except Exception as e:
            print(f"更新数据库失败...: {str(e)}")

@dataclass(frozen=True)
class UnpaidBill:
    amount: float
    channel_id: int
    timestamp: int

    def as_dict(self):
        return {
            "amount": self.amount,
            "channel_id": self.channel_id,
            "timestamp": self.timestamp
        }
