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
# EXTRAS=mcp (default, silent renders) or mcp,tts,align (narrated; see the -narrate image)
ARG EXTRAS=mcp
RUN pip install --no-cache-dir ".[${EXTRAS}]"

USER reel
ENV TOKENREEL_OUT=/home/reel/out
# Narrated variant: bake the small English recognizer into the image so alignment runs offline.
# The Kokoro voice model (about 350 MB) is not baked in; mount it read-only:
#   docker run -i --rm -v ~/.tokenreel/models:/home/reel/.tokenreel/models:ro IMAGE-narrate
RUN if echo "$EXTRAS" | grep -q align; then \
      python -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en', device='cpu', compute_type='int8')"; \
    fi
ENTRYPOINT ["tokenreel-mcp"]
