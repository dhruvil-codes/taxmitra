# PythonAnywhere Deployment Guide for Tax Mitra V2
# No credit card required, completely free tier available

## Step-by-Step PythonAnywhere Deployment:

### 1. Create PythonAnywhere Account
- Go to https://www.pythonanywhere.com
- Sign up for free account (no credit card required)
- Confirm email address

### 2. Create New Web App
- Go to "Web" tab → "Add a new web app"
- Choose "Manual Configuration"
- **Project Name**: tax-mitra
- **Python Version**: 3.11
- Click "Next"

### 3. Configure Web App Settings
- **Working Directory**: /home/yourusername/tax-mitra/backend
- **Virtual Environment Location**: /home/yourusername/tax-mitra/backend/venv
- **GitHub Repository**: https://github.com/dhruvil-codes/taxmitra.git
- **Branch**: main
- **Source Code**: /home/yourusername/tax-mitra/backend

### 4. Set Start Command
- **WSGI Configuration File**: pythonanywhere_startup.sh
- **Or use**: gunicorn app.main:app --workers 1 --threads 2 --bind 0.0.0.0:8000

### 5. Set Environment Variables
- **DEMO_MODE**: true
- **OPENAI_API_KEY**: (your OpenAI API key)

### 6. Install System Dependencies (in Bash Console)
```bash
# In PythonAnywhere Bash console:
sudo apt-get install tesseract-ocr tesseract-ocr-hin
```

### 7. Static Files (for frontend - optional)
- **URL**: /static/
- **Directory**: /home/yourusername/tax-mitra/frontend/dist

### 8. Test Deployment
- Check the web app URL: https://yourusername.pythonanywhere.com
- Test health endpoint: https://yourusername.pythonanywhere.com/api/health
- Update Vercel environment variable if using separate frontend