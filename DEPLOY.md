# Putting this online (free tier)

The repository is complete and runs locally. To have a **public URL** you can put
on Upwork / Fiverr / LinkedIn, deploy the two services separately. Both have a
free tier and neither needs a credit card for this size.

You do not need to read any code to do this. Just follow the steps in order.

---

## Step 1 — Backend on Render (the API)

1. Go to <https://render.com> and sign up **with GitHub** (one click, no card).
2. **New** → **Web Service**.
3. Choose the repository `MrFox2000/ai-pdf-chat`.
4. Fill the form exactly:

| Field | Value |
|---|---|
| Name | `ai-pdf-chat-api` |
| Language | `Docker` |
| Root Directory | `backend` |
| Branch | `main` |
| Instance Type | `Free` |

5. Open **Environment** and add **one** variable:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | your key, or leave it out to stay in offline mode |
| `ALLOWED_ORIGINS` | `https://ai-pdf-chat.vercel.app` (update after step 2) |

6. **Create Web Service** and wait ~3 minutes.
7. Copy the URL it gives you, something like
   `https://ai-pdf-chat-api.onrender.com`.

Check it works by opening that URL + `/health` in the browser. You should see
`{"status":"ok","offline":true,"documents":0}`.

> Free instances sleep after 15 minutes of inactivity. The first request after
> sleeping takes ~30 seconds. That is normal and does not look broken to a client
> if you warn them.

---

## Step 2 — Frontend on Vercel (the page people see)

1. Go to <https://vercel.com> and sign up **with GitHub**.
2. **Add New** → **Project** → import `ai-pdf-chat`.
3. Before clicking deploy, set:

| Field | Value |
|---|---|
| Framework Preset | `Next.js` |
| Root Directory | `frontend` |
| Environment Variable `NEXT_PUBLIC_API_URL` | the Render URL from step 1 |

4. **Deploy**. It takes about 2 minutes.

You now have a public link like `https://ai-pdf-chat.vercel.app`. Send it to
nobody yet — first test it yourself with the sample PDF.

---

## Step 3 — Close the loop

1. Go back to Render → your service → **Environment** → set
   `ALLOWED_ORIGINS` to your real Vercel URL (no trailing slash).
2. Save; Render redeploys automatically.
3. On GitHub, open the repo → **Settings** → **General** → **Website** field and
   paste the Vercel URL. It then appears at the top of the repository page.
4. In the README, replace the "Quickstart" line with a link to the live demo:

```markdown
**Live demo:** https://ai-pdf-chat.vercel.app
```

---

## What to say when someone asks "is it live?"

> Yes — the demo runs in offline mode so it needs no key: upload any text PDF and
> the retrieval and citations work end to end. With `OPENAI_API_KEY` set, the
> answer text is generated instead of extracted.

That is true, checkable, and it is the honest version of the pitch.

---

## Things that will bite you

| Symptom | Cause | Fix |
|---|---|---|
| Upload fails with CORS error | `ALLOWED_ORIGINS` does not match the Vercel domain exactly | include `https://`, no trailing slash |
| First request hangs 30s | free instance woke from sleep | expected |
| `No extractable text found` | scanned PDF, needs OCR | use a text PDF |
| 413 error | file over 20 MB | raise `MAX_UPLOAD_MB` |
