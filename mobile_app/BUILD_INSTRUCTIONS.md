# 📱 How to Build & Download the Android `.apk` App File

Follow these 4 simple steps to compile this mobile app project into a downloadable **`.apk` file** for Android phones:

---

## Step 1: Open Terminal in `mobile_app` Folder
Open PowerShell or Terminal on your computer and navigate into the `mobile_app` directory:

```bash
cd mobile_app
```

---

## Step 2: Install Expo EAS Build CLI
Run:
```bash
npm install -g eas-cli
```

---

## Step 3: Login to Expo (Free Account)
Run:
```bash
eas login
```
*(If you don't have an Expo account, sign up for free at [Expo.dev](https://expo.dev/signup)).*

---

## Step 4: Build Standalone Downloadable `.apk`
Run:
```bash
eas build -p android --profile preview
```

---

## 🎉 What Happens Next?
1. Expo will build the Android `.apk` file in the cloud (takes about 3–5 minutes).
2. Once complete, Expo will print a direct **Downloadable APK Link** in your terminal!
3. Click the link to download the `.apk` file or share it with your homeopathy friends via WhatsApp/Google Drive!
