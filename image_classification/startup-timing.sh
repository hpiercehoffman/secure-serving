#!/bin/bash

# Start container in detached mode
docker run -d -p 80:9000 --device=/dev/nitro_enclaves:/dev/nitro_enclaves:rw resnet-enclave


start_time=$(date +%s.%N)
while true; do
    if curl -s http://localhost:80/ > /dev/null; then
        break
    fi
    sleep 1
done

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)
echo "Container startup time: $duration seconds"

