#!/usr/bin/env python3
import os, time, json, re, requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
from telegram.ext import Updater, CallbackQueryHandler, Dispatcher
from hashlib import md5
LINK_MAP = {}

# 📌 CONFIGURAZIONE
TOKEN = "8043365763:AAHHhiiC-KdvvzGIU7P4nikEJhvuUVG8aKk"
CHAT_ID = "385655299"
GROUP_ID = -4976140202
BOT = Bot(TOKEN)


DATABASE = "seen.json"
DASH_INTERVAL = 6 * 3600
last_dash = 0

SEARCHES = [
    {"enabled": False, "label": "iPhone 11", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+11&ic=40%2C50&ps=30&pe=100", "min": 30, "max": 100},
    {"enabled": True, "label": "iPhone 11 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+11+pro&ic=40%2C50&ps=30&pe=150", "min": 30, "max": 150},
    {"enabled": True, "label": "iPhone 11 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+11+pro+max&ic=40%2C50&ps=30&pe=180", "min": 30, "max": 180},
    {"enabled": True, "label": "iPhone 12", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+12&ic=40%2C50&ps=30&pe=200", "min": 30, "max": 200},
    {"enabled": True, "label": "iPhone 12 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+12+pro&ic=40%2C50&ps=30&pe=220", "min": 30, "max": 220},
    {"enabled": True, "label": "iPhone 12 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+12+pro+max&ic=40%2C50&ps=30&pe=250", "min": 30, "max": 250},
    {"enabled": True, "label": "iPhone 13", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+13&ic=40%2C50&ps=30&pe=250", "min": 30, "max": 250},
    {"enabled": True, "label": "iPhone 13 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+13+pro&ic=40%2C50&ps=30&pe=300", "min": 30, "max": 300},
    {"enabled": True, "label": "iPhone 13 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+13+pro+max&ic=40%2C50&ps=30&pe=330", "min": 30, "max": 330},
    {"enabled": True, "label": "iPhone 14", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+14&ic=40%2C50&ps=30&pe=350", "min": 30, "max": 350},
    {"enabled": True, "label": "iPhone 14 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+14+pro&ic=40%2C50&ps=30&pe=370", "min": 30, "max": 370},
    {"enabled": True, "label": "iPhone 14 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+14+pro+max&ic=40%2C50&ps=30&pe=400", "min": 30, "max": 400},
    {"enabled": True, "label": "iPhone 15", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+15&ic=40%2C50&ps=30&pe=400", "min": 30, "max": 400},
    {"enabled": True, "label": "iPhone 15 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+15+pro&ic=40%2C50&ps=30&pe=420", "min": 30, "max": 420},
    {"enabled": True, "label": "iPhone 15 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+15+pro+max&ic=40%2C50&ps=30&pe=450", "min": 30, "max": 450},
    {"enabled": True, "label": "iPhone 16", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+16&ic=40%2C50&ps=30&pe=400", "min": 30, "max": 400},
    {"enabled": True, "label": "iPhone 16 Pro", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+16+pro&ic=40%2C50&ps=30&pe=420", "min": 30, "max": 420},
    {"enabled": True, "label": "iPhone 16 Pro Max", "url": "https://www.subito.it/annunci-italia/vendita/telefonia/?q=iphone+16+pro+max&ic=40%2C50&ps=30&pe=450", "min": 30, "max": 450}
]

KEYWORDS = {
    "64 GB": [r"\b64\s?gb\b", r"\b64\s?g\b", r"\b64\s?gigabyte\b"],
    "128 GB": [r"\b128\s?gb\b", r"\b128\s?g\b", r"\b128\s?gigabyte\b"],
    "256 GB": [r"\b256\s?gb\b", r"\b256\s?g\b", r"\b256\s?gigabyte\b"],
    "512 GB": [r"\b512\s?gb\b", r"\b512\s?g\b", r"\b512\s?gigabyte\b"],
    "1 TB": [r"\b1\s?tb\b", r"\b1000\s?gb\b"],
    "Display rotto": [r"display.*rotto", r"schermo.*rotto", r"lcd.*rotto", r"vetro.*rotto"],
    "Display crepato": [r"(display|schermo|vetro).*crepat", r"crepa.*(schermo|display|vetro)"],
    "Display sostituito": [r"display.*sostituito", r"schermo.*sostituito", r"lcd.*nuovo"],
    "Display funzionante": [r"display.*funzionante", r"schermo.*funziona"],
    "Batteria da cambiare": [r"batteria.*(cambiare|sostituire)", r"autonomia.*scarsa"],
    "Batteria nuova": [r"batteria.*nuova"],
    "Batteria originale": [r"batteria.*originale"],
    "Batteria 80%": [r"batteria.*80\s?%"],
    "Batteria 85%": [r"batteria.*85\s?%"],
    "Batteria 90%": [r"batteria.*90\s?%"],
    "Graffi": [r"graffiato", r"graffi", r"scocca.*rovinata", r"cover.*rigata"],
    "Ammaccature": [r"ammaccatura", r"ammaccato"],
    "Vetro posteriore rotto": [r"vetro posteriore.*rotto"],
    "Vetro scheggiato": [r"vetro.*scheggiat", r"scheggiatura"],
    "Laterale graffiato": [r"laterale.*(rigato|graffiato)", r"lato.*(sinistro|destro).*graffi"],
    "Face ID non funzionante": [r"face.?id.*(non funziona|rotto|assente)", r"sblocco facciale.*(non funziona|non attivo)"],
    "Tasto power rotto": [r"tasto.*power.*rotto"],
    "Tasto volume rotto": [r"tasto.*volume.*rotto"],
    "Tasto home non funziona": [r"tasto.*home.*(non funziona|rotto)"],
    "Audio non funzionante": [r"audio.*(non funziona|assente)"],
    "Microfono rotto": [r"microfono.*(non funziona|rotto)"],
    "Speaker da cambiare": [r"speaker.*(rotto|cambiare)"],
    "Fotocamera rotta": [r"fotocamera.*(non funziona|rotta)"],
    "Sim non rilevata": [r"sim.*(non rilevata|non legge)"],
    "Touch non risponde": [r"touch.*(non risponde|rotto)"],
    "Danneggiato": [r"\bdanneggiato\b"],
    "Non funzionante": [r"non\sfunzionante"],
    "Da riparare": [r"\bda\s+riparare\b"],
    "Bloccato": [r"\bbloccato\b"],
    "Non si accende": [r"non si accende"],
    "Riparabile": [r"\briparabile\b"],
    "Caduto": [r"cadut[ao]", r"caduta.*accidentale"],
    "Crepa": [r"crepa", r"crepatur", r"crepato", r"crepata"],
    "Cornice rovinata": [r"cornice.*(rovinata|ammaccata)"],
    "Schermo cambiato": [r"schermo.*(cambiato|nuovo)", r"display.*rimpiazzato"],
    "Schermo originale": [r"display.*originale", r"lcd.*originale"],
    "Vetro incrinato": [r"vetro.*(incrinato|fessurato)", r"linea.*vetro"],
    "Segni d'usura": [r"segni.*usura", r"usurato", r"consumato"],
    "Cover rotta": [r"cover.*(rotta|crepata|spaccata)"],
    "Tasto rotto": [r"tasto.*(non funziona|rotto|bloccato)"],
    "Problema ricarica": [r"ricarica.*(non funziona|problema|difetto)", r"porta.*lightning.*(difettosa|rotta)"],
    "Face ID ok": [r"face.?id.*(funziona|ok|attivo)"],
    "Face ID assente": [r"face.?id.*(assente|disattivato)"],
    "Face ID presente": [r"face.?id.*(presente|attivo)"],
    "Tasto power ok": [r"tasto.*power.*(funziona|ok)"],
    "Speaker funzionante": [r"speaker.*ok", r"audio.*pulito"],
    "Audio perfetto": [r"audio.*(perfetto|pulito|forte)"],
    "Touch perfetto": [r"touch.*(funziona|reattivo|ok)"],
    "Camera ok": [r"fotocamera.*(funziona|ok|chiara)"],
    "Tasto silenzioso rotto": [r"tasto.*silenzioso.*(rotto|non funziona)"],
    "Difetti estetici": [r"difetti.*estetici", r"piccoli.*segni", r"imperfezioni"],
    "Ripristinabile": [r"ripristinabile", r"può.*riparare", r"facile.*riparare"],
    "Problemi software": [r"problema.*software", r"sistema.*bloccato"],
    "Schermo nero": [r"schermo.*nero", r"display.*non si vede"],
    "Face ID danneggiato": [r"face.?id.*(danneggiato|difettoso|non rileva|saltuari)"],
    "Face ID assente": [r"face.?id.*(assente|rimosso|mancante)"],
    "True Tone assente": [r"true tone.*(non attivo|disattivo|assente)"],
    "Face ID presente": [r"face.?id.*(presente|funzionante|attivo)"],
    "Autenticazione fallita": [r"sblocco.*non riuscito", r"face.?id.*fallisce"],
    "Vetro rovinato": [r"vetro.*rovinato", r"vetro.*rigato"],
    "Ghost touch": [r"ghost.*touch", r"schermo.*impazzisce", r"tocchi.*fantasma"],
    "Frame danneggiato": [r"(frame|struttura|bordo).*danneggiat", r"scocca.*piegata"],
    "Display originale": [r"display.*originale", r"lcd.*originale", r"schermo.*apple"],
    "Display compatibile": [r"display.*compatibile", r"lcd.*aftermarket"],
    "Display non originale": [r"display.*non.*originale", r"schermo.*non.*apple"],
    "Touch ID assente": [r"touch.?id.*(assente|rimosso|non presente)"],
    "Touch ID ok": [r"touch.?id.*(funziona|ok|presente)"],
    "Problemi con Wi-Fi": [r"wifi.*(non funziona|problema|instabile)"],
    "Bluetooth rotto": [r"bluetooth.*(non funziona|rotto|non rileva)"],
    "NFC non funzionante": [r"nfc.*(non funziona|non attivo)"],
    "FaceTime rotto": [r"facetime.*(non funziona|difettoso)"],
    "iMessage non attivo": [r"imessage.*(non funziona|non attivo)"],
    "iCloud bloccato": [r"icloud.*(bloccato|account|non rimuovibile)"],
    "iCloud libero": [r"icloud.*(libero|pulito|senza account)"],
    "Batteria gonfia": [r"batteria.*(gonfia|rigonfia|deformata)"],
    "Batteria usurata": [r"batteria.*(usurata|vecchia|stanca)"],
    "Problema tasto mute": [r"tasto.*(silenzioso|mute).*(non funziona|rotto)"],
    "Speaker gracchia": [r"speaker.*(gracchia|distorto|basso volume)"],
    "Porta lightning rotta": [r"(porta|connettore).*lightning.*(non funziona|rotto|ossidato)"],
    "Problema caricatore": [r"non si carica", r"caricatore.*non va"],
    "Danno da liquido": [r"danno.*liquido", r"ossidazione", r"acqua.*dentro"],
    "Danno da calore": [r"surriscald", r"scalda.*molto", r"telefono.*caldo"],
    "Riparazione non riuscita": [r"riparazione.*non.*riuscita", r"tentato.*fix"],
    "Touch sfarfalla": [r"touch.*(sfarfallio|instabile|impazzito)"],
    "Schermo sbiadito": [r"schermo.*(sbiadito|colori strani|pallido)"],
    "Schermo giallo": [r"schermo.*(giallo|tinta calda|alterato)"],
    "Schermo lampeggia": [r"schermo.*(lampeggia|flicker|intermittente)"],
    "Modello estero": [r"modello.*(giappone|usa|hk|import)", r"iphone.*(japan|hk|china)"],
    "Versione demo": [r"versione.*demo", r"iphone.*demo", r"unità.*espositiva"],
    "IMEI non leggibile": [r"imei.*(non visibile|non leggibile|cancellato)"],
    "IMEI ok": [r"imei.*(ok|verificato|pulito)"],
    "Blocco operatore": [r"operatore.*bloccato", r"sim.*lock"],
    "Firmware bloccato": [r"firmware.*bloccato", r"versione.*sblocco"],
    "Boot loop": [r"boot.*loop", r"riavvio.*continuo", r"continua.*riavviarsi"],
    "iOS non aggiornabile": [r"ios.*non aggiornabile", r"aggiornamento.*non riuscito"],
    "Problema backup": [r"backup.*(non riuscito|impossibile)"],
    "Errore ripristino": [r"errore.*ripristino", r"problema.*reset"],
    "Segnale assente": [r"nessun.*segnale", r"antenna.*non funziona", r"campo.*zero"],
    "Problema generico": [r"non va", r"non funziona", r"difettoso", r"rotto", r"guasto", r"problema", r"non operativo", r"non parte", r"difetto"],
    "Prezzo trattabile": [r"prezzo.*trattabile", r"trattabile", r"trattabili", r"poco trattabile"],
    "Segni di normale usura": [r"normale.*usura", r"segni.*normale.*utilizzo", r"segni.*di.*uso", r"usura.*normale"],
    "Face ID funzionante": [
    r"face.?id.*(funziona|ok|attivo|presente|va)",
    r"sblocco facciale.*(funziona|ok|presente|attivo|va)"
],
"Face ID non funzionante": [
    r"face.?id.*(non funziona|non va|rotto|assente|disattivo|difettoso|non attivo|guasto|non rileva|non parte)",
    r"sblocco facciale.*(non funziona|non va|difettoso|assente|rotto|non rileva|disattivato|problema|guasto)"
],
"Face ID assente": [
    r"face.?id.*(assente|mancante|rimosso|non c.?è)",
    r"sblocco facciale.*(assente|non presente|rimosso|mancante)"
],
"Face ID danneggiato": [
    r"face.?id.*(danneggiato|saltuari|non rileva|non stabile|malfunzionante)",
    r"sblocco facciale.*(danneggiato|instabile|problema|malfunzionante)"
],
"Face ID presente": [
    r"face.?id.*(presente|installato|abilitato)",
    r"sblocco facciale.*(presente|attivo)"
],
"Errore Face ID": [
    r"face.?id.*errore",
    r"errore.*sblocco facciale"
],
"Autenticazione fallita": [
    r"autenticazione.*(fallita|errore)",
    r"sblocco.*(fallito|non riuscito)",
    r"face.?id.*(non disponibile|non rilevato)"
],

}

if os.path.isfile(DATABASE):
    seen = set(json.load(open(DATABASE)))
else:
    seen = set()
  
def load_json(file):
    if os.path.isfile(file):
        return set(json.load(open(file)))
    return set()

def save_json(file, data):
    json.dump(list(data), open(file, "w"))

saved = load_json("saved.json")
discarded = load_json("discarded.json")

def save_seen():
    json.dump(list(seen), open(DATABASE, "w"))
from datetime import timedelta

def parse_date(date_str):
    date_str = date_str.strip().lower()
    now = datetime.now()

    if "oggi" in date_str or "ora" in date_str:
        return now
    if "ieri" in date_str:
        return now - timedelta(days=1)

    # Match tipo "10 feb"
    match = re.search(r"(\d{1,2})\s+(\w+)", date_str)
    if match:
        day, month_str = match.groups()
        month_str = month_str[:3]  # riduci a 3 lettere per sicurezza
        month_map = {
            "gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6,
            "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12
        }
        month = month_map.get(month_str)
        if month:
            parsed_date = datetime(now.year, month, int(day))
            # Se la data è nel futuro (es. 30 dic oggi che è luglio), allora è dell'anno scorso
            if parsed_date > now:
                parsed_date = parsed_date.replace(year=now.year - 1)
            return parsed_date
    return None

def extract_title_model(soup):
    title_tag = soup.find("h1")
    if not title_tag:
        return None
    title = title_tag.text.lower()
    match = re.search(r"iphone\s+(\d{2})", title)
    if not match:
        return None
    parts = ["iPhone", match.group(1)]
    if "pro" in title:
        parts.append("Pro")
    if "max" in title:
        parts.append("Max")
    elif "plus" in title:
        parts.append("Plus")
    return " ".join(parts)

def extract(link):
    r = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    s = BeautifulSoup(r.text, "html.parser")
    venduto = bool(s.find("span", class_=re.compile("item-sold-badge")))
    price = int(re.search(r"(\d+)\s*€", s.find("p", class_=re.compile("index-module_price")).text).group(1))
    feature_tags = s.find_all("span", class_=re.compile("feature-list_value"))
    raw_cond = next((f.text.strip().lower() for f in feature_tags if "cellulari" not in f.text.lower()), "")
    if any(k in raw_cond for k in ["dannegg", "guasto", "difettoso", "non funzion", "rotto"]):
        cond = "Danneggiato"
    elif any(k in raw_cond for k in ["buono", "ottimo", "usato", "perfetto", "ben conservato", "funzionante"]):
        cond = "Buono"
    else:
        cond = "N/A"
    city = s.find("p", class_=re.compile("AdInfo_locationText")).text.strip()
    date = s.find("span", class_=re.compile("insertion-date")).text.strip()
    parsed = parse_date(date)
    if parsed and (datetime.now() - parsed).days > 2:
        raise Exception("Annuncio troppo vecchio")
    likes_tag = s.find("span", class_=re.compile("Heart_counter-wrapper"))
    likes = likes_tag.text.strip() if likes_tag else "0"
    desc = s.find("p", class_=re.compile("AdDescription_description")).text
    details = []
    for label, patterns in KEYWORDS.items():
        for pattern in patterns:
            match = re.search(pattern, desc, re.IGNORECASE)
            if match:
                if label == "Problema generico":
                    snippet = match.group(0).strip()
                    details.append(f"{label} ({snippet})")
                else:
                    details.append(label)
                break

    imgs = [img["src"] for img in s.select("img.Carousel_image__dcaDx") if img.get("src")][:5]
    label = extract_title_model(s)
    return price, cond, city, date, likes, details, imgs, label or "iPhone", venduto

def send_announcement(data, link):
    price, cond, city, date, likes, details, imgs, label, venduto = data
    if not imgs:
        print("🚫 Nessuna immagine trovata per", link)
        return

    text = (
        f"<b>📌 {label}</b>\n"
        f"💶 <b>{price} €</b>\n"
        f"📆 <i>{date}</i>\n"
        + ("🔒 <b>VENDUTO</b>\n" if venduto else "")
        + f"⚙️ Condizione: {cond}\n"
        + f"📍 Città: {city}\n"
        + f"💥 Like: {likes}\n"
        + "━━━━━━━━━━━━━━\n"
        + "<b>📎 Dettagli tecnici:</b>\n"
        + ("\n".join(f"• {d}" for d in details) if details else "• Nessun dettaglio rilevante") + "\n"
        + f"🌐 <a href='{link}'>Apri in Subito</a>"
    )

    media = [InputMediaPhoto(imgs[0], caption=text, parse_mode="HTML")] + [InputMediaPhoto(u) for u in imgs[1:]]
    try:
        key = md5(link.encode()).hexdigest()
        media_msgs = BOT.send_media_group(CHAT_ID, media)
        if media_msgs:
            media_msg_ids = [m.message_id for m in media_msgs]
            LINK_MAP[key] = (link, media_msg_ids)


            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            msg_testo = "🔘 Vuoi contattare subito?"
            keyboard = [[
                InlineKeyboardButton("✅ Yes", callback_data=f"save|{key}"),
                InlineKeyboardButton("❌ No", callback_data=f"discard|{key}")
            ]]
            BOT.send_message(CHAT_ID, msg_testo, reply_markup=InlineKeyboardMarkup(keyboard))

        print("📲 Pulsanti inviati!")
        status = "[VENDUTO]" if venduto else ""
        print(f"📤 {label:<20} | 💶 {price} € | 📍 {city} | 📆 {date} {status}")
        time.sleep(2)
    except TelegramError as e:
        print("📸 Errore invio immagini:", e)
      
def clean_sold_announcements(all_ann):
    to_remove = []
    for a in all_ann:
        if a["link"] in saved:
            if "venduto" in a.get("label", "").lower() or a["link"] in discarded:
                to_remove.append(a["link"])
    for l in to_remove:
        saved.discard(l)

def build_dash(all_ann):
    txt = "<b>📊 DASHBOARD aggiornata</b>\n\n"

    # Sezione 1: 💾 Salvati
    saved_ann = [a for a in all_ann if a["link"] in saved]
    if saved_ann:
        txt += "💾 <b>ANNUNCI SALVATI</b>\n"
        for a in saved_ann:
            txt += f"• {a['label']} — {a['price']} € — {a['city']} — <a href='{a['link']}'>link</a>\n"
        txt += "\n"

    # Sezione 2: 🔥 Annunci Caldi (20% migliori per prezzo + like)
    filtered = [a for a in all_ann if a["link"] not in discarded and a["link"] not in saved]
    if len(filtered) >= 5:
        sorted_prices = sorted(a["price"] for a in filtered)
        price_threshold = sorted_prices[max(1, len(sorted_prices) // 5)]

        hot = [a for a in filtered if a["price"] <= price_threshold]
        # Simula "calore" con prezzo basso e like alto (likes come stringa, li forziamo a int)
        hot_sorted = sorted(hot, key=lambda x: (x["price"], -int(x.get("likes", "0"))))
        if hot_sorted:
            txt += "🔥 <b>ANNUNCI CALDI</b>\n"
            for a in hot_sorted[:5]:
                txt += f"• {a['label']} — {a['price']} € — {a['city']} — <a href='{a['link']}'>link</a>\n"
            txt += "\n"

    return txt

last_dash_msg_id = None  # aggiungi questa riga tra le variabili globali in alto

def send_dash(all_ann):
    global last_dash, last_dash_msg_id

    clean_sold_announcements(all_ann)

    sections = {"saved": [], "hot": [], "unhandled": []}

    for a in all_ann:
        if a["link"] in saved:
            sections["saved"].append(a)
        elif a["link"] in discarded:
            continue
        else:
            sections["unhandled"].append(a)

    filtered = sections["unhandled"]
    if len(filtered) >= 5:
        sorted_prices = sorted(a["price"] for a in filtered)
        threshold = sorted_prices[max(1, len(sorted_prices) // 5)]
        hot = [a for a in filtered if a["price"] <= threshold]
        hot_sorted = sorted(hot, key=lambda x: (x["price"], -int(x.get("likes", "0"))))
        sections["hot"] = hot_sorted[:5]

    # Costruzione messaggio compatto
    txt = "<b>📊 DASHBOARD aggiornata</b>\n\n"

    txt += section_block("💾 <b>ANNUNCI SALVATI</b>", "saved", sections)
    txt += section_block("🔥 <b>ANNUNCI CALDI</b>", "hot", sections)


    # Elimina messaggio precedente
    if last_dash_msg_id:
        try:
            BOT.delete_message(GROUP_ID, last_dash_msg_id)
        except:
            pass

    msg = BOT.send_message(GROUP_ID, txt, parse_mode="HTML", disable_web_page_preview=True)
    last_dash_msg_id = msg.message_id
    last_dash = time.time()
    # Invia anche i caldi nella terza chat se non già presenti

def section_block(title, key, sections):
    righe = ""
    for a in sections[key]:
        label = a['label']
        prezzo = a['price']
        citta = a['city']
        link = a['link']
        url = link
        righe += f"• {label} — {prezzo} € — {citta} — <a href='{url}'>🔗</a> | <a href='https://t.me/{BOT.username}?start=discard_{md5(link.encode()).hexdigest()}'>🗑️</a>\n"
    return f"{title}\n{righe}\n" if righe else ""

def button_handler(update, context):
    global all_ann
    query = update.callback_query
    if not query:
        return
      
    action, key = query.data.split("|")
    link, media_msg_ids = LINK_MAP.get(key, (None, []))
    if not link:
        query.answer("❌ Errore interno")
        return
      
    if action == "discard_saved":
       link, media_msg_ids = LINK_MAP.get(key, (None, []))
       if not link:
           query.answer("❌ Errore interno")
           return
       discarded.add(link)
       saved.discard(link)
       save_json("discarded.json", discarded)
       save_json("saved.json", saved)
       query.answer("🗑️ Scartato dai salvati!")
       try:
           BOT.delete_message(query.message.chat_id, query.message.message_id)
       except:
           pass
       send_dash(all_ann)
       return

    if action == "save":
        saved.add(link)
        save_json("saved.json", saved)
        query.answer("🔖 Salvato!")
        try:
            BOT.delete_message(query.message.chat_id, query.message.message_id)
            for msg_id in media_msg_ids:
                try:
                    BOT.delete_message(query.message.chat_id, msg_id)
                except:
                    pass

            price, cond, city, date, likes, details, imgs, label, venduto = extract(link)
            if not any(a["link"] == link for a in all_ann):
                all_ann.append({"label": label, "price": price, "city": city, "link": link, "likes": likes})
            send_dash(all_ann)

        except Exception as e:
            print("⚠️ Errore salvataggio o invio nella terza chat:", e)

    elif action == "discard":
        discarded.add(link)
        saved.discard(link)  # ✅ se era salvato lo togliamo
        save_json("discarded.json", discarded)
        save_json("saved.json", saved)
        query.answer("🚫 Scartato!")

        try:
            BOT.delete_message(query.message.chat_id, query.message.message_id)
            for msg_id in media_msg_ids:
                try:
                    BOT.delete_message(query.message.chat_id, msg_id)
                except:
                    pass
            send_dash(all_ann)  # aggiorna la dashboard
        except Exception as e:
            print("❌ Errore eliminazione:", e)

def dash_filter(update, context):
    cmd = update.message.text.lower().strip()
    section = None
    if "/salvati" in cmd:
        section = "saved"
    elif "/caldi" in cmd:
        section = "hot"
    elif "/valutare" in cmd:
        section = "unhandled"
    else:
        BOT.send_message(update.effective_chat.id, "❓ Comando non valido.")
        return

    filtered_ann = []
    if section == "saved":
        filtered_ann = [a for a in all_ann if a["link"] in saved]
    elif section == "unhandled":
        filtered_ann = [a for a in all_ann if a["link"] not in saved and a["link"] not in discarded]
    elif section == "hot":
        temp = [a for a in all_ann if a["link"] not in saved and a["link"] not in discarded]
        if len(temp) >= 5:
            sorted_prices = sorted(a["price"] for a in temp)
            threshold = sorted_prices[max(1, len(sorted_prices) // 5)]
            filtered_ann = [a for a in temp if a["price"] <= threshold]

    if not filtered_ann:
        BOT.send_message(update.effective_chat.id, "⚠️ Nessun annuncio trovato.")
        return

    txt = f"<b>📂 {section.upper()} ({len(filtered_ann)})</b>\n\n"
    for a in filtered_ann[:10]:
        txt += f"• {a['label']} — {a['price']} € — {a['city']} — <a href='{a['link']}'>🌐</a>\n"

    BOT.send_message(update.effective_chat.id, txt, parse_mode="HTML")

all_ann = []

def clear_dashboard(update, context):
    count = 0
    for msg_id in last_dash_msg_ids:
        try:
            BOT.delete_message(GROUP_ID, msg_id)
            count += 1
        except:
            pass
    last_dash_msg_ids.clear()
    BOT.send_message(update.effective_chat.id, f"🧹 Dashboard pulita! ({count} messaggi eliminati)")
#/salvati → mostra i preferiti
#/caldi → mostra i più caldi
#/valutare → da valutare
#/recover → recupera gli scartati
#/reset → svuota tutta la memoria
#/cleandash → cancella la dashboard manualmente

def main():
    global last_dash
    BOT.send_message(GROUP_ID, "✅ *ReBiz Bot attivo e monitoraggio avviato!* 📡", parse_mode="Markdown")
    print("🚀 Bot attivo e in ascolto...")
    from telegram.ext import MessageHandler, Filters

    from threading import Thread

    updater = Updater(TOKEN, use_context=True)
    dispatcher: Dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r"^/start discard_"), handle_start))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    from telegram.ext import CommandHandler
    dispatcher.add_handler(CommandHandler("reset", reset_data))
    dispatcher.add_handler(CommandHandler("recover", recover_discarded))
    dispatcher.add_handler(CommandHandler("salvati", dash_filter))
    dispatcher.add_handler(CommandHandler("caldi", dash_filter))
    dispatcher.add_handler(CommandHandler("valutare", dash_filter))
    dispatcher.add_handler(CommandHandler("cleandash", clear_dashboard))

    Thread(target=updater.start_polling, daemon=True).start()

    while True:
        for s in SEARCHES:
            if not s.get("enabled", True):
                continue
            found = 0
            print(f"\n📦 {datetime.now().strftime('%d/%m %H:%M')} • Ricerca: {s['label']}")

            try:
                resp = requests.get(s["url"], headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
            except Exception as e:
                print(f"🌐 Errore nella richiesta: {e}")
                continue

            for c in soup.find_all("div", class_=re.compile("item-card")):
                href = c.find("a", href=True)["href"]
                link = href if href.startswith("http") else "https://www.subito.it" + href
                link = link.rstrip("/")  # rimuove eventuale slash finale

                if link in seen:
                    continue
                if link in discarded:
                    continue

                try:
                    data = extract(link)
                except Exception as e:
                    print("❌ Errore parsing:", e)
                    continue

                price, cond, city, date, likes, details, imgs, model, venduto = data
                if s["label"].lower() != model.lower():
                    continue
                parsed = parse_date(date)
                if parsed and (datetime.now() - parsed).days > 2:
                    continue
                if not (s["min"] <= price <= s["max"]):
                    continue

                seen.add(link)
                found += 1
                if not any(a["link"] == link for a in all_ann):
                    all_ann.append({"label": model, "price": price, "city": city, "link": link, "likes": likes})

                send_announcement(data, link)
                time.sleep(2)

            if found:
                print(f"✅ Trovati: {found} annunci validi")
            else:
                print("🛑 Nessun annuncio valido")
            print("────────────────────────────────────────────")

        save_seen()
        if time.time() - last_dash > DASH_INTERVAL:
            send_dash(all_ann)
        time.sleep(60)
      
def reset_data(update, context):
    global saved, discarded, seen, all_ann
    saved = set()
    discarded = set()
    seen = set()
    all_ann = []
    save_json("saved.json", saved)
    save_json("discarded.json", discarded)
    save_json(DATABASE, seen)
    BOT.send_message(update.effective_chat.id, "♻️ Memoria svuotata!")

def recover_discarded(update, context):
    lista = [a for a in reversed(all_ann) if a["link"] in discarded]
    if not lista:
        BOT.send_message(update.effective_chat.id, "✅ Nessun annuncio scartato.")
        return

    text = "<b>♻️ Annunci scartati</b>\n\n"
    for a in lista[:10]:
        key = md5(a["link"].encode()).hexdigest()
        text += f"• {a['label']} — {a['price']} € — {a['city']} — <a href='https://t.me/{BOT.username}?start=discard_{key}'>♻️ Recupera</a>\n"

    BOT.send_message(update.effective_chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

def handle_start(update, context):
    text = update.message.text
    if text.startswith("/start discard_"):
        key = text.split("discard_")[1]
        for a in all_ann:
            if md5(a["link"].encode()).hexdigest() == key:
                link = a["link"]
                discarded.discard(link)
                save_json("discarded.json", discarded)

                # Reinvia l'annuncio da valutare
                try:
                    data = extract(link)
                    send_announcement(data, link)
                    BOT.send_message(update.effective_chat.id, "✅ Annuncio recuperato e rimandato per la valutazione!")
                except Exception as e:
                    BOT.send_message(update.effective_chat.id, f"⚠️ Errore recupero annuncio: {e}")
                return
        BOT.send_message(update.effective_chat.id, "❌ Annuncio non trovato.")

if __name__ == "__main__":
    main()


