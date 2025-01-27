FROM python:3.10-alpine

ENV WORK_DIR=workdir \
  HASSIO_DATA_PATH=/data

RUN mkdir -p ${WORK_DIR}
WORKDIR /${WORK_DIR}
COPY requirements.txt .

# install python libraries
RUN pip3 install -r requirements.txt

# Copy code
COPY modbus_mqtt/ ./
COPY src/  ./
COPY modbus_mqtt/ ./
COPY run.sh  ./


# Run
RUN chmod a+x run.sh
CMD [ "sh", "./run.sh" ]
