FROM ubuntu:latest
COPY . /app/services/tenant-management
WORKDIR /app/services/tenant-management
RUN chmod +x ./tenant-management-service
ENV NODE_ENV production
CMD ["./tenant-management-service"]
EXPOSE 3004
