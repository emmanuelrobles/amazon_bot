from stores.Amazon.models import AmazonProduct


class AmazonBotFoundException(Exception):
    def __init__(self, proxies: dict, url: str):
        self.proxies = proxies
        self.url = url

