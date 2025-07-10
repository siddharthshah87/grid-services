FROM python:3.11-slim

WORKDIR /app

COPY ./app /app/app
COPY ./pyproject.toml /app/
COPY ./entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip \
 && pip install poetry \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-root

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
