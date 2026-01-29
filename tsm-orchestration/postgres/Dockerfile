# start from ubuntu based timescale image
ARG BASE_IMAGE_TAG=pg17
FROM timescale/timescaledb-ha:${BASE_IMAGE_TAG}

ARG BUILD_DATE
ARG VCS_REF

LABEL maintainer="The ZID Team" \
    org.opencontainers.image.title="time.IO Database Image" \
    org.opencontainers.image.licenses="EUPL-1.2" \
    org.opencontainers.image.version="0.1" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE

# switch from postgres/1000 to root and install postgis
USER root
RUN apt-get update \
    && apt-get install -y postgresql-14-postgis-3 \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# add user with UID defined in .env
# skip, if UID already exists (e.g. postgres/1000)
ARG UID=1000
RUN adduser --uid ${UID} --disabled-password tsm || exit 0

# Adjust owner of postgres data directory
RUN chown ${UID} /var/lib/postgresql

# switch to user with UID
USER ${UID}