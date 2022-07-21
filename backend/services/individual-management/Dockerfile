FROM ubuntu:latest


COPY . /app/services/individual-management


WORKDIR /app/services/individual-management

RUN chmod +x ./individual-management-service
ENV NODE_ENV production

CMD [ "./individual-management-service"]
EXPOSE 3001
