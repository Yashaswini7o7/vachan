# Vachan: voice-sealed labour agreements

90% of India's workers are informal. Their wages and terms are agreed by voice, and on payday the employer says "maine 500 bola tha." Vachan turns a spoken deal into a record both sides hear, confirm, and can prove.

## How it works (built on Sarvam AI)
1. **Employer speaks the deal** in Hinglish or any Indian language → Sarvam Speech to Text (`saaras:v4`, codemix mode)
2. **Terms extracted** (daily wage, days, advance, pay schedule) → Sarvam 105B. Vague deals are blocked until every term is stated clearly.
3. **Read back to the worker** in their own language (Bengali, Tamil, Marathi, Hindi) → Sarvam Text to Speech (`bulbul:v4-flash`)
4. **Voice-sealed receipt** with a SHA-256 hash of the transcript and terms, so the deal can be proved later.

## Live demo
https://xxxx.gradio.live  ← replace with your link

## Run it
1. Open Google Colab and add a secret named `SARVAM_API_KEY` (Notebook access on).
2. Paste CELL 1 and CELL 2 from `vachan_colab.py` into two cells and run them.
3. Open the public `gradio.live` link it prints.

## Next
SMS delivery of receipts, payday voice reminders, IVR for feature phones, e-Shram integration.
