import subprocess

def main():
    command = (
        "export $(grep -v '^#' ../llama-index-examples/.env | xargs) && "
        "poetry install --project ../sample-api && "
        "poetry run --project ../sample-api python ../sample-api/app.py"
    )
    subprocess.run(["bash", "-c", command], check=True)
