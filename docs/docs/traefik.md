# Traefik

[Traefik](https://traefik.io/) in this repo acts as a reverse-proxy and load-balancer.  In a production Kubernetes environment, those two behaviors would be handled in the infrastructure by ingress managers and services.  Do not focus too much on Traefik in this repository in terms of understanding production Noteable code.  It is included here in order to support demonstrating real-time-updates (RTU) between backend servers (and users connected to different backend servers) over websockets and redis.

Traefik is typically advertised as a way to do dynamic edge routing, for instance by monitoring what containers are alive in Docker and dynamically creating routes to those containers based on Labels.  For this example though, the routing / services / middleware configuration is all file-based in `proxy/traefik.yaml` and files in `proxy/dynamic/`.  

You can see a nice dashboard representing those configurations at `http://localhost:8080/dashboard/`.



