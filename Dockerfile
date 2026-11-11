FROM python:3.14-slim-trixie

WORKDIR /app

COPY requirements.txt .

RUN apt update && apt install -y libatomic
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "bot.py"]