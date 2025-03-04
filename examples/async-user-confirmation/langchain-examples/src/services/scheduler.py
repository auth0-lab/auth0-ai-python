from flask import Flask, request, jsonify
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from langgraph_sdk import get_client
from nanoid import generate
from typing import TypedDict, Literal, Optional
import os
import asyncio
import shelve

load_dotenv()

app = Flask(__name__)
scheduler = AsyncIOScheduler()

DB_FILE = "./.scheduler"
PORT = int(os.getenv("PORT", 5555))

class Schedule(TypedDict):
    unit: Literal["seconds", "minutes", "hours", "days"]
    interval: int

class TaskData(TypedDict):
    graph_id: str
    config: dict
    input: dict
    schedule: Optional[Schedule]

async def execute_task(graph_id: str, task_id: str, data: dict):
    print(f"Executing task {task_id} | {graph_id}")
    client = get_client(base_url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
    threads = await client.threads.create()
    await client.runs.create(
        assistant_id=graph_id,
        thread_id=threads.thread_id,
        input={**data.get('input', {}), 'task_id': task_id},
        config=data.get('config')
    )

def load_tasks():
    with shelve.open(DB_FILE) as db:
        return dict(db)

def add_task(task_id, data):
    unit = data.get("schedule", {}).get("unit", "seconds")
    interval = data.get("schedule", {}).get("interval", 5)
    trigger_args = {unit: interval}
    graph_id = data["graph_id"]
    scheduler.add_job(execute_task, "interval", id=task_id, args=[graph_id, task_id, data], **trigger_args)
    with shelve.open(DB_FILE, writeback=True) as db:
        db[task_id] = data

def delete_task(task_id):
    scheduler.remove_job(task_id)
    with shelve.open(DB_FILE, writeback=True) as db:
        if task_id in db:
            del db[task_id]

def restore_tasks():
    tasks = load_tasks()
    for task_id, data in tasks.items():
        add_task(task_id, data)

async def initialize():
    scheduler.start()
    restore_tasks()

@app.route('/schedule', methods=['POST'])
def create():
    try:
        task_data: TaskData = TaskData(**request.json)
    except TypeError:
        return jsonify({"error": "Invalid payload"}), 400
    
    task_id = generate()
    add_task(task_id, task_data)
    return jsonify({"task_id": task_id}), 201

@app.route('/schedule/<string:task_id>', methods=['DELETE'])
def delete(task_id):
    delete_task(task_id)
    return jsonify({"task_id": task_id}), 200

if __name__ == '__main__':
    asyncio.run(initialize())
    app.run(port=PORT)
