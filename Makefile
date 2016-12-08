help:
    @echo "Options:"
    @echo "    build-image: build the docker image of rConfig"

build-image:
    docker build --rm -t ispm/keepupz .

test:
    docker run ispm/keepupz python tests.py
