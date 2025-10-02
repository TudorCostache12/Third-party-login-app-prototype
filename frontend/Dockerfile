# Stage 1: build Angular
FROM node:20 AS build
WORKDIR /app

# Copiază dependențele
COPY package*.json ./
RUN npm install

# Copiază restul codului și build
COPY . .
RUN npm run build --configuration=production --output-path=/app/dist/frontend/browser/

# Stage 2: serve cu Nginx
FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/*
RUN rm -rf /usr/share/nginx/html/*
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist/frontend/browser/ /usr/share/nginx/html/


# Expune portul HTTPS
EXPOSE 443

# Pornește Nginx în prim-plan
CMD ["nginx", "-g", "daemon off;"]
