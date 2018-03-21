FROM python:latest

RUN apt-get update -y && \
    apt-get install -y libmosquitto-dev && \
    rm -rf /var/lib/apt /var/lib/dpkg

RUN pip3 install paho-mqtt requests && \
    rm -rf /root/.cache/

RUN mkdir /app

WORKDIR /app

COPY w*.py /app/

CMD ["/app/weather_to_mqtt.py"]
