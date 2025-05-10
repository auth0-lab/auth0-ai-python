import logging
import os
import click

from dotenv import load_dotenv
load_dotenv()

from hr_agent.agent import HRAgentClient
from hr_agent.task_manager import AgentTaskManager
from common.server import A2AServer
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    AgentAuthentication,
    MissingAPIKeyError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


@click.command()
@click.option('--host', default='0.0.0.0')
@click.option('--port', default=int(os.getenv("HR_AGENT_PORT", 8080)))
def main(host, port):
    try:
        agent_card = AgentCard(
            name='Staff0 HR Agent',
            description='This agent handles external verification requests about Staff0 employees made by third parties.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=HRAgentClient.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=HRAgentClient.SUPPORTED_CONTENT_TYPES,
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
            authentication=AgentAuthentication(
                schemes=['Bearer'],
                credentials=f'https://{os.getenv("HR_AUTH0_DOMAIN")}/oauth/token'
            )
        )

        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=HRAgentClient()),
            host=host,
            port=port,
        )

        server.start()
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
