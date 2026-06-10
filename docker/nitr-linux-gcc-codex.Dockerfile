FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        bash \
        ca-certificates \
        cmake \
        curl \
        git \
        ninja-build \
        python3 \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace/repo
