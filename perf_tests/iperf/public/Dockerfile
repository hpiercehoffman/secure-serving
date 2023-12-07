FROM python:3.9-slim AS compile-image
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc libtool lib32z1 gcc make g++

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY iperf-vsock/ /iperf-vsock/

EXPOSE 9000

RUN ls iperf-vsock/build/src
RUN cd iperf-vsock/build && ls ../ && ../configure && make

RUN chmod +x iperf-vsock/build/src/iperf3
CMD ["iperf-vsock/build/src/iperf3", "-s"]
