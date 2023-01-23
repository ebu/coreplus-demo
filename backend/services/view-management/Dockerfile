FROM ubuntu:latest


COPY . /app/services/view-management


WORKDIR /app/services/view-management

RUN chmod +x ./view-management-service
ENV NODE_ENV production

CMD [ "./view-management-service"]
EXPOSE 3009
