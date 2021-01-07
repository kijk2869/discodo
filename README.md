# Discodo

![PyPI](https://img.shields.io/pypi/v/discodo?logo=pypi)
![Docker Image Version (latest by date)](https://img.shields.io/docker/v/kijk2869/discodo?arch=amd64&label=docker&logo=docker&sort=semver)
![PyPI - License](https://img.shields.io/pypi/l/discodo)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/kijk2869/discodo/Python%20application?logo=github)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/kijk2869/discodo/Upload%20Python%20Package?label=release&logo=pypi)


Discodo is an enhanced audio player for discord.

## Features

* Standalone Audio Node
* Youtube Related Video Autoplay
* Crossfade and Audio effects
* Synced Youtube Video Subtitle

## Documentation

**More information can be found [here](./docs).**

## Installation

**Discodo requires Python 3.7 or higher**

```sh
python -m pip install --upgrade discodo
```

On Linux environments, more dependencies are required.

## Execution

### Audio Node Server

**Additional options can be seen with the --help flag**

```sh
python -m discodo
```

### Client libraries

* [discodo](https://github.com/kijk2869/discodo) (Python)
* ~~[discodo.js](Under Developing) (Node.JS)~~

## Supported sources

+ All sources that can be extracted from [youtube_dl](https://github.com/ytdl-org/youtube-dl)
+ All formats that can be demuxed by [libav](https://libav.org/)
