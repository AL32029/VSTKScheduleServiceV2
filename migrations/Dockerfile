FROM python:3.12-slim AS builder

ENV PATH="/root/.local/bin:${PATH}"

RUN pip install --no-cache-dir pipx && pipx install poetry==2.4.1 && pipx inject poetry poetry-plugin-export

COPY pyproject.toml poetry.lock ./

RUN poetry export --only main --without-hashes -o requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

RUN useradd --uid 1000 --shell /bin/bash appuser

WORKDIR /app

COPY --from=database_models . /shared_libs/database_models

COPY --from=builder requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --disable-pip-version-check \
    -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["alembic", "-c", "alembic.ini", "upgrade", "head"]

