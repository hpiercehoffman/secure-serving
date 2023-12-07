#!/bin/bash

output_file="docker_stats_output.txt"
> "$output_file"

for i in {1..30}
do
   echo "----- Timestamp: $(date) -----" >> "$output_file"
   docker stats --no-stream >> "$output_file"
   sleep 1
done
