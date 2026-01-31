# Homepage

Homepage is a modern, customizable dashboard for your homelab services.

## Features

- Service status monitoring
- Docker integration
- Widgets (weather, search, bookmarks)
- Custom CSS themes
- Multiple languages

## Docker Compose Setup

```yaml
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: homepage
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock:ro
    environment:
      PUID: 1000
      PGID: 1000
    networks:
      - proxy

networks:
  proxy:
    external: true
```

## Configuration

### Directory Structure

```
config/
├── bookmarks.yaml
├── docker.yaml
├── services.yaml
├── settings.yaml
└── widgets.yaml
```

### Settings

```yaml
# config/settings.yaml
title: My Homelab
theme: dark
color: slate
background:
  image: https://images.unsplash.com/photo-1502790671504-542ad42d5189
  blur: sm
  opacity: 50
cardBlur: md
headerStyle: clean
layout:
  Infrastructure:
    style: row
    columns: 4
  Media:
    style: row
    columns: 3
  Monitoring:
    style: row
    columns: 2
```

### Services

```yaml
# config/services.yaml
- Infrastructure:
    - Proxmox:
        icon: proxmox.png
        href: https://proxmox.local:8006
        description: Virtualization
        widget:
          type: proxmox
          url: https://proxmox.local:8006
          username: api@pam!homepage
          password: your-api-token

    - Portainer:
        icon: portainer.png
        href: https://portainer.example.com
        description: Docker Management
        widget:
          type: portainer
          url: https://portainer.example.com
          env: 2
          key: your-api-key

    - Pi-hole:
        icon: pi-hole.png
        href: http://pihole.local/admin
        description: DNS Ad Blocker
        widget:
          type: pihole
          url: http://pihole.local
          key: your-api-key

- Media:
    - Jellyfin:
        icon: jellyfin.png
        href: https://media.example.com
        description: Media Server
        widget:
          type: jellyfin
          url: http://jellyfin:8096
          key: your-api-key
          enableBlocks: true
          enableNowPlaying: true

    - Sonarr:
        icon: sonarr.png
        href: https://sonarr.example.com
        description: TV Shows
        widget:
          type: sonarr
          url: http://sonarr:8989
          key: your-api-key

    - Radarr:
        icon: radarr.png
        href: https://radarr.example.com
        description: Movies
        widget:
          type: radarr
          url: http://radarr:7878
          key: your-api-key

- Monitoring:
    - Uptime Kuma:
        icon: uptime-kuma.png
        href: https://status.example.com
        description: Status Page
        widget:
          type: uptimekuma
          url: http://uptime-kuma:3001
          slug: default

    - Grafana:
        icon: grafana.png
        href: https://grafana.example.com
        description: Dashboards
```

### Bookmarks

```yaml
# config/bookmarks.yaml
- Development:
    - GitHub:
        - icon: github.png
          href: https://github.com
    - GitLab:
        - icon: gitlab.png
          href: https://gitlab.com

- Documentation:
    - Docker Docs:
        - icon: docker.png
          href: https://docs.docker.com
    - Kubernetes:
        - icon: kubernetes.png
          href: https://kubernetes.io/docs

- Tools:
    - ChatGPT:
        - icon: openai.png
          href: https://chat.openai.com
    - Claude:
        - icon: si-anthropic
          href: https://claude.ai
```

### Widgets

```yaml
# config/widgets.yaml
- search:
    provider: duckduckgo
    target: _blank

- datetime:
    text_size: xl
    format:
      dateStyle: long
      timeStyle: short
      hourCycle: h23

- openweathermap:
    label: Oslo
    latitude: 59.9139
    longitude: 10.7522
    units: metric
    provider: openweathermap
    apiKey: your-api-key

- resources:
    backend: resources
    expanded: true
    cpu: true
    memory: true
    disk: /

- kubernetes:
    cluster:
      show: true
      cpu: true
      memory: true
    nodes:
      show: true
```

### Docker Integration

```yaml
# config/docker.yaml
my-docker:
  socket: /var/run/docker.sock
```

Auto-discover services via labels:

```yaml
# In service docker-compose.yml
services:
  myapp:
    labels:
      - homepage.group=Applications
      - homepage.name=My App
      - homepage.icon=mdi-application
      - homepage.href=https://myapp.example.com
      - homepage.description=My Application
      - homepage.widget.type=customapi
      - homepage.widget.url=http://myapp:8080/api/status
```

## Widget Types

### Infrastructure

```yaml
# Proxmox
widget:
  type: proxmox
  url: https://proxmox:8006
  username: api@pam!homepage
  password: token

# Portainer
widget:
  type: portainer
  url: https://portainer:9000
  env: 1
  key: api-key

# Traefik
widget:
  type: traefik
  url: http://traefik:8080
```

### Media

```yaml
# Jellyfin
widget:
  type: jellyfin
  url: http://jellyfin:8096
  key: api-key
  enableBlocks: true
  enableNowPlaying: true

# Plex
widget:
  type: plex
  url: http://plex:32400
  key: token

# Transmission
widget:
  type: transmission
  url: http://transmission:9091
  username: admin
  password: password
```

### Monitoring

```yaml
# Pi-hole
widget:
  type: pihole
  url: http://pihole
  key: api-key

# Uptime Kuma
widget:
  type: uptimekuma
  url: http://uptime-kuma:3001
  slug: default

# Prometheus
widget:
  type: prometheus
  url: http://prometheus:9090
```

### Custom API

```yaml
widget:
  type: customapi
  url: http://service/api/status
  refreshInterval: 10000
  method: GET
  mappings:
    - field: status
      label: Status
    - field: uptime
      label: Uptime
      format: duration
```

## Custom CSS

```yaml
# config/custom.css
:root {
  --color-primary: #3b82f6;
}

.service-card {
  backdrop-filter: blur(10px);
}
```

Reference in settings:

```yaml
# config/settings.yaml
customCss: custom.css
```

## Reverse Proxy

### Traefik Labels

```yaml
services:
  homepage:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.homepage.rule=Host(`home.example.com`)"
      - "traefik.http.routers.homepage.entrypoints=https"
      - "traefik.http.routers.homepage.tls.certresolver=letsencrypt"
      - "traefik.http.services.homepage.loadbalancer.server.port=3000"
```

### Caddy

```
home.example.com {
    reverse_proxy homepage:3000
}
```

## Authentication

Protect Homepage with your auth proxy:

```yaml
labels:
  - "traefik.http.routers.homepage.middlewares=authelia@docker"
```

## Environment Variables

```yaml
environment:
  HOMEPAGE_VAR_WEATHER_API: ${WEATHER_API_KEY}
  HOMEPAGE_VAR_PIHOLE_KEY: ${PIHOLE_API_KEY}
```

Use in config:

```yaml
widget:
  type: openweathermap
  apiKey: {{HOMEPAGE_VAR_WEATHER_API}}
```

## Troubleshooting

### Logs

```bash
docker logs homepage
```

### Common Issues

1. **Widget not loading**
   - Check service is reachable from Homepage container
   - Verify API key is correct
   - Check URL format

2. **Docker services not showing**
   - Verify socket mount
   - Check labels syntax

3. **Icons not loading**
   - Use dashboard-icons: `si-servicename`
   - Or mdi icons: `mdi-icon-name`

## See Also

- [Services Overview](../index.md)
- [Uptime Kuma](../uptime-kuma/index.md)
- [Reverse Proxy](../reverse-proxy/index.md)
