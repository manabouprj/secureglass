# How to Upload SecureGlass to GitHub

## Prerequisites
- Git installed (`git --version` to verify)
- GitHub account (github.com)
- GitHub CLI optional but recommended (`gh --version`)

---

## Method 1: GitHub Web Interface (Simplest — no Git required)

1. **Create the repository**
   - Go to https://github.com/new
   - Repository name: `secureglass`
   - Description: `Multi-Vertical Security Intelligence Platform — Single Pane of Glass`
   - Set to **Public** (required for GitHub Pages demo)
   - Check **Add a README file**
   - Click **Create repository**

2. **Upload files via drag and drop**
   - In your new repo, click **Add file → Upload files**
   - Drag and drop in this order:
     - `frontend/index.html` → upload to a `frontend/` folder
     - `docs/HLD.md` → upload to `docs/`
     - `docs/LLD.md` → upload to `docs/`
     - `data/generate_demo.py` → upload to `data/`
     - `README.md` → root
     - `docker-compose.yml` → root
   - Commit message: `feat: initial release — multi-vertical security dashboard`
   - Click **Commit changes**

3. **Enable GitHub Pages (for live demo link)**
   - Go to **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: `main`, Folder: `/frontend`
   - Click **Save**
   - Your live URL will be: `https://manabouprj.github.io/secureglass/`

---

## Method 2: Git CLI (Recommended for ongoing development)

### Step 1: Prepare local files
```bash
# Create the project folder structure
mkdir -p secureglass/frontend
mkdir -p secureglass/docs
mkdir -p secureglass/data
mkdir -p secureglass/src

# Copy your downloaded files into place
cp sentinel-glass-dashboard.html  secureglass/frontend/index.html
cp HLD.md                          secureglass/docs/HLD.md
cp LLD.md                          secureglass/docs/LLD.md
cp README.md                       secureglass/README.md
cp generate_demo.py                secureglass/data/generate_demo.py
cp docker-compose.yml              secureglass/docker-compose.yml
```

### Step 2: Initialise Git
```bash
cd secureglass
git init
git branch -M main
```

### Step 3: Create .gitignore
```bash
cat > .gitignore << 'GITEOF'
.env
*.pyc
__pycache__/
node_modules/
.DS_Store
*.log
*.sqlite
postgres_data/
GITEOF
```

### Step 4: Create .env.example
```bash
cat > .env.example << 'ENVEOF'
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# CrowdStrike Falcon
CROWDSTRIKE_CLIENT_ID=your-client-id
CROWDSTRIKE_CLIENT_SECRET=your-client-secret
CROWDSTRIKE_BASE_URL=https://api.crowdstrike.com

# Mimecast
MIMECAST_CLIENT_ID=your-client-id
MIMECAST_CLIENT_SECRET=your-client-secret

# Qualys
QUALYS_USERNAME=your-username
QUALYS_PASSWORD=your-password
QUALYS_API_URL=https://qualysapi.qg1.apps.qualys.eu

# Database (Phase 2)
POSTGRES_URL=postgresql://user:pass@localhost:5432/secureglass
REDIS_URL=redis://localhost:6379
ENVEOF
```

### Step 5: Stage and commit
```bash
git add .
git status   # verify files look correct
git commit -m "feat: initial release — SecureGlass multi-vertical security dashboard

- 5 industry verticals: Enterprise, Healthcare, Financial, Energy, Retail
- 20 security controls per vertical
- HLD and LLD documentation
- Synthetic data generator
- Docker Compose demo deployment"
```

### Step 6: Create GitHub repo and push
```bash
# Create repo via GitHub CLI (if installed)
gh repo create secureglass --public --description "Multi-Vertical Security Intelligence Platform"

# OR manually: go to github.com/new, create 'secureglass' (empty, no README)

# Add remote and push
git remote add origin https://github.com/manabouprj/secureglass.git
git push -u origin main
```

### Step 7: Enable GitHub Pages
```bash
# Via GitHub CLI
gh api repos/manabouprj/secureglass/pages \
  --method POST \
  --field source='{"branch":"main","path":"/frontend"}'

# OR via web: Settings → Pages → Branch: main, Folder: /frontend → Save
```

---

## Method 3: GitHub CLI (Fastest — one-liner create + push)

```bash
cd secureglass

# Authenticate first (one time)
gh auth login

# Create repo and push in one command
gh repo create secureglass \
  --public \
  --description "Multi-Vertical Security Intelligence Platform — Single Pane of Glass" \
  --source=. \
  --push

# Enable Pages
gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pages \
  --method POST \
  --field source='{"branch":"main","path":"/frontend"}'
```

---

## Post-Upload Checklist

- [ ] Confirm `https://github.com/manabouprj/secureglass` is accessible
- [ ] Open `frontend/index.html` via raw link — verify dashboard loads
- [ ] GitHub Pages URL works: `https://manabouprj.github.io/secureglass/`
- [ ] Add repo topics: `security`, `dashboard`, `siem`, `soc`, `cybersecurity`, `devsecops`, `enterprise-security`
  - Settings → Topics → add tags
- [ ] Add a social preview image (Settings → Social preview)
- [ ] Pin the repo to your GitHub profile
- [ ] Share the GitHub Pages link as the live demo in your README badge

---

## Adding a GitHub Pages Badge to README

Once Pages is live, add this to the top of README.md:

```markdown
[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-4f8bff?style=flat-square&logo=github)](https://manabouprj.github.io/secureglass/)
```

---

## Updating the Repo Later

```bash
# After making changes locally
git add .
git commit -m "feat: add healthcare vertical OT enhancements"
git push

# GitHub Pages auto-redeploys on push to main — no action needed
```

---

## Repository Settings Recommended

| Setting | Value |
|---------|-------|
| Visibility | Public |
| Default branch | `main` |
| Issues | Enabled |
| Discussions | Optional |
| Pages source | Branch: main, Folder: /frontend |
| Security advisories | Enabled |
| Dependabot alerts | Enabled |

