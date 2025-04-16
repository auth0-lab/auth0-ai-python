import subprocess

def main():
    subprocess.run(["langgraph", "dev", "--port", "54367", "--allow-blocking"], check=True)

if __name__ == "__main__":
    main()
