FROM python:3.13 as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim as production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY ./bot ./bot

RUN useradd --create-home appuser
USER appuser

ENV ENV=prod

CMD ["python", "-m", "bot.main"]

FROM base as development

COPY ./bot ./bot

ENV ENV=dev

CMD ["python", "-m", "bot.main"]
