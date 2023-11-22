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
COPY sentiment_analysis.py sentiment_analysis_model.h5 requirements.txt tokenizer.pickle setup.sh ./

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000
RUN ["chmod", "+x", "./setup.sh"]

# Set up vsock connection to enclave
RUN ["./setup.sh"]

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "sentiment_analysis:app", "--host", "0.0.0.0", "--port", "8000"]