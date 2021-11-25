from models.communication import Action
from stores.Amazon.models import AmazonProductFoundAction, AmazonProductNotFoundAction


def on_product_found(payload: AmazonProductFoundAction) -> Action[AmazonProductFoundAction]:
    return Action("amazon_product_found", payload)


def on_product_not_found(payload: AmazonProductNotFoundAction) -> Action[AmazonProductNotFoundAction]:
    return Action("amazon_product_not_found", payload)
