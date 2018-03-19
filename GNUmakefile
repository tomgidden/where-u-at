.PHONY: all life360_to_mqtt ical_to_mqtt run

run: stack.yml life360_to_mqtt ical_to_mqtt
	docker stack deploy -c stack.yml where-u-at

clean:
	docker stack rm where-u-at

life360_to_mqtt:
	$(MAKE) -C $@ build

ical_to_mqtt:
	$(MAKE) -C $@ build
