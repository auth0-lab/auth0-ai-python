# ====================
# Load environment variables from .env
# ====================

include .env
export $(shell sed 's/=.*//' .env)

# ====================
# Config Variables
# ====================

ENV_FILE=.env

# ====================
# HR Agent Variables
# ====================

HR_AGENT_IMAGE_NAME=hr-agent
HR_AGENT_DOCKERFILE=hr_agent/Dockerfile

# ====================
# HR API Variables
# ====================

HR_API_IMAGE_NAME=hr-api
HR_API_DOCKERFILE=hr_api/Dockerfile

# ====================
# Local Docker HR Agent
# ====================

build-hr-agent:
	docker build -t $(HR_AGENT_IMAGE_NAME) -f $(HR_AGENT_DOCKERFILE) .

run-hr-agent:
	docker run --env-file $(ENV_FILE) -p $(HR_AGENT_PORT):$(HR_AGENT_PORT) $(HR_AGENT_IMAGE_NAME)

rebuild-run-hr-agent: build-hr-agent run-hr-agent

# ====================
# Local Docker HR API
# ====================

build-hr-api:
	docker build -t $(HR_API_IMAGE_NAME) -f $(HR_API_DOCKERFILE) .

run-hr-api:
	docker run --env-file $(ENV_FILE) -p $(HR_API_PORT):$(HR_API_PORT) $(HR_API_IMAGE_NAME)

rebuild-run-hr-api: build-hr-api run-hr-api

# ====================
# Local All
# ====================
run:
	@{ \
		poetry run adk web & \
		docker-compose up --build & \
		wait; \
	}
