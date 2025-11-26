#!/bin/bash

PROXY="http://127.0.0.1:3128"   # change to your Squid IP/port

for i in {1..20}; do
    echo -n "Request $i → "
    curl -s --proxy "$PROXY" https://checkip.amazonaws.com/
done
