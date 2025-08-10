import mysql.connector
import threading
import time
from .query import QueryBills
from .defines import UnpaidBill
from typing import Callable

class Bills:
    def __init__(self, query_bills: QueryBills):
        self.query_bills = query_bills
        self.bills = []
    
    def create(self, amount: float, channel_type: str):
        while True:
            for bill in self.bills:
                if (bill.amount == amount) and (bill.channel_type == channel_type):
                    amount += 0.01
                    continue
            break
        bill = UnpaidBill(amount, channel_type)
        self.bills.append(bill)
        return bill
    
    def callback(self, bill: UnpaidBill, callback: Callable, timeout_callback: Callable = None, params: tuple = (), timeout: int = 180):
        def check(bill: UnpaidBill, callback: Callable, timeout_callback: Callable, params: tuple, timeout: int):
            start_time = int(time.time())
            while True:
                if (int(time.time()) - start_time) > timeout:
                    self.bills.remove(bill)
                    if timeout_callback:
                        timeout_callback(*params)
                        return
                    raise TimeoutError
                paid_bills = self.query_bills.by_amount(bill.amount)
                for paid_bill in paid_bills:
                    if (paid_bill.channel_type == bill.channel_type) and (paid_bill.timestamp > start_time):
                        self.bills.remove(bill)
                        paid_bill.change_finished_state(True)
                        callback(*params)
                        return
                time.sleep(2)
        
        thread = threading.Thread(target=check, args=(bill, callback, timeout_callback, params, timeout))
        thread.start()
        return thread
    
    def wait(self, bill: UnpaidBill, timeout: int = 180):
        def check(bill: UnpaidBill, timeout: int):
            start_time = int(time.time())
            while True:
                if (int(time.time()) - start_time) > timeout:
                    self.bills.remove(bill)
                    raise TimeoutError
                paid_bills = self.query_bills.by_amount(bill.amount)
                for paid_bill in paid_bills:
                    if (paid_bill.channel_type == bill.channel_type) and (paid_bill.timestamp > start_time):
                        self.bills.remove(bill)
                        paid_bill.change_finished_state(True)
                        return
                time.sleep(2)
        
        check(bill, timeout)
    
    def remove(self, bill: UnpaidBill):
        self.bills.remove(bill)
