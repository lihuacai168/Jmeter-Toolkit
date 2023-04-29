
compose-file := docker-compose.yml

ifdef COMPOSE_FILE
    compose-file := $(COMPOSE_FILE)
endif

cmd = docker-compose -f $(compose-file)

image_tag ?= latest


tag := $(tag)

service := $(word 1,$(MAKECMDGOALS))

.PHONY: fastup
fastup:
	export TAG=$(image_tag); docker-compose -f docker-compose-for-fastup.yml up -d  --build --remove-orphans

.PHONY: up
up:
	$(cmd) up -d  --build --remove-orphans

.PHONY: up-no-build
up-no-build:
	$(cmd) up -d --remove-orphans

.PHONY: up-tag
up-tag:
	export TAG=$(tag); $(cmd) up -d  --build --remove-orphans


.PHONY: down
down:
	$(cmd) down

.PHONY: build
build:
	# build latest
	$(cmd) build

git-tag:
	git checkout $(tag)

.PHONY: build-tag
build-tag:git-tag
	export TAG=$(tag);  $(cmd) build

.PHONY: config
config:
	$(cmd) config

.PHONY: ps
ps:
	$(cmd) ps

.PHONY: logs
logs:
	$(cmd) logs -f fastapi_jmx

.PHONY: restart
restart:
	$(cmd) restart $(service)

.PHONY: exec
exec:
	$(cmd) exec $(service) /bin/bash
