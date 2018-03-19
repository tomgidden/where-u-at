build: Dockerfile l*.py
	docker build . -t tomgidden/life360_to_mqtt

push: build
	docker push tomgidden/life360_to_mqtt:latest

run: build
	docker run -d --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/life360_to_mqtt

test: build
	docker run -it --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/life360_to_mqtt
