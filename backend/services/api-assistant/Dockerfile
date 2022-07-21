


FROM ubuntu:latest


COPY . /app/services/api-assistant


WORKDIR /app/services/api-assistant

RUN chmod +x ./api-assistant-service
ENV NODE_ENV production

CMD ["./api-assistant-service"]
EXPOSE 3005
