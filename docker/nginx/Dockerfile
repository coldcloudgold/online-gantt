FROM nginx:1.19.9-alpine

# замента конфига nginx'a
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# напоминание о порте
EXPOSE 8080
