FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install flask
RUN pip install fastf1
RUN pip install flask_caching

RUN mkdir -p /app/.fastf1/cache

COPY . .

ENV FASTF1_CACHE_DIR /app/.fastf1/cache

CMD [ "python", "server.py" ]

EXPOSE 5000
