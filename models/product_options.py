from models.enums import StoresEnum


class ProductOptions:
    def __init__(self, store: StoresEnum, url: str, username: str, password: str, qty: int, price: float):
        self.store = store
        self.url = url
        self.username = username
        self.password = password
        self.qty = qty
        self.price = price
