import threading
import time
from .query import QueryBills
from .defines import UnpaidBill
from typing import Callable
import asyncio

import requests
def get_time():
    import time
    return int(requests.post("http://api.potatoblock.top/api/time/timestamp").json())

class Bills:
    def __init__(self, query_bills: QueryBills):
        self.query_bills = query_bills
        self.bills = []
    
    def create(self, amount: float, channel_id: int):
        while True:
            for bill in self.bills:
                if (bill.amount == amount) and (bill.channel_id == channel_id):
                    amount += 0.01
                    continue
            break
        bill = UnpaidBill(amount, channel_id, get_time())
        self.bills.append(bill)
        return bill
    
    def callback(self, bill: UnpaidBill, callback: Callable, timeout_callback: Callable = None, params: tuple = (), timeout: int = 180):
        def check(bill: UnpaidBill, callback: Callable, timeout_callback: Callable, params: tuple, timeout: int):
            start_time = get_time()
            while True:
                if (get_time() - start_time) > timeout:
                    self.bills.remove(bill)
                    if timeout_callback:
                        timeout_callback(*params)
                        return
                    raise TimeoutError
                paid_bills = self.query_bills.by_amount(bill.amount)
                for paid_bill in paid_bills:
                    if (paid_bill.channel_id == bill.channel_id) and (paid_bill.timestamp > bill.timestamp):
                        self.bills.remove(bill)
                        paid_bill.change_finished_state(True)
                        callback(*params)
                        return
                time.sleep(2)
        
        thread = threading.Thread(target=check, args=(bill, callback, timeout_callback, params, timeout))
        thread.start()
        return thread
    
    def async_callback(self, bill: UnpaidBill, callback: Callable, timeout_callback: Callable = None, params: tuple = (), timeout: int = 180):
        def check(bill: UnpaidBill, callback: Callable, timeout_callback: Callable, params: tuple, timeout: int):
            start_time = get_time()
            while True:
                if (get_time() - start_time) > timeout:
                    self.bills.remove(bill)
                    if timeout_callback:
                        async def async_callback():
                            await timeout_callback(*params)
                        asyncio.run(async_callback())
                        return
                    raise TimeoutError
                paid_bills = self.query_bills.by_amount(bill.amount)
                for paid_bill in paid_bills:
                    if (paid_bill.channel_id == bill.channel_id) and (paid_bill.timestamp > bill.timestamp):
                        self.bills.remove(bill)
                        paid_bill.change_finished_state(True)
                        async def async_callback():
                            await callback(*params)
                        asyncio.run(async_callback())
                        return
                time.sleep(2)
        
        thread = threading.Thread(target=check, args=(bill, callback, timeout_callback, params, timeout))
        thread.start()
        return thread
    
    def wait(self, bill: UnpaidBill, timeout: int = 180):
        def check(bill: UnpaidBill, timeout: int):
            start_time = get_time()
            while True:
                if (get_time() - start_time) > timeout:
                    self.bills.remove(bill)
                    raise TimeoutError
                paid_bills = self.query_bills.by_amount(bill.amount)
                for paid_bill in paid_bills:
                    if (paid_bill.channel_id == bill.channel_id) and (paid_bill.timestamp > bill.timestamp):
                        self.bills.remove(bill)
                        paid_bill.change_finished_state(True)
                        return
                time.sleep(2)
        
        check(bill, timeout)
    
    def check(self, bill: UnpaidBill):
        paid_bills = self.query_bills.by_amount(bill.amount)
        for paid_bill in paid_bills:
            if (paid_bill.channel_id == bill.channel_id) and (paid_bill.timestamp > bill.timestamp):
                self.bills.remove(bill)
                return paid_bill
            return False
    
    def remove(self, bill: UnpaidBill):
        self.bills.remove(bill)
