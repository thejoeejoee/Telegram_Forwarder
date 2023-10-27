export DOCKER_BUILDKIT=1

COMPONENT ?= telegram-forwarder
RELEASE_NAME ?= $(COMPONENT)

REGISTRY ?= thejoeejoee/$(COMPONENT)

dev-converge:
	werf converge \
		--repo $(REGISTRY) \
		--dev \
		--release $(RELEASE_NAME)

compose-up:
	werf compose up --dev

render:
	werf render \
		--repo $(REGISTRY) \
		--dev \
		--release $(RELEASE_NAME)

bundle-render:
	werf bundle render \
		--repo $(REGISTRY)
