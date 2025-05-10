import asyncio
import os

from bank_agent.host_agent import HostAgent
from bank_agent.prompt import agent_instruction
from bank_agent.remote_agent_connection import TaskCallbackArg

from a2a.types import AgentCard, Artifact, Message, Task, TaskArtifactUpdateEvent, TaskState, TaskStatus, TaskStatusUpdateEvent

# TODO: move task_callback stuff to a different file/class
_tasks: list[Task] = []
_task_map: dict[str, str] = {} # Map of message id to task id
# Map to manage 'lost' message ids until protocol level id is introduced
_next_id = {}  # dict[str, str]: previous message to next message
_artifact_chunks = {}

def add_task(task: Task):
    _tasks.append(task)

def add_or_get_task(task: TaskStatusUpdateEvent | TaskArtifactUpdateEvent):
    current_task = next(
        filter(lambda x: x.id == task.taskId, _tasks), None
    )
    if not current_task:
        conversation_id = None
        if task.metadata and 'conversation_id' in task.metadata:
            conversation_id = task.metadata['conversation_id']
        current_task = Task(
            id=task.taskId,
            contextId=conversation_id,
            status=TaskStatus(
                state=TaskState.submitted, # initialize with submitted
            ),
            metadata=task.metadata,
            artifacts=[],
        )
        add_task(current_task)
        return current_task

    return current_task

def attach_message_to_task(message: Message | None, task_id: str):
    if message and message.metadata and 'message_id' in message.metadata:
        _task_map[message.metadata['message_id']] = task_id

def insert_message_history(task: Task, message: Message | None):
    if not message:
        return
    if task.history is None:
        task.history = []
    message_id = get_message_id(message)
    if not message_id:
        return
    if get_message_id(task.status.message) not in [
        get_message_id(x) for x in task.history
    ]:
        task.history.append(task.status.message)
    else:
        print(
            'Message id already in history',
            get_message_id(task.status.message),
            task.history,
        )

def insert_message_history(task: Task, message: Message | None):
    if not message:
        return
    if task.history is None:
        task.history = []
    message_id = get_message_id(message)
    if not message_id:
        return
    if get_message_id(task.status.message) not in [
        get_message_id(x) for x in task.history
    ]:
        task.history.append(task.status.message)
    else:
        print(
            'Message id already in history',
            get_message_id(task.status.message),
            task.history,
        )

def update_task(task: Task):
    for i, t in enumerate(_tasks):
        if t.id == task.id:
            _tasks[i] = task
            return

def insert_id_trace(message: Message | None):
        if not message:
            return
        message_id = get_message_id(message)
        last_message_id = get_last_message_id(message)
        if message_id and last_message_id:
            _next_id[last_message_id] = message_id

def process_artifact_event(
    current_task: Task, task_update_event: TaskArtifactUpdateEvent
):
    artifact = task_update_event.artifact
    if not task_update_event.append:
        # received the first chunk or entire payload for an artifact
        if task_update_event.lastChunk is None or task_update_event.lastChunk:
            # lastChunk bit is missing or is set to true, so this is the entire payload
            # add this to artifacts
            if not current_task.artifacts:
                current_task.artifacts = []
            current_task.artifacts.append(artifact)
        else:
            # this is a chunk of an artifact, stash it in temp store for assembling
            if task_update_event.taskId not in _artifact_chunks:
                _artifact_chunks[task_update_event.taskId] = {}
            _artifact_chunks[task_update_event.taskId][artifact.artifactId] = (
                artifact
            )
    else:
        # we received an append chunk, add to the existing temp artifact
        current_temp_artifact: Artifact = _artifact_chunks[task_update_event.taskId][
            artifact.artifactId
        ]
        # TODO handle if current_temp_artifact is missing
        current_temp_artifact.parts.extend(artifact.parts)
        if task_update_event.lastChunk:
            current_task.artifacts.append(current_temp_artifact)
            del _artifact_chunks[task_update_event.taskId][artifact.artifactId]

def get_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or 'message_id' not in m.metadata:
        return None
    return m.metadata['message_id']

def get_last_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or 'last_message_id' not in m.metadata:
        return None
    return m.metadata['last_message_id']

def task_callback(task: TaskCallbackArg, agent_card: AgentCard):
    if isinstance(task, TaskStatusUpdateEvent):
        current_task = add_or_get_task(task)
        current_task.status = task.status
        attach_message_to_task(task.status.message, current_task.id)
        insert_message_history(current_task, task.status.message)
        update_task(current_task)
        insert_id_trace(task.status.message)
        return current_task
    
    if isinstance(task, TaskArtifactUpdateEvent):
        current_task = add_or_get_task(task)
        process_artifact_event(current_task, task)
        update_task(current_task)
        return current_task
    
    # Otherwise this is a Task, either new or updated
    if not any(filter(lambda x: x.id == task.id, _tasks)):
        attach_message_to_task(task.status.message, task.id)
        insert_id_trace(task.status.message)
        add_task(task)
        return task
    
    attach_message_to_task(task.status.message, task.id)
    insert_id_trace(task.status.message)
    update_task(task)
    return task

def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass

    return asyncio.run(coro)

agent_instance = HostAgent(
    remote_agent_addresses=[
        os.getenv('HR_AGENT_BASE_URL'), # Staff0's HR Agent (TODO: specify M2M client id and secret)
    ],
    name='bank_agent',
    instruction=agent_instruction,
    description=(
        'This agent helps users open accounts step by step.'
        'Also, it is responsible for selecting a remote agent to validate the user\'s employment status and coordinate its work.'
    ),
    task_callback=task_callback,
)

root_agent = _run_async(agent_instance.create_agent())
