# Discodo Dockerfile
# First, build docker image using `docker build` command
# If an error occurs while building this image, please create an issue on Github or create a pull request
# The working directory is /opt/discodo, which is where you would mount & edit your config.json file
# Python 3.8
FROM python:3.8

# You can override this arg using --build-arg
ARG discodoRepoURL=https://github.com/kijk2869/discodo

# Open default discodo node port
EXPOSE 8000

# set default workdir
WORKDIR /opt/discodo

# discodo deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libopus-dev python3-dev libnacl-dev && \
    apt-get install --no-install-recommends -y pkg-config ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# install discodo from pypi
RUN pip install --no-cache-dir --force-reinstall git+${discodoRepoURL} --no-binary av && \
    echo "Discodo version: "$(python -m discodo --version)

# Set workdir to /temp/discodo
WORKDIR /temp/discodo

# Clone discodo repository
RUN git clone ${discodoRepoURL}

# Move example config.inc.json to /opt/discodo/config.json
RUN mv discodo/example/remote/config.inc.json /opt/discodo/config.json

# Set workdir to /opt/discodo
WORKDIR /opt/discodo

# Remove Cloned repository
RUN rm -rf /temp/discodo

# Run discodo with --config /opt/discodo/config.json option
CMD [ "python", "-m", "discodo", "--config", "/opt/discodo/config.json" ]
