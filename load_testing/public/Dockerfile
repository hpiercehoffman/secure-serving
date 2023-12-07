FROM python:3.9-slim AS compile-image
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY resnet_server.py requirements.txt resnet18_pretrained.pth ./

EXPOSE 9000
CMD ["uvicorn", "resnet_server:app", "--host", "0.0.0.0", "--port", "9000"]