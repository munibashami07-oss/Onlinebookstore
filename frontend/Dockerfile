# Stage 1: Build React Vite Application
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Railway passes service Variables as build args, but ONLY for args that
<<<<<<< HEAD
# are explicitly declared here with ARG -- without this, VITE_API_URL set
# in the Railway dashboard never reaches this build step, and Vite bakes
# in the fallback '/api/v1' instead, pointing requests at this frontend's
# own domain instead of the backend.
=======
# are explicitly declared here with ARG.
>>>>>>> a0cf987e7e93710dc20efca204e5a8c41f562bd2
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve static production assets with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
<<<<<<< HEAD

CMD ["nginx", "-g", "daemon off;"]
=======
CMD ["nginx", "-g", "daemon off;"]
>>>>>>> a0cf987e7e93710dc20efca204e5a8c41f562bd2
