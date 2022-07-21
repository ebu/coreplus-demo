FROM ubuntu:latest


COPY . /app/services/cdk-backend


WORKDIR /app/services/cdk-backend

RUN chmod +rwx ./cdk-backend-service
ENV NODE_ENV production

CMD [ "./cdk-backend-service"]
EXPOSE 3007
