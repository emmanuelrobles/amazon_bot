from models.communication import Action
from stores.Amazon.Models import AmazonProductFoundAction, AmazonProductNotFoundAction


def on_product_found(payload: AmazonProductFoundAction) -> Action[AmazonProductFoundAction]:
    return Action("amazon_product_found", payload)


def on_not_product_found(payload: AmazonProductNotFoundAction) -> Action[AmazonProductNotFoundAction]:
    return Action("amazon_not_product_found", payload)
