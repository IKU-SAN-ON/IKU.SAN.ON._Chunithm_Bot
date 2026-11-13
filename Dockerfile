# Python runtime for the Discord bot.
#
# Security/deployment notes:
#   * The interpreter is pinned by minor version (3.14) so rebuilds stay predictable.
#   * The bot runs as an unprivileged service account (`bot`), never as root.
#   * Playwright's Chromium is installed into a shared, world-readable path instead
#     of /root/.cache, otherwise the non-root user cannot launch it.
#   * The SQLite database/state directory lives at /app/data; when it is bind-mounted
#     from the host, that directory must be writable by APP_UID/APP_GID (1000 by
#     default). Alternatively, use a named volume.

FROM python:3.14-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Dedicated service account. UID/GID 1000 is the usual first non-root user on
# Linux hosts, which keeps bind-mounted data directories writable by default.
ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid "${APP_GID}" bot \
    && useradd \
        --uid "${APP_UID}" \
        --gid bot \
        --create-home \
        --shell /usr/sbin/nologin \
        bot

# `libatomic1` is required by Chromium; tini gives us a correct PID 1 that
# forwards signals to Python (compose also sets `init: true`, but the image
# should behave correctly with a plain `docker run` too).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libatomic1 \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Dependencies are installed before the source so edits to the bot do not
# invalidate this (slow) layer. Pin versions in requirements.txt (or add a
# lock/constraints file) if you need byte-for-byte reproducible releases.
COPY --chown=bot:bot requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium and its OS dependencies as root, then make the browser
# bundle readable by the runtime user.
RUN playwright install --with-deps chromium \
    && chmod -R a+rX "${PLAYWRIGHT_BROWSERS_PATH}" \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=bot:bot . .

# Make sure the state directory exists and is writable even without a volume.
RUN mkdir -p /app/data \
    && chown -R bot:bot /app

USER bot

ENTRYPOINT ["/usr/bin/tini", "-s", "--"]
CMD ["python", "bot.py"]
