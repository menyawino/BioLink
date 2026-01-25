# BioLink Migration Guide

## Moving to a Bigger Machine

### Step 1: Prepare the Source Machine
```bash
# Stop all services
docker compose down

# Create a compressed archive
tar -czf biolink-backup.tar.gz .
```

### Step 2: Transfer to Target Machine
```bash
# Copy the archive
scp biolink-backup.tar.gz user@target-machine:~

# Or use rsync for large files
rsync -avz . user@target-machine:~/biolink-code/
```

### Step 3: Setup on Target Machine
```bash
# Extract if using tar
tar -xzf biolink-backup.tar.gz
cd biolink-code

# Run the automated setup (GPU will be auto-detected and configured)
./setup-and-test.sh
```

### Step 4: Performance Optimization (Optional)

**GPU acceleration is now automatically configured** during setup based on your hardware:
- **Apple Silicon (M1/M2/M3)**: GPU automatically enabled
- **NVIDIA GPUs**: Docker GPU passthrough automatically configured  
- **AMD GPUs**: ROCm support detected (limited Docker support)

For manual GPU configuration or advanced settings:
Edit `docker-compose.yml` and add GPU support:
```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

#### For Larger Models
Edit `backend-py/.env.docker`:
```bash
OLLAMA_MODEL=llama3.2:7b
# or
OLLAMA_MODEL=llama3.2:13b
```

#### For More Memory
```bash
# Increase Docker memory limits
# Or add swap space
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Step 5: Verify Migration
```bash
# Run tests
./scripts/quick_test.sh

# Check performance
time curl -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "How many patients are there?"}'
```

## Troubleshooting

### Common Issues

**Docker not starting**:
```bash
# Check Docker service
sudo systemctl status docker
sudo systemctl start docker

# On macOS, start Docker Desktop
```

**Port conflicts**:
```bash
# Check what's using ports
lsof -i :3000
lsof -i :3001
lsof -i :5432

# Change ports in docker-compose.yml if needed
```

**Memory issues**:
```bash
# Check memory usage
docker stats

# Free up memory
docker system prune -a
```

**Model download failures**:
```bash
# Pull models manually
docker exec biolink-ollama ollama pull llama3.2:3b

# Check model status
docker exec biolink-ollama ollama list
```

### Performance Tuning

**For CPU-only machines**:
- Use smaller models: `phi3:mini` or `llama3.2:1b`
- Reduce context length to 2048
- Add more heuristics to reduce LLM usage

**For GPU machines**:
- Use larger models: `llama3.2:7b` or `llama3.2:13b`
- Increase context length to 4096-8192
- Enable flash attention

**For high-memory machines**:
- Use multiple Ollama instances
- Enable model caching
- Increase batch sizes

## Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:3001/health

# Service status
docker compose ps

# Logs
docker compose logs -f backend
```

### Performance Metrics
```bash
# Response times
time ./tests/test_agent.sh

# Resource usage
docker stats

# Database performance
docker exec biolink-postgres pg_stat_activity
```

## Backup and Recovery

### Regular Backups
```bash
# Database backup
docker exec biolink-postgres pg_dump -U biolink biolink > backup.sql

# Full container backup
docker commit biolink-postgres biolink-postgres-backup
```

### Recovery
```bash
# Restore database
docker exec -i biolink-postgres psql -U biolink biolink < backup.sql

# Restore from image
docker run --name temp-postgres biolink-postgres-backup
docker cp temp-postgres:/var/lib/postgresql/data/. ./postgres-data/
docker stop temp-postgres
```