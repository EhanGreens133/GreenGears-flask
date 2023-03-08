FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install flask
RUN pip install fastf1
RUN pip install flask_caching
RUN pip install gunicorn
RUN pip install flask-cors


RUN mkdir -p /app/.fastf1/cache

COPY . .

ENV FASTF1_CACHE_DIR /app/.fastf1/cache

# CMD [ "python", "server.py" ]
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app"]


EXPOSE 5000
