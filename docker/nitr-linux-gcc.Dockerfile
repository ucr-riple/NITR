FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        bash \
        ca-certificates \
        cmake \
        git \
        ninja-build \
        python3 \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/repo
