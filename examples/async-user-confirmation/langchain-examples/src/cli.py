import subprocess

def start():
    """Run `langgraph up`."""
    subprocess.run(["langgraph", "up"], check=True)

def dev():
    """Run `langgraph dev --port 54367`."""
    subprocess.run(["langgraph", "dev", "--port", "54367"], check=True)
