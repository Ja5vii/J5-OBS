FROM ubuntu:22.04 AS base

LABEL maintainer="J5 Studio"
LABEL description="J5 OBS Multi-Instance for Pterodactyl"

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    obs-studio \
    xvfb \
    alsa-utils \
    python3 \
    python3-pip \
    python3-venv \
    procps \
    lsof \
    ca-certificates \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libx11-6 \
    libxext6 \
    libxrender1 \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

RUN useradd -m -d /home/container -s /bin/bash container

WORKDIR /home/container

COPY requirements.txt /home/container/requirements.txt
RUN pip3 install --no-cache-dir -r /home/container/requirements.txt

COPY install.sh startup.sh shutdown.sh /home/container/
COPY instance_manager/ /home/container/instance_manager/
COPY panel/ /home/container/panel/

RUN chmod +x /home/container/install.sh \
    && chmod +x /home/container/startup.sh \
    && chmod +x /home/container/shutdown.sh

USER container
WORKDIR /home/container

ENTRYPOINT ["/home/container/startup.sh"]
