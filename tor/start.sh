#!/bin/sh

# Forward 0.0.0.0:9051 to 127.0.0.1:9052
nohup socat tcp-listen:9051,reuseaddr,fork tcp:127.0.0.1:9052 &

# Start tor
tor -f /app/torrc
