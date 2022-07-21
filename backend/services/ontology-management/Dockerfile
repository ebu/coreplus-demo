FROM ubuntu:latest


COPY . /app/services/ontology-management


WORKDIR /app/services/ontology-management



RUN chmod +x ./ontology-management-service

ENV NODE_ENV production
CMD ["./ontology-management-service"]
EXPOSE 3002
