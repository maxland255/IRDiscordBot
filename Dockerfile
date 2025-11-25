FROM python:3.13 as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim as production

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

COPY --chown=appuser ./bot ./bot

RUN chown -R appuser:appuser /app
RUN mkdir /app/bot/logs && chown -R appuser:appuser /app/bot/logs

USER appuser

ENV ENV=prod

CMD ["python", "-m", "bot.main"]

FROM base as development

COPY ./bot ./bot

ENV ENV=dev

CMD ["python", "-m", "bot.main"]
