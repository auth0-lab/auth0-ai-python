from src.agents.clients.scheduler import SchedulerClient
from langchain_auth0_ai.ciba.ciba_poller_graph import ciba_poller_graph

async def on_stop_scheduler(state):
    await SchedulerClient().stop(state['task_id'])

ciba_graph = ciba_poller_graph(on_stop_scheduler)
graph = ciba_graph.compile()
