import os
import click

from dotenv import load_dotenv
load_dotenv()

from hr_agent.agent import HRAgent
from hr_agent.agent_executor import HRAgentExecutor
from a2a.server import A2AServer, InMemoryTaskStore, DefaultA2ARequestHandler
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AgentAuthentication,
)

@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=int(os.getenv("HR_AGENT_PORT", 8080)))
def main(host: str, port: int):
    task_store = InMemoryTaskStore()

    request_handler = DefaultA2ARequestHandler(
        agent_executor=HRAgentExecutor(task_store=task_store),
        task_store=task_store,
    )

    server = A2AServer(
        agent_card=get_agent_card(host, port), request_handler=request_handler
    )

    server.start(host=host, port=port)


def get_agent_card(host: str, port: int):
    return AgentCard(
        name='Staff0 HR Agent',
        description='This agent handles external verification requests about Staff0 employees made by third parties.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        defaultInputModes=HRAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=HRAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id='is_active_employee',
                name='Check Employment Status Tool',
                description='Confirm whether a person is an active employee of the company.',
                tags=['employment'],
                examples=[
                    'Is John Doe (with email jdoe@staff0.com) an active employee?'
                ],
            )
        ],
        authentication=AgentAuthentication(schemes=['public']),
        # authentication=AgentAuthentication(
        #     schemes=['Bearer'],
        #     credentials=f'https://{os.getenv("HR_AUTH0_DOMAIN")}/oauth/token'
        # )
    )

if __name__ == '__main__':
    main()
