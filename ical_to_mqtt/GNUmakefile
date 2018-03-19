build: Dockerfile i*.py calzone.py
	docker build . -t tomgidden/ical_to_mqtt

push: build
	docker push tomgidden/ical_to_mqtt:latest

run: build
	docker run -d --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/ical_to_mqtt

test: build
	docker run -it --rm -v $(PWD)/config.py:/app/config.py:ro tomgidden/ical_to_mqtt bash
