# syntax=docker/dockerfile:1
# ==============================================================================
# Stage 1: Builder – Compile hardened setuid dispatcher (`runas`)
# ==============================================================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY src/runas.c /src/runas.c
RUN gcc -static -O2 -Wall -Wextra -Werror -o /src/runas /src/runas.c

# ==============================================================================
# Stage 2: Runtime – Cyberus Linux Quest Environment
# ==============================================================================
FROM ubuntu:24.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TERM=xterm-256color \
    TZ=UTC

# Re-enable man pages in stripped Ubuntu 24.04 image BEFORE installing packages
RUN rm -f /etc/dpkg/dpkg.cfg.d/excludes && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        man-db \
        manpages \
        less \
        nano \
        tree \
        python3 \
        sudo \
        coreutils \
        findutils \
        grep \
        procps \
        util-linux \
        ca-certificates \
        locales \
        bsdextrautils \
        sed \
        gawk && \
    if [ -f /usr/bin/man.REAL ]; then \
        rm -f /usr/bin/man; \
        dpkg-divert --quiet --remove --rename /usr/bin/man; \
    fi && \
    apt-get install -y --reinstall --no-install-recommends coreutils findutils grep man-db manpages && \
    rm -rf /var/lib/apt/lists/* && \
    MANPAGER=cat man ls >/dev/null

# Ensure UID 1000 belongs to user `member` and GID 1000 belongs to group `bug`
RUN if id -u ubuntu >/dev/null 2>&1; then userdel -r ubuntu || true; fi && \
    if getent group ubuntu >/dev/null 2>&1; then groupdel ubuntu || true; fi && \
    groupadd -g 1000 bug && \
    useradd -m -d /home/member -u 1000 -g 1000 -s /bin/bash member && \
    ln -sfn /home/member /home/student && \
    passwd -d member >/dev/null 2>&1 || true

# Create directories with strict root ownership and permissions
RUN mkdir -p /opt/quest/engine /opt/quest/missions /opt/quest/tests \
             /usr/local/lib/quest /var/lib/quest /challenge /opt/vault

COPY --chown=root:root engine/ /opt/quest/engine/
COPY --chown=root:root missions/ /opt/quest/missions/
COPY --chown=root:root tests/ /opt/quest/tests/
COPY --chown=root:root entrypoint.sh /opt/quest/entrypoint.sh

# Install setuid dispatcher binary
COPY --from=builder --chown=root:root /src/runas /usr/local/lib/quest/runas
COPY --from=builder --chown=root:root /src/runas /usr/local/bin/quest

# Normalize permissions recursively and pre-install custom man page
RUN mkdir -p /usr/share/man/man1 /usr/local/share/man/man1 && \
    cp -f /opt/quest/missions/02-home-sweet-home/man/run.1 /usr/share/man/man1/run.1 && \
    cp -f /opt/quest/missions/02-home-sweet-home/man/run.1 /usr/local/share/man/man1/run.1 && \
    chmod 0644 /usr/share/man/man1/run.1 /usr/local/share/man/man1/run.1 && \
    mandb -q >/dev/null 2>&1 || true && \
    chown -R root:root /opt/quest /usr/local/lib/quest /challenge /opt/vault /var/lib/quest /usr/local/bin/quest && \
    chmod -R go-w /opt/quest /usr/local/lib/quest /challenge /opt/vault /usr/local/bin && \
    chmod 0755 / /usr /usr/local /usr/local/bin /opt /opt/quest /usr/local/lib/quest /challenge /opt/quest/entrypoint.sh && \
    chmod 0700 /opt/quest/engine /opt/quest/missions /opt/quest/tests /var/lib/quest && \
    chmod 0600 /opt/quest/engine/*.py && \
    chmod 0755 /usr/local/lib/quest/runas && \
    chmod 4755 /usr/local/bin/quest && \
    find /opt/quest/missions -type d -exec chmod 0700 {} + && \
    find /opt/quest/missions -type f -exec chmod 0600 {} + && \
    find /opt/quest/missions -name "*.sh" -exec chmod 0700 {} + && \
    chmod 0700 /opt/quest/tests/run_all.sh

WORKDIR /home/member
ENTRYPOINT ["/opt/quest/entrypoint.sh"]
CMD ["login-shell"]
