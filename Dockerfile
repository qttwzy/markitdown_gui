FROM python:3.11-slim-bookworm AS builder

ARG APT_MIRROR=mirrors.ustc.edu.cn
ARG PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN if [ "$APT_MIRROR" != "deb.debian.org" ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN pip install --no-cache-dir --prefix=/install \
    -i ${PIP_INDEX} \
    --trusted-host ${PIP_TRUSTED_HOST} \
    "markitdown[pdf]>=0.1.5" \
    "tkinterdnd2>=0.4.3" \
    "pymupdf>=1.24.0"

FROM python:3.11-slim-bookworm

ARG APT_MIRROR=mirrors.ustc.edu.cn

RUN if [ "$APT_MIRROR" != "deb.debian.org" ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi

ENV DISPLAY=:0
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
ENV VNC_RESOLUTION=1280x800
ENV VNC_PASSWORD=

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    tk \
    tkdnd \
    libtk8.6 \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libxi6 \
    libxtst6 \
    libasound2 \
    libxcursor1 \
    libjpeg62-turbo \
    libfreetype6 \
    liblcms2-2 \
    libopenjp2-7 \
    libtiff6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

COPY gui.py converter.py predictor.py i18n.py console_panel.py logger_config.py main.py ./

RUN mkdir -p /app/input /app/output

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE ${NOVNC_PORT} ${VNC_PORT}

VOLUME ["/app/input", "/app/output"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:${NOVNC_PORT}/vnc.html >/dev/null 2>&1 || exit 1

ENTRYPOINT ["/entrypoint.sh"]
