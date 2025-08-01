#!/bin/bash

# 🚀 Manifest 12 - Vercel Deployment Script

echo "🎉 Starting Manifest 12 Deployment to Vercel..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo -e "${RED}❌ Error: vercel.json not found. Run this from the project root.${NC}"
    exit 1
fi

echo -e "${BLUE}📍 Current directory: $(pwd)${NC}"

# Step 1: Install Vercel CLI if not installed
echo -e "${YELLOW}🔧 Checking Vercel CLI...${NC}"
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Vercel CLI...${NC}"
    npm install -g vercel
else
    echo -e "${GREEN}✅ Vercel CLI already installed${NC}"
fi

# Step 2: Build frontend to check for errors
echo -e "${YELLOW}🏗️ Building frontend to check for errors...${NC}"
cd frontend
npm install
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend build successful!${NC}"
else
    echo -e "${RED}❌ Frontend build failed! Fix errors before deploying.${NC}"
    exit 1
fi

cd ..

# Step 3: Check backend dependencies
echo -e "${YELLOW}🐍 Checking backend dependencies...${NC}"
cd backend
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✅ requirements.txt found${NC}"
    echo "📋 Python dependencies:"
    head -5 requirements.txt
    echo "   ... and $(wc -l < requirements.txt) total dependencies"
else
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi

cd ..

# Step 4: Show project structure
echo -e "${YELLOW}📁 Project structure for Vercel:${NC}"
echo "manifest12/"
echo "├── frontend/ (React app)"
echo "├── backend/ (FastAPI app)"
echo "├── vercel.json (deployment config)"
echo "└── README.md"

# Step 5: Login to Vercel
echo -e "${PURPLE}🔐 Please login to Vercel...${NC}"
vercel login

# Step 6: Deploy to Vercel
echo -e "${YELLOW}🚀 Deploying to Vercel...${NC}"
echo -e "${BLUE}This will:${NC}"
echo "  • Build your React frontend"
echo "  • Deploy your FastAPI backend"
echo "  • Generate a live URL"
echo "  • Set up automatic deployments"

vercel

# Step 7: Production deployment
echo -e "${YELLOW}🌟 Deploying to production...${NC}"
vercel --prod

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo -e "${PURPLE}📝 Next steps:${NC}"
    echo "1. Set up MongoDB Atlas database"
    echo "2. Configure environment variables in Vercel dashboard"
    echo "3. Update REACT_APP_BACKEND_URL with your Vercel URL"
    echo "4. Test all functionality"
    echo ""
    echo -e "${BLUE}🔗 Your app is live at: https://your-app.vercel.app${NC}"
    echo -e "${BLUE}⚙️ Configure it at: https://vercel.com/dashboard${NC}"
else
    echo -e "${RED}❌ Deployment failed! Check the logs above.${NC}"
    exit 1
fi

echo -e "${GREEN}✨ Manifest 12 is now live on Vercel! ✨${NC}"