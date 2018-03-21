build: Dockerfile w*.py
	docker build . -t tomgidden/weather_to_mqtt

push: build
	docker push tomgidden/weather_to_mqtt:latest

run: build
	docker run -d --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/weather_to_mqtt

test: build
	docker run -it --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/weather_to_mqtt
