FROM ubuntu:latest
COPY . /app/services/cache-managment
WORKDIR /app/services/cache-managment
RUN chmod +rwx ./cache-management-service
ENV NODE_ENV production
CMD ["./cache-management-service"]
EXPOSE 3000