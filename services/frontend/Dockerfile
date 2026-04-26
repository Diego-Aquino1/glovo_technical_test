FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY src/ /usr/share/nginx/html/
COPY docker-entrypoint.sh /docker-entrypoint.d/50-inject-config.sh
RUN chmod +x /docker-entrypoint.d/50-inject-config.sh

EXPOSE 3000
