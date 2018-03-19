FROM python:latest

RUN apt-get update -y && \
    apt-get install -y libmosquitto-dev && \
    rm -rf /var/lib/apt /var/lib/dpkg

RUN pip3 install paho-mqtt requests && \
    rm -rf /root/.cache/

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt && \
    rm -rf /root/.cache/

COPY calzone.py i*.py /app/

CMD ["/app/ical_to_mqtt.py"]
