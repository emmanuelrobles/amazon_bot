import asyncio
import json

import stores.amazon
from stores.Amazon.config import amazon_config_from_json


async def main():
    with open('config.json', 'r') as config_file:
        data = config_file.read()

    config_json = json.loads(data)

    amazon = amazon_config_from_json(config_json)

    stores.amazon.init_store(amazon).subscribe()


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
