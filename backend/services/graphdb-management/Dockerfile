FROM ubuntu:latest


COPY . /app/services/graphdb-management


WORKDIR /app/services/graphdb-management

RUN chmod +x ./graphdb-management-service

ENV NODE_ENV production
CMD [ "./graphdb-management-service"]
EXPOSE 3006
