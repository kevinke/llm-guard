# Use the Python 3.12 slim image
FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/protectai/llm-guard
LABEL org.opencontainers.image.description="LLM Guard API"
LABEL org.opencontainers.image.licenses=MIT

# Install system packages needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# ensures that the python output is sent straight to terminal (e.g. your container log)
# without being first buffered and that you can see the output of your application (e.g. django logs)
# in real time. Equivalent to python -u: https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED 1

# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONDONTWRITEBYTECODE
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE 1

# Set up a working directory
WORKDIR $HOME/app

# Build-time toggles for dependency behavior in constrained networks.
ARG TORCH_CPU_VERSION=2.4.0+cpu
ARG PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
ARG PIP_EXTRA_INDEX_URL="https://mirrors.ustc.edu.cn/pypi/simple https://pypi.org/simple"
ARG PIP_TRUSTED_HOST=
ARG PIP_DEFAULT_TIMEOUT=300
ARG PIP_RETRIES=10
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
ARG INSTALL_SPACY_MODELS=0
# When INSTALL_SPACY_MODELS=1, spaCy models are baked into the image and the
# runtime download guard should be lifted. Default keeps the guard on (=1).
ARG SKIP_SPACY_DOWNLOAD=1

# Copy pyproject.toml and other necessary files for installation
COPY --chown=user:user llm_guard_api/pyproject.toml ./pyproject.toml
COPY --chown=user:user llm_guard_api/app ./app
COPY --chown=user:user pyproject.toml /tmp/llm_guard_src/pyproject.toml
COPY --chown=user:user README.md /tmp/llm_guard_src/README.md
COPY --chown=user:user LICENSE /tmp/llm_guard_src/LICENSE
COPY --chown=user:user llm_guard /tmp/llm_guard_src/llm_guard

# Install the project's dependencies
RUN mkdir -p "$HOME/.config/pip" && \
    printf '[global]\nindex-url = %s\nextra-index-url = %s\ndefault-timeout = %s\nretries = %s\ndisable-pip-version-check = true\n' \
    "$PIP_INDEX_URL" "$PIP_EXTRA_INDEX_URL" "$PIP_DEFAULT_TIMEOUT" "$PIP_RETRIES" \
    > "$HOME/.config/pip/pip.conf" && \
    if [ -n "$PIP_TRUSTED_HOST" ]; then \
        printf 'trusted-host = %s\n' "$PIP_TRUSTED_HOST" >> "$HOME/.config/pip/pip.conf"; \
    fi && \
    printf "torch==%s\n" "$TORCH_CPU_VERSION" > /tmp/constraints.txt && \
        pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir \
    --index-url "$TORCH_INDEX_URL" \
    --extra-index-url "$PIP_INDEX_URL" \
        "torch==$TORCH_CPU_VERSION" && \
        pip install --no-cache-dir \
        --constraint /tmp/constraints.txt \
        ".[cpu]" && \
        pip install --no-cache-dir --force-reinstall --no-deps /tmp/llm_guard_src && \
        rm -rf /tmp/llm_guard_src && \
        rm -f /tmp/constraints.txt

RUN if [ "$INSTALL_SPACY_MODELS" = "1" ]; then \
            python -m spacy download en_core_web_sm || true; \
            python -m spacy download zh_core_web_sm || true; \
        else \
            echo "Skipping spaCy model downloads at build time"; \
        fi

COPY --chown=user:user llm_guard_api/config/scanners.yml ./config/scanners.yml
COPY --chown=user:user llm_guard_api/entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

ENV PYTHONPATH=$HOME/app
ENV LLM_GUARD_SKIP_SPACY_DOWNLOAD=$SKIP_SPACY_DOWNLOAD

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
