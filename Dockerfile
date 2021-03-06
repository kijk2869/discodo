# Discodo Dockerfile
# First, build docker image using `docker build` command
# If an error occurs while building this image, please create an issue on Github or create a pull request
# The working directory is /opt/discodo, which is where you would mount & edit your config.json file
# Python 3.8
FROM python:3.8

# Open default discodo node port
EXPOSE 8000

# set default workdir
WORKDIR /opt/discodo

# discodo deps
RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libopus-dev python3-dev libnacl-dev && \
    apt-get install --no-install-recommends -y pkg-config ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir to /opt/discodo
WORKDIR /opt/discodo

# Copy discodo repository
COPY . .

# Move example config file
RUN mv ./example/remote/config.inc.json ./config.json

# install pypi dependencies
RUN pip install --no-cache-dir --force-reinstall requirements.txt --no-binary av

# Echo discodo version
RUN echo "Discodo version: "$(python -m discodo --version)

# Run discodo with --config /opt/discodo/config.json option
CMD [ "python", "-m", "discodo", "--config", "/opt/discodo/config.json" ]
