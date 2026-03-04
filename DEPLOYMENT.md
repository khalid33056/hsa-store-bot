# Render Deployment Guide for HSA Store Bot

## Prerequisites
- GitHub account with your bot repository
- Render account (sign up at https://render.com)
- Telegram Bot Token from @BotFather
- Admin Telegram User ID
- Firebase service account credentials (firebase-key.json)

## Step-by-Step Deployment

### 1. Prepare Firebase Credentials
1. Open your `firebase-key.json` file
2. Copy the entire JSON content
3. Minify it to a single line (remove line breaks)
4. Keep it ready for the next step

### 2. Create a New Web Service on Render
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `https://github.com/khalid33056/hsa-store-bot.git`
4. Configure the service:
   - **Name**: `hsa-store-bot` (or your choice)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: `Free` (or paid for better performance)

### 3. Set Environment Variables
In the Render dashboard, add these environment variables:

#### Required Variables:
1. **GOOGLE_APPLICATION_CREDENTIALS**
   - Value: Paste the entire firebase-key.json content as a single-line JSON string
   - Example: `{"type":"service_account","project_id":"telegrambot-f7128",...}`

2. **BOT_TOKEN** (if you modify bot.py to use env vars)
   - Value: Your Telegram bot token from @BotFather
   - Example: `8673798950:AAFe8Iko5CVT5UzovpxRNcYg8qk3iP_RgQQ`

3. **ADMIN_ID** (if you modify bot.py to use env vars)
   - Value: Your Telegram user ID
   - Example: `7107553688`

### 4. Alternative: Using Render Blueprint (render.yaml)
If you push `render.yaml` to your repo, Render will automatically detect it:
1. Go to Render Dashboard
2. Click **"New +"** → **"Blueprint"**
3. Connect your repository
4. Render will read `render.yaml` and configure automatically

### 5. Deploy
1. Click **"Create Web Service"**
2. Render will start building and deploying
3. Monitor the logs for any errors
4. Once deployed, your bot will start automatically

### 6. Verify Deployment
1. Open your Telegram app
2. Send `/start` to your bot
3. Bot should respond with the welcome message

## Important Notes

### Firebase Credentials
Since firebase-key.json is in .gitignore (security best practice), you must:
- Store the JSON content in Render's environment variables, OR
- Use Render's secret files feature to upload firebase-key.json

### Firestore Database
- Your bot uses Firestore for data storage
- Make sure your Firebase project has Firestore enabled
- Database rules should allow read/write from your service account

### Bot Token Security
Never commit your bot token or firebase credentials to GitHub!
Always use environment variables for sensitive data.

### Free Tier Limitations
Render free tier:
- Spins down after 15 minutes of inactivity
- Takes ~30 seconds to wake up on first request
- Consider paid tier for 24/7 availability

### Logs and Monitoring
- View logs in Render Dashboard → Your Service → Logs
- Monitor bot performance and errors in real-time

## Updating Your Bot
1. Push changes to GitHub: `git push origin main`
2. Render automatically detects changes and redeploys
3. Or manually redeploy from Render Dashboard

## Troubleshooting

### Bot Not Responding
- Check Render logs for errors
- Verify environment variables are set correctly
- Ensure Firebase credentials are valid
- Check bot token is correct

### Database Errors
- Verify GOOGLE_APPLICATION_CREDENTIALS is properly formatted
- Check Firebase project permissions
- Ensure Firestore is enabled in your Firebase project

### Build Failures
- Check requirements.txt has all dependencies
- Verify Python version compatibility
- Review build logs for specific errors

## Support
For issues, check:
- Render logs (in dashboard)
- Firebase console (for database issues)
- Telegram bot logs (for bot-specific errors)

---

## Quick Commands
```bash
# Test locally before deploying
python bot.py

# Check requirements
pip install -r requirements.txt

# Push to GitHub
git add .
git commit -m "Deploy to Render"
git push origin main
```

## Environment Variables Template
```bash
GOOGLE_APPLICATION_CREDENTIALS={"type":"service_account","project_id":"telegrambot-f7128",...}
BOT_TOKEN=8673798950:AAFe8Iko5CVT5UzovpxRNcYg8qk3iP_RgQQ
ADMIN_ID=7107553688
```
