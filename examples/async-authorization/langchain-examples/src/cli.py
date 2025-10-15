import subprocess

def start_api():
    command = (
        "export $(grep -v '^#' ../langchain-examples/.env | xargs) && "
        "poetry install --project ../sample-api && "
        "poetry run --project ../sample-api python ../sample-api/app.py"
    )
    subprocess.run(["bash", "-c", command], check=True)

def start_scheduler():
    subprocess.run(["python", "./src/services/scheduler.py"], check=True)

def start_resumer():
    subprocess.run(["python", "./src/services/resumer.py"], check=True)

def start_langgraph_dev():
    subprocess.run(["langgraph", "dev", "--port", "54367", "--allow-blocking"], check=True)
