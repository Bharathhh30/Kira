import asyncio
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "Experiments", "Kira", "backend", ".env")
load_dotenv(dotenv_path=env_path)

from livekit import api

async def main():
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    lk_api = api.LiveKitAPI(
        url=url,
        api_key=api_key,
        api_secret=api_secret
    )
    async with lk_api:
        req = api.ListAgentDispatchRequest()
        req.room = "3b86b1bb-4569-4db8-b786-d828749e1d08"
        res = await lk_api.agent_dispatch.list_dispatch(req)
        print("Dispatches list:", res)

if __name__ == "__main__":
    asyncio.run(main())
