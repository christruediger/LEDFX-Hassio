# GitHub Setup Instructions

Follow these steps to publish your LEDFX Home Assistant integration to GitHub:

## 1. Create a GitHub Account (if needed)
- Go to https://github.com
- Sign up for a free account
- Verify your email

## 2. Create a New Repository

1. Click the "+" icon in the top right → "New repository"
2. Repository name: `ledfx-homeassistant` (or your preferred name)
3. Description: `Home Assistant integration for LEDFX LED controllers`
4. Choose **Public** (required for HACS)
5. **Do NOT** initialize with README (we have our own)
6. Click "Create repository"

## 3. Upload Your Files

### Option A: GitHub Web Interface (Easiest)

1. On your new repository page, click "uploading an existing file"
2. Drag and drop all files from the `ledfx_integration` folder
3. **Important**: Maintain the folder structure:
   ```
   custom_components/
     ledfx/
       __init__.py
       config_flow.py
       const.py
       ledfx_client.py
       light.py
       select.py
       manifest.json
       strings.json
   README.md
   LICENSE
   hacs.json
   .gitignore
   ```
4. Commit message: "Initial commit"
5. Click "Commit changes"

### Option B: Git Command Line

If you have Git installed:

```bash
# Navigate to your ledfx_integration folder
cd /path/to/ledfx_integration

# Initialize git
git init

# Add all files
git add .

# Make first commit
git commit -m "Initial commit"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR-USERNAME/ledfx-homeassistant.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 4. Create a Release (Required for HACS)

1. Go to your repository on GitHub
2. Click "Releases" on the right sidebar
3. Click "Create a new release"
4. Tag version: `v1.0.0`
5. Release title: `Initial Release v1.0.0`
6. Description:
   ```
   Initial release of LEDFX Home Assistant integration
   
   Features:
   - RGB color control
   - Brightness adjustment
   - Audio-reactive and static effects
   - 8 gradient presets
   - Device status monitoring
   ```
7. Click "Publish release"

## 5. Add to HACS

Now users can add your integration:

1. In Home Assistant → HACS → Integrations
2. Click three dots (top right) → Custom repositories
3. Add URL: `https://github.com/YOUR-USERNAME/ledfx-homeassistant`
4. Category: Integration
5. Click "Add"

## 6. Update README

Don't forget to update the README.md file and replace:
- `YOUR-USERNAME` with your actual GitHub username

## 7. Optional: Add a Logo

Create a `logo.png` (256x256px) with your integration's logo and add it to the root of the repository.

## 8. Make It Official (Optional)

To get your integration added to the default HACS repository list:
1. Make sure your integration follows all HACS requirements
2. Submit it to https://github.com/hacs/default
3. Follow their submission process

## Done! 🎉

Your integration is now:
- ✅ Published on GitHub
- ✅ Available for HACS installation
- ✅ Open source for the community

Users can now install it via HACS using your repository URL!

## Future Updates

When you make changes:
1. Commit and push your changes to GitHub
2. Create a new release with an incremented version (v1.0.1, v1.1.0, etc.)
3. HACS users will see the update available
