FROM python:3.9-slim AS compile-image
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Build in a different stage to make final image smaller
FROM python:3.9-slim AS build-image
COPY --from=compile-image /opt/venv /opt/venv
COPY resnet_server.py requirements.txt setup.sh resnet18_pretrained.pth ./

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 9000
RUN ["chmod", "+x", "./setup.sh"]

# Set up vsock connection to enclave
RUN ["./setup.sh"]

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "resnet_server:app", "--host", "0.0.0.0", "--port", "8000"]