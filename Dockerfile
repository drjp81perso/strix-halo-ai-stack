ARG LLAMA_SWAP_IMAGE=ghcr.io/mostlygeek/llama-swap:unified-vulkan
FROM ${LLAMA_SWAP_IMAGE}
USER root
RUN apt-get update && apt-get install -y --no-install-recommends jq procps bc && rm -rf /var/lib/apt/lists/*
COPY scripts/admit-run scripts/check-runtime-flags /usr/local/bin/
RUN chmod 0755 /usr/local/bin/admit-run /usr/local/bin/check-runtime-flags
