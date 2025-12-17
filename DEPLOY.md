# Deploy to Netlify

This project is configured to deploy to Netlify with serverless functions for the AI backends.

## Prerequisites

1. **Netlify Account** - Sign up at [netlify.com](https://netlify.com)
2. **OpenAI API Key** - Get one from [platform.openai.com](https://platform.openai.com)
3. **Git Repository** - Push this project to GitHub/GitLab/Bitbucket

## Quick Deploy

### Option 1: Deploy from Git (Recommended)

1. **Push to Git:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GIT_URL
   git push -u origin main
   ```

2. **Connect to Netlify:**
   - Go to [app.netlify.com](https://app.netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect your Git provider
   - Select your repository

3. **Configure Build Settings:**
   - Build command: `echo "No build needed"`
   - Publish directory: `character_files`
   - Functions directory: `netlify/functions`

4. **Set Environment Variable:**
   - Go to Site Settings → Environment Variables
   - Add: `OPENAI_API_KEY` = `sk-your-key-here`

5. **Deploy!**
   - Click "Deploy site"
   - Wait for deployment to complete
   - Your site will be live at: `your-site-name.netlify.app`

### Option 2: Netlify CLI

1. **Install Netlify CLI:**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify:**
   ```bash
   netlify login
   ```

3. **Initialize & Deploy:**
   ```bash
   netlify init
   netlify env:set OPENAI_API_KEY "sk-your-key-here"
   netlify deploy --prod
   ```

## Important Notes

### VRM Files
The VRM models in `animation vr1/`, `animation vr2/`, `animation vr3/`, `animation vr4/` need to be accessible. Either:
1. Move them to `character_files/models/` folder
2. Update VRM paths in HTML files to use relative paths from `character_files/`

### File Structure for Netlify
```
character_files/          ← Published to web (PUBLIC)
├── main.html            ← Landing page
├── index.html           ← Nicky
├── luna.html            ← Luna
├── cypher.html          ← Cypher
├── oracle.html          ← Oracle
└── models/              ← VRM files (move here)
    ├── nicky.vrm
    ├── luna.vrm
    ├── cypher.vrm
    └── oracle.vrm

netlify/
└── functions/           ← Serverless backend
    ├── nicky-chat.js
    ├── luna-chat.js
    ├── cypher-chat.js
    └── oracle-chat.js
```

### Update VRM Paths

Before deploying, update these lines in each HTML file:

**index.html (Nicky):**
```javascript
const VRM_PATH = './models/nicky.vrm';  // or 'models/nicky.vrm'
```

**luna.html:**
```javascript
const VRM_PATH = './models/luna.vrm';
```

**cypher.html:**
```javascript
const VRM_PATH = './models/cypher.vrm';
```

**oracle.html:**
```javascript
const VRM_PATH = './models/oracle.vrm';
```

## Testing Locally with Netlify Dev

```bash
npm install
netlify dev
```

This runs the functions locally at `http://localhost:8888`

## Environment Variables Needed

- `OPENAI_API_KEY` - Your OpenAI API key (REQUIRED)

## Features on Netlify

✅ All AI companions work (Nicky, Luna, Cypher, Oracle)
✅ Voice chat (speech-to-text in browser, text-to-speech from backend)
✅ 3D VRM avatars
✅ Real-time crypto data (Cypher via DexScreener)
✅ Interactive touch/click responses
✅ Serverless - scales automatically

## Troubleshooting

**"OPENAI_API_KEY not set"**
- Add the environment variable in Netlify dashboard
- Redeploy after adding

**VRM models not loading:**
- Check file paths are correct
- Ensure VRM files are in published directory
- Check browser console for 404 errors

**Functions timing out:**
- OpenAI API calls can take 5-10 seconds
- Netlify functions have 10s timeout on free tier, 26s on pro

**CORS errors:**
- Should be handled by functions
- Check function logs in Netlify dashboard

## Cost Estimate

- **Netlify:** Free tier includes 125k function requests/month
- **OpenAI:** ~$0.01-0.02 per conversation (chat + TTS)

## Support

Check function logs: Netlify Dashboard → Functions → [function name] → Recent logs






