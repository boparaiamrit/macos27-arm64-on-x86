FROM snapintosh-windows-builder:local
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-dev libpixman-1-dev libslirp-dev \
    python3-venv python3-requests python3-lz4 vulkan-tools qemu-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["/bin/bash"]
