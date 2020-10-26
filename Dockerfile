# Discodo Dockerfile
# First, build docker image using `docker build` command
# If an error occurs while building this image, please create an issue on Github or create a pull request
# The working directory is /opt/discodo, which is where you would mount & edit your config.json file
# Python 3.8
FROM python:3.8

# You can override this arg using --build-arg
ARG discodoRepoURL=https://github.com/sannoob/discodo

WORKDIR /opt/discodo

RUN apt-get update && \
    apt-get install --no-install-recommends -y gcc libopus-dev python3-dev libnacl-dev && \
    apt-get install --no-install-recommends -y pkg-config ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
RUN pip install --force-reinstall discodo --no-binary av
RUN pip uninstall uvloop -y
RUN python -m discodo --version

RUN git clone ${discodoRepoURL}
RUN cp discodo/example/remote/config.inc.json config.json

CMD [ "python", "-m", "discodo", "--config", "/opt/discodo/config.json" ]