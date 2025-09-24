import httpx

class SchedulerClient:
    def __init__(self, url: str = "http://localhost:5555"):
        self.url = url

    async def schedule(self, data: dict):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.url}/schedule", json=data, headers={"Content-Type": "application/json"})
        except Exception as e:
            print(e)

    async def stop(self, task_id: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{self.url}/schedule/{task_id}")
        except Exception as e:
            print(e)