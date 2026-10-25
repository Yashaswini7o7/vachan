# ===== CELL 1: install (run once) =====
!pip install -q sarvamai gradio

# ===== CELL 2: the whole Vachan app =====
# Before running: click the 🔑 key icon (left bar in Colab) -> Add secret
#   Name: SARVAM_API_KEY   Value: your key   -> turn on "Notebook access"
import json, re, hashlib, datetime
import gradio as gr
from google.colab import userdata
from sarvamai import SarvamAI
from sarvamai.play import save

client = SarvamAI(api_subscription_key=userdata.get("SARVAM_API_KEY"))

SYSTEM = """You extract labour agreement terms from spoken, code-mixed Indian speech (any Indian language).
Return ONLY JSON: {"daily_wage": number|null, "days": number|null, "advance": number|null,
"pay_schedule": "weekly"|"monthly"|"month-end"|null, "missing": [list of unclear terms]}
Never guess. If a term is vague, put null and list it in "missing"."""

LANGS = {
    "Hindi": ("hi-IN", lambda t: f"आपकी रोज़ की मज़दूरी ₹{t['daily_wage']} है, {t['days']} दिन का काम, एडवांस ₹{t['advance'] or 0}, कुल ₹{t['total']}। भुगतान: {t['pay_schedule']}। क्या आप सहमत हैं?"),
    "Bengali": ("bn-IN", lambda t: f"আপনার দৈনিক মজুরি ₹{t['daily_wage']}, {t['days']} দিনের কাজ, অগ্রিম ₹{t['advance'] or 0}, মোট ₹{t['total']}। পেমেন্ট: {t['pay_schedule']}। আপনি কি রাজি?"),
    "Marathi": ("mr-IN", lambda t: f"तुमची रोजची मजुरी ₹{t['daily_wage']}, {t['days']} दिवसांचे काम, आगाऊ ₹{t['advance'] or 0}, एकूण ₹{t['total']}. पैसे: {t['pay_schedule']}. तुम्ही सहमत आहात का?"),
    "Tamil": ("ta-IN", lambda t: f"உங்கள் தினக்கூலி ₹{t['daily_wage']}, {t['days']} நாள் வேலை, முன்பணம் ₹{t['advance'] or 0}, மொத்தம் ₹{t['total']}. சம்பளம்: {t['pay_schedule']}. நீங்கள் ஒப்புக்கொள்கிறீர்களா?"),
}

def extract(text):
    r = client.chat.completions(
        model="sarvam-105b",  # if this errors, try "sarvam-105b-conversations"
        temperature=0.2,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
    )
    out = r.choices[0].message.content
    return json.loads(out[out.find("{"): out.rfind("}") + 1])  # strip any extra text

def run(audio_path, typed_text, lang):
    # 1. Voice -> text (Sarvam Speech to Text)
    if audio_path:
        transcript = client.speech_to_text.transcribe(
            file=open(audio_path, "rb"), model="saaras:v4", mode="codemix").transcript
    else:
        transcript = typed_text or ""
    if not transcript.strip():
        return "Record or type the deal first.", "", "", None, ""

    # 2. Text -> structured terms (Sarvam LLM)
    t = extract(transcript)
    if t.get("missing"):
        return transcript, json.dumps(t, indent=2, ensure_ascii=False), \
            f"⚠ Cannot seal. Ask the employer to state clearly: {', '.join(t['missing'])}", None, ""
    t["total"] = t["daily_wage"] * t["days"]

    # 3. Read back in the worker's language (Sarvam Text to Speech)
    code, tmpl = LANGS[lang]
    readback = tmpl(t)
    audio = client.text_to_speech.convert(text=readback, language_code=code, model="bulbul:v4-flash")
    save(audio, "readback.wav")

    # 4. Tamper-proof receipt
    when = datetime.datetime.now().strftime("%d %b %Y, %H:%M")
    payload = json.dumps({"transcript": transcript, "terms": t, "lang": lang, "time": when}, ensure_ascii=False)
    h = hashlib.sha256(payload.encode()).hexdigest()
    receipt = (f"VACHAN VOICE AGREEMENT · {when}\n"
               f"₹{t['daily_wage']}/day × {t['days']} days = ₹{t['total']}\n"
               f"Advance ₹{t['advance'] or 0} · Balance ₹{t['total'] - (t['advance'] or 0)} · Paid {t['pay_schedule']}\n"
               f"Read back to worker in {lang}\nSHA-256: {h}")
    return transcript, json.dumps(t, indent=2, ensure_ascii=False), readback, "readback.wav", receipt

with gr.Blocks(title="Vachan") as app:
    gr.Markdown("# Vachan\nA spoken labour deal becomes a record both sides hear, confirm and can prove. Built on Sarvam AI.")
    with gr.Row():
        mic = gr.Audio(sources=["microphone", "upload"], type="filepath", label="1 · Employer speaks the deal")
        typed = gr.Textbox(label="…or type it", value="Dekho bhai, roz ka 600 rupaye milega, 20 din ka kaam hai. 2000 advance abhi de raha hoon, baaki har shanivaar ko payment.")
    lang = gr.Dropdown(list(LANGS), value="Bengali", label="Worker's language")
    go = gr.Button("Create voice agreement", variant="primary")
    tr = gr.Textbox(label="Transcript (Sarvam Speech to Text)")
    terms = gr.Code(label="Extracted terms (Sarvam 105B)", language="json")
    rb = gr.Textbox(label="Read-back text / gap warning")
    rb_audio = gr.Audio(label="Read-back audio (Sarvam Text to Speech)")
    receipt = gr.Textbox(label="Voice-sealed receipt", lines=5)
    go.click(run, [mic, typed, lang], [tr, terms, rb, rb_audio, receipt])

app.launch(share=True, debug=True)  # prints a public https://….gradio.live link
