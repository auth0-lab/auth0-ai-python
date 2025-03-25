import subprocess

def main():
    subprocess.run(["langgraph", "dev", "--port", "54367"], check=True)

if __name__ == "__main__":
    main()
