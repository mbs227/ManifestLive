# 🎯 Environment Variables Setup for Vercel

## Required Environment Variables

Add these in your Vercel dashboard (Settings → Environment Variables):

### 🔑 Production Variables

```bash
# MongoDB Atlas Connection
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Database Name  
DB_NAME=manifest12_production

# JWT Secret Key (generate a strong one)
SECRET_KEY=your-super-secure-production-secret-key-minimum-32-characters

# Frontend API URL (will be your Vercel domain)
REACT_APP_BACKEND_URL=https://your-app-name.vercel.app
```

## 🔄 How to Set Environment Variables

### Method 1: Vercel Dashboard (Recommended)
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable with these settings:
   - **Key**: Variable name (e.g., `MONGO_URL`)
   - **Value**: Variable value (e.g., your MongoDB connection string)
   - **Environments**: Select `Production`, `Preview`, and `Development`

### Method 2: Vercel CLI
```bash
# Set environment variables via CLI
vercel env add MONGO_URL production
vercel env add DB_NAME production
vercel env add SECRET_KEY production
vercel env add REACT_APP_BACKEND_URL production
```

## 🔒 Generating Secure SECRET_KEY

### Option 1: Python
```python
import secrets
print(secrets.token_urlsafe(32))
# Example output: kQG8R7XzY9m4P1vN3wL2E5oS8jF6uA9cK0xZ7nM1qW4
```

### Option 2: OpenSSL
```bash
openssl rand -base64 32
# Example output: XyZ9mN2pQ1rS8vW5kL3oE7fA6nK0cH4jG9xM1yB8uD2
```

### Option 3: Online Generator
- Use [passwordsgenerator.net](https://passwordsgenerator.net/)
- Select 32+ characters, include symbols

## 🗄️ MongoDB Atlas Setup

### 1. Create Free Account
- Go to [cloud.mongodb.com](https://cloud.mongodb.com)
- Sign up for free account
- Choose M0 free tier (512MB storage)

### 2. Create Cluster
- Select cloud provider (AWS recommended)
- Choose region closest to your users
- Name your cluster (e.g., `manifest12-cluster`)

### 3. Database Access
- Create database user
- Username: `manifest12user` 
- Password: Generate strong password
- Permissions: Read and write to any database

### 4. Network Access
- Add IP address: `0.0.0.0/0` (allow all)
- This is needed for Vercel serverless functions

### 5. Get Connection String
- Click "Connect" → "Connect your application"
- Copy the connection string
- Replace `<password>` with your database user password
- Example: `mongodb+srv://manifest12user:yourpassword@manifest12-cluster.abc123.mongodb.net/?retryWrites=true&w=majority`

## 🔄 Data Migration to Atlas

### Export from Local MongoDB
```bash
# Create backup of your local database
mongodump --db manifest12_database --out ./backup

# List what was backed up
ls -la backup/manifest12_database/
```

### Import to MongoDB Atlas
```bash
# Restore to Atlas (replace with your connection string)
mongorestore --uri "mongodb+srv://username:password@cluster.mongodb.net/" backup/manifest12_database/

# Verify data was imported
mongosh "mongodb+srv://username:password@cluster.mongodb.net/" --eval "use manifest12_database; db.users.countDocuments()"
```

## ✅ Environment Variables Checklist

- [ ] `MONGO_URL` - MongoDB Atlas connection string
- [ ] `DB_NAME` - Set to `manifest12_production`  
- [ ] `SECRET_KEY` - 32+ character secure key
- [ ] `REACT_APP_BACKEND_URL` - Your Vercel app URL

## 🧪 Testing Environment Variables

### Test MongoDB Connection
```python
# Test script (run locally)
import os
from motor.motor_asyncio import AsyncIOMotorClient

mongo_url = "your-atlas-connection-string"
client = AsyncIOMotorClient(mongo_url)
db = client["manifest12_production"]

# Test connection
try:
    await client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
```

### Test API Endpoints
```bash
# Test your deployed API
curl https://your-app.vercel.app/api/
# Should return: {"message": "Manifest 12 API - Transform Your Life in 12 Weeks"}

# Test authentication endpoint
curl -X POST https://your-app.vercel.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass","full_name":"Test User"}'
```

## 🚨 Security Best Practices

### ✅ Do's
- Use strong, unique passwords
- Generate random SECRET_KEY  
- Use environment variables for all secrets
- Enable MongoDB authentication
- Use HTTPS only (Vercel provides this)

### ❌ Don'ts  
- Don't commit secrets to Git
- Don't use weak passwords
- Don't hardcode credentials in code
- Don't disable CORS in production
- Don't use default/example keys

## 🔧 Troubleshooting

### Common Issues

#### ❌ "Database connection failed"
- Check MONGO_URL format
- Verify database user permissions
- Ensure IP address 0.0.0.0/0 is whitelisted

#### ❌ "JWT token invalid"
- Verify SECRET_KEY is set correctly
- Ensure key is 32+ characters
- Check for extra spaces in environment variable

#### ❌ "CORS error"
- Update backend CORS to include your Vercel domain
- Verify REACT_APP_BACKEND_URL is correct
- Check frontend is calling correct API URL

#### ❌ "Environment variable not found"
- Verify variable name spelling
- Check it's set for correct environment
- Redeploy after adding variables

## 📞 Support Resources

- **Vercel Docs**: [vercel.com/docs/concepts/projects/environment-variables](https://vercel.com/docs/concepts/projects/environment-variables)
- **MongoDB Atlas**: [docs.atlas.mongodb.com](https://docs.atlas.mongodb.com)
- **Vercel Community**: [github.com/vercel/vercel/discussions](https://github.com/vercel/vercel/discussions)

Your environment variables are the key to a successful deployment! 🔑✨