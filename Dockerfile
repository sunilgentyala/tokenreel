FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/sunilgentyala/tokenreel" \
      org.opencontainers.image.description="TokenReel MCP server: text to animated, narrated, captioned videos" \
      org.opencontainers.image.licenses="Apache-2.0"

# ffmpeg for encoding, DejaVu fonts for frame rendering
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 reel
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[mcp]"

USER reel
ENV TOKENREEL_OUT=/home/reel/out
# For narration, mount the two Kokoro model files and install the tts extra, e.g.
#   docker run -v ~/.tokenreel/models:/home/reel/.tokenreel/models:ro ...
ENTRYPOINT ["tokenreel-mcp"]
