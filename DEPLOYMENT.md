# Railway Deployment Guide

## 🚀 Quick Deploy to Railway

### Prerequisites
- Railway account (sign up at https://railway.app)
- Git repository connected to Railway

### Step 1: Create New Project on Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `Briefly-backend` repository

### Step 2: Configure Environment Variables

In your Railway project dashboard, add these environment variables:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ARCADE_API_KEY=your_arcade_api_key_here
```

### Step 3: Deploy

Railway will automatically:
1. Detect the Dockerfile
2. Build your container
3. Deploy to a public URL

### Step 4: Verify Deployment

Once deployed, Railway will provide a public URL (e.g., `https://your-app.railway.app`)

Test your deployment:
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

### Step 5: Test the Meeting Prep Endpoint

```bash
curl -X POST https://your-app.railway.app/summarize \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Prep me for standup"}'
```

## 🔧 Configuration

### Port Configuration
Railway automatically sets the `PORT` environment variable. The Dockerfile is configured to use this.

### CORS Configuration
Currently configured to allow all origins (`*`). For production, update `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Logging
Logs are available in the Railway dashboard under "Deployments" → "Logs"

## 📊 Monitoring

### Health Check
- Endpoint: `/health`
- Interval: 30s
- Available in Railway metrics

### Logs
View real-time logs in Railway dashboard:
- Application logs
- Build logs
- Deployment logs

## 🔄 Continuous Deployment

Railway automatically redeploys when you push to your main branch:

```bash
git add .
git commit -m "Update meeting prep agent"
git push origin main
```

## 🛠️ Local Docker Testing

Test your Docker build locally before deploying:

```bash
# Build
docker build -t briefly-backend .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  -e ARCADE_API_KEY=your_key \
  briefly-backend

# Test
curl http://localhost:8000/health
```

## 🐛 Troubleshooting

### Build Fails
- Check Railway build logs
- Verify all dependencies in `requirements.txt`
- Ensure Dockerfile syntax is correct

### Runtime Errors
- Verify all environment variables are set
- Check application logs in Railway dashboard
- Test API endpoints individually

### Slow Response Times
- Check LangGraph node execution times in logs
- Consider adding caching for repeated requests
- Monitor Railway metrics for resource usage

## 📝 Notes

- Railway free tier includes 500 hours/month
- Domain will be `*.railway.app` (can add custom domain)
- Auto-scaling available on paid plans
- Database can be added via Railway marketplace

