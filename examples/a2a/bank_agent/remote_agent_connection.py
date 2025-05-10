import uuid
import httpx
from collections.abc import Callable

from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Task,
    TaskArtifactUpdateEvent,
    MessageSendParams,
    TaskStatusUpdateEvent,
    TaskStatus,
    TaskState,
)

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, agent_card: AgentCard, httpx_client: httpx.AsyncClient):
        self.agent_client = A2AClient(agent_card=agent_card, httpx_client=httpx_client)
        self.card = agent_card

        self.conversation_name = None
        self.conversation = None
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_task(
        self,
        request: MessageSendParams,
        task_callback: TaskUpdateCallback | None,
    ) -> Task | None:
        if self.card.capabilities.streaming:
            task = None
            if task_callback:
                task_callback(
                    Task(
                        id=request.message.taskId,
                        contextId=request.message.contextId,
                        status=TaskStatus(
                            state=TaskState.submitted,
                            message=request.message,
                        ),
                        history=[request.message],
                    ),
                    self.card,
                )
            async for response in self.agent_client.send_message_streaming(
                request.model_dump(),
                request.message.taskId,
            ):
                merge_metadata(response.root.result, request)
                # For task status updates, we need to propagate metadata and provide
                # a unique message id.
                if (
                    hasattr(response.root.result, 'status')
                    and hasattr(response.root.result.status, 'message')
                    and response.root.result.status.message
                ):
                    merge_metadata(
                        response.root.result.status.message, request.message
                    )
                    m = response.root.result.status.message
                    if not m.metadata:
                        m.metadata = {}
                    if 'message_id' in m.metadata:
                        m.metadata['last_message_id'] = m.metadata['message_id']
                    m.metadata['message_id'] = str(uuid.uuid4())
                if task_callback:
                    task = task_callback(response.root.result, self.card)
                if hasattr(response.root.result, 'final') and response.root.result.final:
                    break
            return task
        # Non-streaming
        response = await self.agent_client.send_message(request.model_dump(), request.message.taskId)
        merge_metadata(response.root.result, request)
        # For task status updates, we need to propagate metadata and provide
        # a unique message id.
        if (
            hasattr(response.root.result, 'status')
            and hasattr(response.root.result.status, 'message')
            and response.root.result.status.message
        ):
            merge_metadata(response.root.result.status.message, request.message)
            m = response.root.result.status.message
            if not m.metadata:
                m.metadata = {}
            if 'message_id' in m.metadata:
                m.metadata['last_message_id'] = m.metadata['message_id']
            m.metadata['message_id'] = str(uuid.uuid4())

        if task_callback:
            task_callback(response.root.result, self.card)
        return response.root.result


def merge_metadata(target, source):
    if not hasattr(target, 'metadata') or not hasattr(source, 'metadata'):
        return
    if target.metadata and source.metadata:
        target.metadata.update(source.metadata)
    elif source.metadata:
        target.metadata = dict(**source.metadata)
