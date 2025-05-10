FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY ../pyproject.toml ../poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY hr_agent ./hr_agent
COPY a2a ./a2a
COPY common ./common

ENV PORT=8080
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "-m", "hr_agent"]
