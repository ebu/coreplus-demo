FROM ubuntu:latest


COPY . /app/services/sparql-assistant


WORKDIR /app/services/sparql-assistant

RUN chmod +x ./sparql-assistant-service
ENV NODE_ENV production

CMD [ "./sparql-assistant-service"]
EXPOSE 3003
