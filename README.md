# Deploying CCAD RTLS Dashboard (Docker)

## 📦 structure
Move these files to your VPS into a folder named `ccad_dashboard`:
```
/ccad_dashboard
  ├── Dockerfile
  ├── requirements.txt
  ├── app.py
  ├── db_init.py
  └── templates/
      ├── login.html
      └── index.html
```

## 🚀 Build & Run

### 1. Build the Image
```bash
docker build -t ccad-dashboard .
```

### 2. Run the Container
Run on port 80 (standard web port):
```bash
docker run -d -p 80:80 --name rtls_app \
  -v $(pwd)/instance:/app/instance \
  -v $(pwd)/uploads:/app/uploads \
  ccad-dashboard
```
*Note: We mount volumes (`-v`) so that the Database and Uploads persist even if you restart the container.*

### 3. Initialize Database
For the first run, you need to seed the database:
```bash
# Enter the running container
docker exec -it rtls_app python db_init.py
```

## 🌐 Domain Setup (Nginx)
To point `ccad.ign3el.com` to this container, add this to your Nginx config:

```nginx
server {
    server_name ccad.ign3el.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔑 Default Credentials
*   **URL**: `http://ccad.ign3el.com/login`
*   **Password**: `CCAD2026` (Change this in `app.py`)
