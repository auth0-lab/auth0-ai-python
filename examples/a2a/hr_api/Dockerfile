FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY ../pyproject.toml ../poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY hr_api ./hr_api
COPY common ./common

ENV PORT=8081
ENV PYTHONPATH=/app

EXPOSE 8081

CMD ["python", "hr_api/server.py"]
