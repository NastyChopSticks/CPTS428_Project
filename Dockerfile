FROM ghcr.io/anomalyco/opencode:2.1.1

USER root

RUN apk add --no-cache \
    curl \
    git \
    bash \
    ca-certificates \
    && addgroup -S agent \
    && adduser -S -G agent -h /home/agent agent \
    && mkdir -p /workspace /home/agent/.config/opencode \
    && chown -R agent:agent /workspace /home/agent

ENV HOME=/home/agent
WORKDIR /workspace
COPY --chown=agent:agent AGENTS.md /home/agent/.config/opencode/AGENTS.md
USER agent

ENTRYPOINT ["opencode"]
