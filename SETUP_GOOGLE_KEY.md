# Setting Up Your Google API Key

This guide walks you through getting a free Google API key so the Ethos Sound Creator can generate audio files using Google's Text-to-Speech service.

The whole process takes about 10 minutes and is free for normal use.

---

## What Does It Cost?

Google gives you a free allowance every month:

| Voice type | Free per month |
|---|---|
| WaveNet voices (e.g. en-US-Wavenet-F) | 1 million characters |
| Neural2 voices (e.g. en-GB-Neural2-A) | 1 million characters |

A typical full Ethos sound pack is around **10,000 characters** — about 1% of the free allowance. You would need to regenerate a pack roughly **100 times in a single month** before incurring any charge.

> Google requires a credit card to activate an account, but **you will not be charged** unless you manually upgrade to a paid plan or exceed the free tier by a large margin. You can also set a budget alert to notify you if spending ever approaches a limit.

---

## Step 1 — Sign In to Google Cloud

1. Open your browser and go to **https://console.cloud.google.com**
2. Sign in with your Google account (Gmail, Google Workspace, etc.)
3. If this is your first time, you will be asked to agree to the Terms of Service — tick the box and click **Agree and Continue**

---

## Step 2 — Create a Project

Google Cloud organises everything into *projects*. You need one to hold your API key.

1. At the top of the page, click the project selector (it usually says **"My First Project"** or shows a project name next to the Google Cloud logo)
2. In the popup, click **New Project**
3. Give it a name — something like `Ethos Sound Creator` works well
4. Leave the organisation set to **No organisation**
5. Click **Create**
6. Wait a few seconds, then make sure your new project is selected in the top bar

---

## Step 3 — Enable the Text-to-Speech API

1. In the left-hand menu, click **APIs & Services** → **Library**  
   *(Or go directly to: https://console.cloud.google.com/apis/library)*
2. In the search box, type **Text-to-Speech**
3. Click **Cloud Text-to-Speech API** (published by Google)
4. Click the blue **Enable** button
5. Wait a moment while it activates

---

## Step 4 — Set Up Billing

Google requires a billing account even for free-tier usage. Your card will **not** be charged during normal use.

1. In the left-hand menu, click **Billing**
2. If prompted, click **Link a billing account** or **Create billing account**
3. Follow the steps to add a payment method
4. Once complete, return to your project

> **Tip:** After setup, go to **Billing → Budgets & Alerts** and create a budget of $1. Google will email you if spending ever exceeds that — giving you complete peace of mind.

---

## Step 5 — Create an API Key

1. In the left-hand menu, click **APIs & Services** → **Credentials**  
   *(Or go to: https://console.cloud.google.com/apis/credentials)*
2. Click **+ Create Credentials** at the top
3. Select **API key**
4. Your new key will appear on screen — it looks something like:  
   `AIzaSyD-9tSrke72I9mpKkXMAg8gQ5_anABcDeF`
5. Copy this key and keep it somewhere safe (like a password manager)

---

## Step 6 — Restrict the Key (Recommended)

Restricting the key means it can only be used for Text-to-Speech, so even if someone else got hold of it they could not use it for anything else.

1. After creating the key, click **Edit API key** (or click the pencil icon next to it in the list)
2. Under **API restrictions**, select **Restrict key**
3. In the dropdown, tick **Cloud Text-to-Speech API**
4. Click **Save**

---

## Step 7 — Paste the Key Into the App

1. Open **Ethos Sound Creator**
2. Go to the **Settings** tab
3. Paste your API key into the **Google API Key** field
4. Click **Test** to confirm it works — you should see a *"Valid"* message
5. Click **Save Settings**

You are now ready to generate audio files.

---

## Troubleshooting

**"API key test failed: 403"**  
The Text-to-Speech API may not be enabled yet, or billing is not linked. Go back to Steps 3 and 4.

**"API key test failed: 400 — API key not valid"**  
Double-check you copied the full key with no extra spaces. Keys start with `AIzaSy`.

**"API key test failed: 403 — API Key restriction"**  
You restricted the key but may have selected the wrong API. Go to Credentials → edit the key → check **Cloud Text-to-Speech API** is ticked under API restrictions.

**The Test button succeeds but Generate gives errors**  
Make sure the output directory exists and you have permission to write to it. Try changing the output directory in Settings to somewhere like your Desktop.

---

## Finding Your Key Again Later

1. Go to **https://console.cloud.google.com/apis/credentials**
2. Your key is listed under **API Keys** — click the copy icon to grab it again

> For security, Google does not show the full key after creation. If you lose it, simply delete the old key and create a new one following Step 5 above.
