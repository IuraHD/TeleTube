FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg socat \
    && curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
       | gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ bookworm main" \
       > /etc/apt/sources.list.d/cloudflare-client.list \
    && apt-get update && apt-get install -y --no-install-recommends cloudflare-warp \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
