# Desi AI Keyboard – realistic AI presenter ad: production pack

**Goal:** 30-second vertical (9:16) ad for Google App Campaigns + Meta Reels, with a realistic AI presenter ("Priya") and a real screen recording of the keyboard.
**Time to finish:** about 1–2 hours in CapCut once the presenter clips are generated.

---

## What's in `assets/`

| File | Use |
|---|---|
| `endcard_5s.mp4` | Final 5 s (25–30 s). Full-frame, already animated. Just place it. |
| `demo_background_10s.mp4` | Animated navy background for the phone demo (10–19 s) and features (19–25 s). |
| `phone_frame.png` | Device frame with a **transparent screen**. Put your screen recording *under* it. Screen area = x 185–895, y 230–1808 (710 × 1578 px) on a 1080 × 1920 canvas. A 1080 × 2400 recording fits at **65.7 %** scale. |
| `logo_sting_2s.webm` | Logo + name pop, transparent background (7–9 s). |
| `feature_pills_4s.webm` | 8 feature chips popping in, transparent background (20–24 s). |
| `captions/01…07.png` | Styled caption stickers (transparent). One per beat; see timeline. |
| `music_placeholder_30s.wav` | Royalty-free placeholder beat. A trending CapCut/Reels track will perform better. |
| `style_frames.png` | Preview of the look. |

> If your CapCut version drops the transparency of `.webm`, re-run `python3 build_pack.py <fonts_dir>` to also get ProRes 4444 `.mov` files (too large for git), or set the overlay's blend mode to **Screen**.

---

## Step 1 – Create Priya (the presenter)

**Image prompt** (Midjourney / Ideogram / Flux / Imagen). Make 10–20 and pick ONE face – reuse it for every clip so she looks the same throughout:

> Photorealistic vertical portrait of a 24-year-old Indian woman, warm brown skin, shoulder-length black hair, small gold earrings, small red bindi, wearing a teal cotton kurti with gold trim, sitting on a sofa in a bright, modern middle-class Indian apartment, holding a smartphone, soft window light, candid friendly expression, shot on iPhone, shallow depth of field, 9:16, no text

## Step 2 – Voiceover (Hindi/Hinglish)

Use **ElevenLabs** (multilingual model, a young female Hindi voice, stability ~40 %, style ~30 %) or the voice built into HeyGen/Veo. Generate each line separately so it is easy to time.

| # | Time | Devanagari (paste into the voice tool) | Roman Hinglish |
|---|---|---|---|
| V1 | 0–3 s | मेरा नया बॉस सिर्फ़ इंग्लिश समझता है… और मेरी इंग्लिश? | Mera naya boss sirf English samajhta hai… aur meri English? |
| V2 | 3–7 s | छुट्टी माँगनी थी… दस मिनट से एक लाइन लिख रही हूँ! | Chhutti maangni thi… das minute se ek line likh rahi hoon! |
| V3 | 7–10 s | फिर मैंने देसी AI कीबोर्ड ट्राई किया। | Phir maine Desi AI Keyboard try kiya. |
| V4 | 10–16 s | हिंदी में लिखो… एक टैप… और इंग्लिश में चला गया! | Hindi mein likho… ek tap… aur English mein chala gaya! |
| V5 | 16–19 s | और बॉस ने तुरंत हाँ बोल दिया! | Aur boss ne turant haan bol diya! |
| V6 | 19–25 s | वॉइस टाइपिंग, हैंडराइटिंग, स्टाइलिश फ़ॉन्ट्स, स्टिकर्स… सब एक कीबोर्ड में। | Voice typing, handwriting, stylish fonts, stickers… sab ek keyboard mein. |
| V7 | 25–30 s | देसी AI कीबोर्ड — प्राउडली मेड फ़ॉर इंडिया। अभी फ्री डाउनलोड करो! | Desi AI Keyboard — proudly made for India. Abhi free download karo! |

## Step 3 – Generate the presenter clips

**Option A – HeyGen / Hedra (talking photo, easiest):** upload Priya's image → create a photo avatar → paste each line (V1, V2, V3, V5, V7) → export 9:16. Ask for a green/transparent background only if you want to put her over the navy background; otherwise keep the apartment background.

**Option B – Google Veo / Kling (more cinematic, acting + lip-sync):** use Priya's image as the reference/first frame. One clip per prompt (≤ 8 s). Always add: *"vertical 9:16, photorealistic, natural handheld phone-camera look, no subtitles, no text on screen."*

| Clip | Prompt (append the line in quotes) |
|---|---|
| P1 – Hook | Medium close-up of the woman on the sofa looking at her phone, then up at the camera with an awkward, embarrassed smile; she speaks in Hindi: "Mera naya boss sirf English samajhta hai… aur meri English?" |
| P2 – Struggle | Close-up, she types slowly on her phone, frowns, deletes, sighs and rubs her forehead, then looks at camera and says in Hindi: "Chhutti maangni thi… das minute se ek line likh rahi hoon!" |
| P3 – Idea | She raises her eyebrows with an idea, smiles, turns the phone screen towards the camera and says in Hindi: "Phir maine Desi AI Keyboard try kiya." |
| P4 – Joy | Her phone buzzes, she reads it, gasps, and celebrates with a happy fist pump, saying in Hindi: "Aur boss ne turant haan bol diya!" |
| P5 – CTA | Bright smile to camera, points down towards the bottom of the frame, then waves; says in Hindi: "Abhi free download karo!" |

> Don't let the AI tool generate the keyboard or app UI – use the real screen recording (Step 4). Faked UI can get the ad rejected for being misleading, and the presenter must not claim to be a real customer.

## Step 4 – Record the real demo (screen recording)

Clean phone, Do Not Disturb on, full battery, 1080 × 2400 recording:
1. Open WhatsApp with a contact named **"Boss"** whose last message is *"Are you coming to office tomorrow?"*
2. Tap the message box → Desi AI Keyboard opens.
3. Type **कल मुझे छुट्टी चाहिए, घर पे function है** (or use Voice Input).
4. Tap **AI Translation** → it becomes *"I need leave tomorrow, there's a function at home."*
5. Send. From a second phone, reply *"Sure, no problem. Approved!"*
6. Also record 2–3 s each of: Voice Input, Handwriting, Fonts/Text Effects, Stickers, GIF, Themes.

## Step 5 – Edit in CapCut (1080 × 1920, 30 fps)

| Time | Main video (V1) | Overlays | Audio |
|---|---|---|---|
| 0–3 s | **P1** hook (punch-in zoom 100→110 %) | `captions/01_hook.png` lower third | V1 |
| 3–7 s | **P2** struggle | `02_struggle.png` (pop-in at 5 s) | V2 |
| 7–10 s | **P3** idea | `logo_sting_2s.webm` top half at 7.5 s, `03_reveal.png` | V3 |
| 10–16 s | `demo_background_10s.mp4` + screen recording (65.7 %, under) + `phone_frame.png` (over) | `04_type_hindi.png` → `05_send_english.png` at the tap; P-in-P circle of Priya bottom-right (optional) | V4 + tap "pop" SFX |
| 16–19 s | **P4** joy | `06_approved.png` | V5 + "ding" SFX |
| 19–25 s | `demo_background_10s.mp4` + quick 0.7 s feature recordings in the phone frame | `feature_pills_4s.webm` at 20 s, `07_features.png` | V6 |
| 25–30 s | `endcard_5s.mp4` | optional: **P5** as a small circle bottom-left for the wave | V7 |

**Polish checklist**
- Cut on every beat (~every 1–2 s); add a 4-frame zoom/whip transition between scenes.
- Music at about −18 dB under the voice, full volume on the end card.
- Turn on CapCut auto-captions only if you remove the PNG captions (don't double them).
- Keep everything important inside the safe area: 120 px from the top, 320 px from the bottom (Reels UI covers it).
- Export: 1080 × 1920, 30 fps, H.264, high bitrate. Also export 1:1 (1080 × 1080) and 16:9 (1920 × 1080) for YouTube by re-framing.

## Step 6 – Variations to test (same assets)
- **Hook B:** "US client se chat karna hai aur dimaag blank?" (foreign-client angle)
- **Hook C:** "Insta bio itna stylish kaise?" (fonts angle, younger audience)
- **Persona B:** Ramesh ji, 45, shop owner, voice-typing to a Bengaluru supplier (tier-2/3 audience)

Run 3–5 versions, keep the one with the lowest **cost per keyboard enabled**, and make new hooks for it every 2–3 weeks.

---
Rebuild the assets: `python3 build_pack.py <fonts_dir>` (needs Poppins SemiBold/ExtraBold as `pop-sb.ttf`/`pop-xb.ttf` and Noto Sans Devanagari as `deva.ttf`).
