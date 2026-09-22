#!/bin/sh
set -eu

warp-svc &
warp_pid=$!
trap 'kill "$warp_pid" "${socat_pid:-}" 2>/dev/null || true' TERM INT
for attempt in $(seq 1 30); do
    if warp-cli --accept-tos status >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! warp-cli --accept-tos registration show >/dev/null 2>&1; then
    warp-cli --accept-tos registration new
fi
warp-cli --accept-tos mode proxy
warp-cli --accept-tos proxy port 40001
warp-cli --accept-tos connect

socat TCP-LISTEN:40000,reuseaddr,fork TCP:127.0.0.1:40001 &
socat_pid=$!
while kill -0 "$warp_pid" 2>/dev/null && kill -0 "$socat_pid" 2>/dev/null; do
    sleep 5
done
exit 1
