#!/bin/bash

channel_id=1
loop_count=100

for ((i=0; i<loop_count; i++)); do
    iperf3 --vsock -c $channel_id
    ((channel_id++))
done
