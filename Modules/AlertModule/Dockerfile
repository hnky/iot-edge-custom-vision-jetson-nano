FROM python:3.7-slim-buster

RUN apt update

RUN pip install azure-iot-device~=2.0.0RC11


ADD /app/ .


ENTRYPOINT [ "python", "-u", "./main.py" ]
