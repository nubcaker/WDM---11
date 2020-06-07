import random
from typing import List


from locust import HttpLocust, TaskSet, TaskSequence, seq_task, between

# replace the example urls and ports with the appropriate ones
ORDER_URL = "https://localhost:5001"


#ORDER_URL = "https://wdmorleans.azurewebsites.net/"
PAYMENT_URL = ORDER_URL
STOCK_URL = PAYMENT_URL
USER_URL = STOCK_URL


# STOCK
def subtract_stock(self, item_idx: int, amount: int):
    self.client.post(f"{STOCK_URL}/stock/subtract/{self.item_ids[item_idx]}/{amount}",
                     name="/stock/subtract/[item_id]/[number]")


def find_stock(self, item_idx: int):
    response = self.client.post(f"{STOCK_URL}/stock/find/{self.item_ids[item_idx]}",
                    name="/stock/find/[item_id]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def add_stock(self, item_idx: int):
    stock_to_add = random.randint(100, 1000)
    self.client.post(f"{STOCK_URL}/stock/add/{self.item_ids[item_idx]}/{stock_to_add}",
                     name="/stock/add/[item_id]/[number]")


def create_item(self):
    price = random.randint(1, 10)
    response = self.client.post(f"{STOCK_URL}/stock/item/create/{price}", name="/stock/item/create/[price]",verify = False)
    self.item_ids.append(response.json()['item_id'])


def make_items_stock_zero(self, item_idx: int):
    stock_to_subtract = self.client.get(f"{STOCK_URL}/stock/find/{self.item_ids[item_idx]}",
                                        name="/stock/find/[item_id]").json()['stock']
    self.client.post(f"{STOCK_URL}/stock/subtract/{self.item_ids[item_idx]}/{stock_to_subtract}",
                     name="/stock/subtract/[item_id]/[number]")


# USER
def create_user(self):
    response = self.client.post(f"{USER_URL}/users/create", name="/users/create/")
    self.user_id = response.json()['user_id']


def remove_user(self, id: int):
    response = self.client.post(f"{USER_URL}/users/remove/{id}", name="/users/remove/[id]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def find_user(self):
    response = self.client.post(f"{STOCK_URL}/user/find/{self.user_id}",
                                name="/user/find/[user_id]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def subtract_balance_from_user(self, amount: int):
    response = self.client.post(f"{USER_URL}/users/credit/subtract/{self.user_id}/{amount}",
                     name="/users/credit/subtract/[user_id]/[amount]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def add_balance_to_user(self):
    balance_to_add = random.randint(10000, 100000)
    self.client.post(f"{USER_URL}/users/credit/add/{self.user_id}/{balance_to_add}",
                     name="/users/credit/add/[user_id]/[amount]")


# ORDER
def create_order(self):
    response = self.client.post(f"{ORDER_URL}/orders/create/{self.user_id}", name="/orders/create/[user_id]")
    self.order_id = response.json()['order_id']


def remove_order(self):
    response = self.client.post(f"{ORDER_URL}/orders/remove/{self.order_id}", name="/orders/remove/[order_id]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def find_order(self):
    response = self.client.post(f"{ORDER_URL}/orders/find/{self.order_id}", name="/orders/find/[order_id]")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def add_item_to_order(self, item_idx: int):
    response = self.client.post(f"{ORDER_URL}/orders/addItem/{self.order_id}/{self.item_ids[item_idx]}",
                                name="/orders/addItem/[order_id]/[item_id]", catch_response=True)
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def remove_item_from_order(self, item_idx: int):
    response = self.client.delete(f"{ORDER_URL}/orders/removeItem/{self.order_id}/{self.item_ids[item_idx]}",
                                  name="/orders/removeItem/[order_id]/[item_id]", catch_response=True)
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def checkout_order(self):
    response = self.client.post(f"{ORDER_URL}/orders/checkout/{self.order_id}", name="/orders/checkout/[order_id]",
                                catch_response=True)
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def checkout_order_that_is_supposed_to_fail(self, reason: int):
    response = self.client.post(f"{ORDER_URL}/orders/checkout/{self.order_id}", name="/orders/checkout/[order_id]",
                                catch_response=True)
    if 400 <= response.status_code < 500:
        response.success()
    else:
        if reason == 0:
            response.failure("This was supposed to fail: Not enough stock")
        else:
            response.failure("This was supposed to fail: Not enough credit")


# Payment
def payment_pay(self):
    response = self.client.post(f"{PAYMENT_URL}/payment/pay/{self.user_id}/{self.order_id}/0",name="/pay/[user_id]/[order_id]/0")
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


def cancel_payment(self):
    self.client.post(f"{PAYMENT_URL}/payment/cancel/{self.user_id}/{self.order_id}",name="/cancel/[user_id]/[order_id]")
    response = self.client.get(f"{PAYMENT_URL}/payment/status/{self.order_id}",name="/status/[order_id]").json()["paid"]
    if(response == True):
        response.failure("Payment was not properly canceled")
    else:
        response.success()


def payment_status(self):
    response = self.client.get(f"{PAYMENT_URL}/payment/status/{self.order_id}",name="/status/[order_id]").json()
    if 400 <= response.status_code < 600:
        response.failure(response.text)
    else:
        response.success()


class LoadTest1(TaskSequence):
    """
    Scenario where a stock admin creates an item and adds stock to it
    """
    item_ids: List[int]

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.item_ids = list()

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        self.item_ids = list()

    @seq_task(1)
    def admin_creates_item(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item(self): add_stock(self, 0)


class LoadTest2(TaskSequence):
    """
    Scenario where a user checks out an order with one item inside that an admin has added stock to before
    """
    item_ids: List[int]
    user_id: int
    order_id: int

    def on_start(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    def on_stop(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    @seq_task(1)
    def admin_creates_item(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @seq_task(3)
    def user_creates_account(self): create_user(self)

    @seq_task(4)
    def user_adds_balance(self): add_balance_to_user(self)

    @seq_task(5)
    def user_creates_order(self): create_order(self)

    @seq_task(6)
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @seq_task(7)
    def user_checks_out_order(self): checkout_order(self)
    
    @seq_task(8)
    def payment_is_cancelled(self): cancel_payment(self)


class LoadTest3(TaskSequence):
    """
    Scenario where a user checks out an order with two items inside that an admin has added stock to before
    """
    item_ids: List[int]
    user_id: int
    order_id: int

    def on_start(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    def on_stop(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    @seq_task(1)
    def admin_creates_item1(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item1(self): add_stock(self, 0)

    @seq_task(3)
    def admin_creates_item2(self): create_item(self)

    @seq_task(4)
    def admin_adds_stock_to_item2(self): add_stock(self, 1)

    @seq_task(5)
    def user_creates_account(self): create_user(self)

    @seq_task(6)
    def user_adds_balance(self): add_balance_to_user(self)

    @seq_task(7)
    def user_creates_order(self): create_order(self)

    @seq_task(8)
    def user_adds_item1_to_order(self): add_item_to_order(self, 0)

    @seq_task(9)
    def user_adds_item2_to_order(self): add_item_to_order(self, 1)

    @seq_task(10)
    def user_checks_out_order(self): checkout_order(self)


class LoadTest4(TaskSequence):
    """
    Scenario where a user adds an item to an order, regrets it and removes it and then adds it back and checks out
    """
    item_ids: List[int]
    user_id: int
    order_id: int

    def on_start(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    def on_stop(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    @seq_task(1)
    def admin_creates_item(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @seq_task(3)
    def user_creates_account(self): create_user(self)

    @seq_task(4)
    def user_adds_balance(self): add_balance_to_user(self)

    @seq_task(5)
    def user_creates_order(self): create_order(self)

    @seq_task(6)
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @seq_task(7)
    def user_removes_item_from_order(self): remove_item_from_order(self, 0)

    @seq_task(8)
    def user_adds_item_to_order_again(self): add_item_to_order(self, 0)

    @seq_task(9)
    def user_checks_out_order(self): checkout_order(self)


class LoadTest5(TaskSequence):
    """
    Scenario that is supposed to fail because the second item does not have enough stock
    """
    item_ids: List[int]
    user_id: int
    order_id: int

    def on_start(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    def on_stop(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    @seq_task(1)
    def admin_creates_item1(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item1(self): add_stock(self, 0)

    @seq_task(3)
    def admin_creates_item2(self): create_item(self)

    @seq_task(4)
    def admin_adds_stock_to_item2(self): add_stock(self, 1)

    @seq_task(5)
    def user_creates_account(self): create_user(self)

    @seq_task(6)
    def user_adds_balance(self): add_balance_to_user(self)

    @seq_task(7)
    def user_creates_order(self): create_order(self)

    @seq_task(8)
    def user_adds_item1_to_order(self): add_item_to_order(self, 0)

    @seq_task(9)
    def user_adds_item2_to_order(self): add_item_to_order(self, 1)

    @seq_task(10)
    def stock_admin_makes_item2s_stock_zero(self): make_items_stock_zero(self, 1)

    @seq_task(11)
    def user_checks_out_order(self): checkout_order_that_is_supposed_to_fail(self, 0)


class LoadTest6(TaskSequence):
    """
    Scenario that is supposed to fail because the user does not have enough credit
    """
    item_ids: List[int]
    user_id: int
    order_id: int

    def on_start(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    def on_stop(self):
        self.item_ids = list()
        self.user_id = -1
        self.order_id = -1

    @seq_task(1)
    def admin_creates_item(self): create_item(self)

    @seq_task(2)
    def admin_adds_stock_to_item(self): add_stock(self, 0)

    @seq_task(3)
    def user_creates_account(self): create_user(self)

    @seq_task(4)
    def user_creates_order(self): create_order(self)

    @seq_task(5)
    def user_adds_item_to_order(self): add_item_to_order(self, 0)

    @seq_task(6)
    def user_checks_out_order(self): checkout_order_that_is_supposed_to_fail(self, 1)


class LoadTest7(TaskSequence):
    pass

class LoadTests(TaskSet):
    # [TaskSequence]: [weight of the TaskSequence]
    tasks = {
        LoadTest1: 5,
        LoadTest2: 30,
        LoadTest3: 25,
        LoadTest4: 20,
        LoadTest5: 10,
        LoadTest6: 10
    }


class MicroservicesUser(HttpLocust):
    task_set = LoadTests
    wait_time = between(1, 15)  # how much time a user waits (seconds) to run another TaskSequence