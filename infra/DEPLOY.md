# Guia de Deploy

## ¿Que es esto?

Un sistema para actualizar la aplicacion en el servidor **sin que los usuarios noten que se esta actualizando** (zero downtime).

## Arquitectura

```mermaid
flowchart TB
    subgraph Tu computadora
        DEV[make deploy]
    end

    subgraph Servidor
        subgraph Infraestructura["compose.prod.infra.yaml (siempre corriendo)"]
            DB[(PostgreSQL)]
            RD[(Redis)]
        end

        N[Nginx :80]

        subgraph Blue["compose.prod.yaml (blue)"]
            BF[Frontend :3001]
            BA[API :8001]
            BC[Celery]
        end

        subgraph Green["compose.prod.yaml (green)"]
            GF[Frontend :3002]
            GA[API :8002]
            GC[Celery]
        end
    end

    DEV -->|SSH| N
    N -->|trafico| BF
    BF --> BA
    BA --> DB
    BA --> RD
    GF --> GA
    GA --> DB
    GA --> RD
```

### Archivos Docker Compose

| Archivo | Que hace | Cuando se usa |
|---------|----------|---------------|
| `compose.yaml` | Dev: DB + Redis + pgweb con puertos expuestos | `make up` en tu maquina |
| `compose.prod.infra.yaml` | Prod: DB + Redis (sin puertos, red interna) | Deploy - siempre corriendo |
| `compose.prod.yaml` | Prod: Frontend + API + Celery | Deploy - blue o green |

### Como funciona blue/green

1. Tenes dos copias de la app: **blue** (puertos 3001/8001) y **green** (puertos 3002/8002)
2. Solo una recibe trafico (la "activa")
3. Para actualizar:
   - Levantas la copia inactiva con el nuevo codigo
   - Verificas que funcione
   - Nginx cambia el trafico a la nueva
   - Apagas la vieja
4. Los usuarios nunca ven downtime

> **Nota:** "blue" y "green" son solo nombres arbitrarios, no hay uno principal y otro secundario. Ambos son produccion y se van alternando con cada deploy. Podrian llamarse "A" y "B" - es solo una convencion de la industria.

## Configuracion

### 1. Crear archivo de configuracion

```bash
cp .env.deploy.example .env.deploy
```

Editar `.env.deploy`:

```bash
# Nombre de la app (para containers, volumenes, etc)
APP_NAME=dashboard

# Conexion SSH al servidor
SSH_HOST=192.168.1.100
SSH_USER=tu_usuario
SSH_PORT=22

# Base de datos
DB_NAME=dashboard_db
DB_USER=dashboard_user
DB_PASSWORD=password_seguro_aqui

# Seguridad (generar con: openssl rand -hex 32)
SECRET_KEY=clave_secreta_aqui
NEXTAUTH_SECRET=otra_clave_secreta_aqui

# URLs del servidor (usar HTTPS en produccion!)
NEXT_PUBLIC_API_HOST=https://192.168.1.100
FRONTEND_URL=https://192.168.1.100
NEXTAUTH_URL=https://192.168.1.100
CORS_ORIGINS=https://192.168.1.100
ALLOWED_HOSTS=192.168.1.100,localhost
```

> **IMPORTANTE:** NextAuth requiere HTTPS para que las cookies de sesion funcionen correctamente. Ver seccion "Configuracion HTTPS" mas abajo.

### 2. Setup del servidor (solo una vez)

```bash
# Crear directorios en el servidor
make deploy-setup
```

Luego conectate al servidor:

```bash
make deploy-ssh
```

Y ejecuta estos comandos:

```bash
# Crear deploy key para GitHub
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""
cat ~/.ssh/deploy_key.pub
# ^ Agregar esta clave en GitHub: Repo > Settings > Deploy keys

# Configurar SSH para usar la clave
cat >> ~/.ssh/config << 'EOF'
Host github.com
    IdentityFile ~/.ssh/deploy_key
    IdentitiesOnly yes
EOF

# Clonar el repositorio
cd /opt/dashboard  # o donde hayas configurado REMOTE_DIR
git clone git@github.com:tu-org/tu-repo.git app

# Instalar y configurar Nginx
sudo apt update && sudo apt install -y nginx
sudo cp /opt/dashboard/app/infra/nginx.conf /etc/nginx/sites-enabled/dashboard.conf
sudo nginx -t && sudo systemctl reload nginx

# Salir
exit
```

### 3. Primer deploy

```bash
make deploy
```

## Uso diario

### Comandos disponibles

| Comando | Que hace |
|---------|----------|
| `make deploy` | Deploy al servidor (blue/green) |
| `make deploy-rollback` | Volver a la version anterior |
| `make deploy-status` | Ver que esta corriendo |
| `make deploy-logs` | Ver logs del servidor |
| `make deploy-ssh` | Conectarse al servidor |

### Deploy normal

```bash
make deploy
```

Output:

```
>>> Conectando a usuario@192.168.1.100...
[OK] Conexion SSH
>>> Activo: blue -> Deployando: green (puertos 3002/8002)
>>> Subiendo .env...
>>> Ejecutando deploy...

1/7 Bajando cambios del repositorio...
2/7 Construyendo nuevas imagenes (esto puede tardar unos minutos)...
3/7 Levantando infraestructura (DB, Redis)...
4/7 Levantando aplicacion (green)...
5/7 Verificando que la aplicacion responda...
    OK - La aplicacion responde correctamente
6/7 Aplicando migraciones de base de datos...
7/7 Cambiando trafico a la nueva version...

Apagando version anterior (blue)...
Limpiando imagenes viejas...

[OK] Deploy completado - Ambiente activo: green
```

## Si algo sale mal

### El deploy fallo a mitad de camino

No pasa nada. La version anterior sigue funcionando.

```bash
make deploy
```

### La nueva version tiene un bug

```bash
make deploy-rollback
```

Esto vuelve automaticamente a la version anterior.

### Ya arregle el bug despues del rollback

```bash
# Commitear el fix
git add . && git commit -m "fix: ..." && git push

# Deployar de nuevo (va al ambiente que tenia el bug, ahora con el fix)
make deploy
```

### No me puedo conectar al servidor

```bash
# Probar conexion manual
ssh tu_usuario@192.168.1.100

# Verificar que .env.deploy tenga los datos correctos
cat .env.deploy
```

## Estructura en el servidor

```
/opt/dashboard/           # REMOTE_DIR
├── active_env                # Archivo que dice "blue" o "green"
└── app/                      # Repositorio clonado
    ├── .env                  # Variables de produccion (generado por deploy)
    ├── compose.prod.yaml     # App (frontend, api, celery)
    ├── compose.prod.infra.yaml # Infraestructura (db, redis)
    └── ...
```

## Configuracion HTTPS

NextAuth (el sistema de autenticacion) requiere HTTPS para setear cookies seguras. Sin HTTPS, el login no funcionara correctamente.

### Opcion A: Certificado autofirmado (para red interna)

Ideal para servidores en red local sin dominio publico.

```bash
# Conectate al servidor
make deploy-ssh

# Generar certificado autofirmado (valido por 1 año)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/epidemiologia.key \
  -out /etc/ssl/certs/epidemiologia.crt \
  -subj "/CN=192.168.1.100"

# Editar nginx.conf para habilitar HTTPS
sudo nano /etc/nginx/sites-enabled/dashboard.conf
# Descomentar la seccion HTTPS del archivo

# Verificar y recargar Nginx
sudo nginx -t && sudo systemctl reload nginx

# Salir
exit
```

> **Nota:** El browser mostrara una advertencia de "conexion no segura" porque el certificado es autofirmado. Podes ignorarla haciendo click en "Avanzado" > "Continuar".

### Opcion B: Let's Encrypt (con dominio publico)

Requiere:
- Un dominio publico (ej: `epidemiologia.miorganizacion.gob.ar`)
- Que el servidor sea accesible desde internet en puertos 80 y 443

```bash
# Conectate al servidor
make deploy-ssh

# Instalar certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado (reemplaza con tu dominio)
sudo certbot --nginx -d epidemiologia.miorganizacion.gob.ar

# Certbot configura Nginx automaticamente y renueva el certificado cada 90 dias

# Salir
exit
```

### Despues de configurar HTTPS

1. Actualizar `.env.deploy` con URLs HTTPS:

```bash
NEXT_PUBLIC_API_HOST=https://192.168.1.100  # o tu dominio
FRONTEND_URL=https://192.168.1.100
NEXTAUTH_URL=https://192.168.1.100
CORS_ORIGINS=https://192.168.1.100
```

2. Hacer deploy para que tome los cambios:

```bash
make deploy
```

### Troubleshooting HTTPS

**Error: Cookie rejected because non-HTTPS**

El login falla porque NextAuth intenta setear cookies seguras pero estas usando HTTP.

Solucion: Configurar HTTPS (ver arriba).

**NextAuth devuelve `{"url":"http://localhost:3000"}`**

La variable `NEXTAUTH_URL` no esta configurada correctamente.

Solucion:
1. Verificar que `.env.deploy` tenga `NEXTAUTH_URL=https://tu-ip-o-dominio`
2. Hacer `make deploy` para reconstruir el frontend

**El browser muestra "Conexion no segura"**

Normal si usas certificado autofirmado. Podes:
- Ignorar la advertencia (click en "Avanzado" > "Continuar")
- O usar Let's Encrypt si tenes dominio publico

## Glosario

| Termino | Que significa |
|---------|---------------|
| **Deploy** | Subir una nueva version de la aplicacion al servidor |
| **Blue/Green** | Tecnica de tener dos copias para actualizar sin cortes |
| **Nginx** | Programa que recibe las peticiones y las manda a la app |
| **Docker Compose** | Herramienta para definir y correr aplicaciones multi-contenedor |
| **Health check** | Verificar que la aplicacion responde antes de mandar usuarios |
| **SSH** | Protocolo para conectarse de forma segura a un servidor |
| **Deploy key** | Clave SSH especifica para un repositorio (no asociada a una persona) |
| **Rollback** | Volver a la version anterior de la aplicacion |
| **HTTPS/SSL** | Conexion encriptada entre el browser y el servidor |
| **Certificado autofirmado** | Certificado SSL generado localmente (sin autoridad certificadora) |
| **Let's Encrypt** | Servicio gratuito de certificados SSL validos |
