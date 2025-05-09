FROM python:3.10-slim

RUN pip install --no-cache-dir gradio==5.4.0
RUN pip install pydantic==2.10.6
WORKDIR /usr/src/app
COPY . .
ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "app.py"]