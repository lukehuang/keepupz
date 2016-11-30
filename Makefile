help:
	@echo "Options:"
	@echo "    build-image: build the docker image of rConfig"

build-image:
	# docker build --rm -t ispm/icmpreceiver icmpreceiver/ && docker build --rm -t ispm/rconfig-api api/
	docker build --rm -t ispm/icmpreceiver icmpreceiver/
