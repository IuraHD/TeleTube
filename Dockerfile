FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY teletube ./teletube
RUN useradd --create-home --uid 10001 bot && mkdir /app/downloads /app/data \
    && chown bot:bot /app/downloads /app/data
USER bot
CMD ["python", "-m", "teletube"]

FROM runtime AS test
USER root
RUN pip install --no-cache-dir pytest
COPY tests ./tests
RUN python -m pytest -q
