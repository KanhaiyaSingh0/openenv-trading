# OpenEnv Hackathon Submission Guide

**DEADLINE: April 8, 2026 - 11:59 PM**

---

## **STEP 1: Push to GitHub** ⏱️ (5 minutes)

Copy-paste these commands **one by one** into PowerShell:

```powershell
# 1. Configure git (do this once)
git config --global user.name "Kanhaiya Kumar Singh"
git config --global user.email "kanhaiyasingh453@gmail.com"

# 2. Initialize repo
cd C:\Users\kanha\OneDrive\Desktop\My_Project\OpenEnv_Hacathon\openEnv_proj
git init

# 3. Add all files
git add .

# 4. First commit
git commit -m "OpenEnv Trading Environment - Round 1 Submission"

# 5. Rename branch to main
git branch -M main

# 6. Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/openenv-trading

# 7. Push to GitHub
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username

---

## **STEP 2: Deploy to HuggingFace Spaces** ⏱️ (10 minutes)

### Option A: Direct Upload (Easiest)

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Space name:** `openenv-trading`
   - **License:** Apache 2.0
   - **Space SDK:** `Docker` ← **IMPORTANT**
   - **Private:** No (make public)
4. Click **"Create Space"**
5. You'll see the Space page
6. Click **"+ Add file"** → **"Upload files"**
7. Select these files from your folder:
   ```
   inference.py
   models.py
   client.py
   __init__.py
   Dockerfile
   openenv.yaml
   pyproject.toml
   README.md
   QUICK_START.md
   server/ (entire folder with all files)
   ```
8. Click **"Upload"** and **"Commit"**
9. **WAIT** 5-10 minutes for Docker build

### Option B: Git Push (Faster if you know git)

1. In your Space settings, find **"Clone repository"**
2. Copy the git URL
3. Run:
```powershell
cd C:\Users\kanha\OneDrive\Desktop\My_Project\OpenEnv_Hacathon\openEnv_proj
git remote add spaces <PASTE_URL_HERE>
git push -u spaces main
```

---

## **STEP 3: Test Your Space** ⏱️ (2 minutes)

Once the Space is built (you'll see "Running" status):

1. Copy your **Space URL** (looks like: https://kanhaiyasingh01-openenv-trading.hf.space)

2. Test it in PowerShell:
```powershell
$url = "https://YOUR_SPACE_URL"

# Test reset endpoint
curl -X POST "$url/reset" `
  -H "Content-Type: application/json" `
  -d '{"task":"easy"}' -v
```

Should return **200 OK** with JSON response ✅

---

## **STEP 4: Submit to Hackathon** ⏱️ (2 minutes)

1. Go to: https://scaler.com/openenv-hackathon (or your registration page)
2. Look for **"Submit Assessment"** button
3. Paste your **Space URL**:
   ```
   https://YOUR_USERNAME-openenv-trading.hf.space
   ```
4. Click **"Submit"**

✅ **Done!**

---

## **Checklist Before Submitting**

- [ ] GitHub repo created with all files
- [ ] HF Space created (Docker SDK)
- [ ] All files uploaded
- [ ] Space built successfully (15+ minutes max)
- [ ] `/reset` endpoint returns 200
- [ ] `/step` endpoint works
- [ ] Space URL submitted to hackathon portal

---

## **Troubleshooting**

### Space stuck on "Building"
- Wait up to 20 minutes
- If it fails, check the "Logs" tab in your Space

### 404 when testing endpoints
- Space might still be building
- Try again in 2 minutes

### Docker build errors
- Check that you uploaded ALL files in `server/` folder
- Make sure `Dockerfile` is at the root level
- Check Space logs for details

---

## **Final Submission Confirmation**

Once submitted, you should see a **confirmation message**.

**Deadline: April 8, 11:59 PM**

**Time left: ~30 hours** ⏰

---

## **Questions?**

If anything is unclear, ask me! I'm here to help. 💪

