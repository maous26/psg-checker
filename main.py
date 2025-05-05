import os
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import schedule

# Charger les variables d'environnement
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))

URL = "https://billetterie.psg.fr/fr/offres/abonnements"
CHECK_INTERVAL_MIN = 5

# Mots-clés à rechercher
MOTS_CLES_IMPORTANTS = [
    "abonnement", "abonnements",
    "nouvelle", "nouveaux", "nouvelles",
    "mise", "vente",
    "campagne",
    "disponible", "disponibilité", "disponibles",
    "ouverture", "ouverts", "ouvert",
    "inscription", "inscriptions",
    "prévente", "pré-vente",
    "souscription", "souscrire",
    "accès", "réservation", "réserver"
]

# Combinaisons à forte valeur
COMBINAISONS_CRITIQUES = [
    ("abonnement", "disponible"),
    ("abonnement", "nouvelle"),
    ("mise", "vente"),
    ("campagne", "abonnement"),
    ("ouverture", "vente")  
]

derniere_detection = set()

def send_telegram_message(text):
    """Envoyer un message via l'API Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def verifier_disponibilite():
    global derniere_detection
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        time.sleep(5)
        contenu = driver.page_source
        driver.quit()

        soup = BeautifulSoup(contenu, "html.parser")
        texte = soup.get_text().lower()

        # Recherche mots simples
        found_keywords = []
        for keyword in MOTS_CLES_IMPORTANTS:
            if keyword in texte:
                found_keywords.append(keyword)

        # Recherche combinaisons critiques
        found_combinations = []
        for combo in COMBINAISONS_CRITIQUES:
            if all(word in texte for word in combo):
                found_combinations.append(" + ".join(combo))

        # Nouveaux éléments
        triggers = found_keywords + found_combinations
        nouveaux = [t for t in triggers if t not in derniere_detection]

        if nouveaux:
            derniere_detection.update(nouveaux)
            
            # Priorité aux combinaisons critiques
            alert_level = "🚨 *ALERTE URGENTE PSG*" if any("+" in x for x in nouveaux) else "⚠️ *INFORMATION PSG*"
            
            message = f"{alert_level}\n\n"
            
            # Séparer nouveaux mots-clés et combinaisons
            nouveaux_combos = [x for x in nouveaux if "+" in x]
            nouveaux_keywords = [x for x in nouveaux if "+" not in x]
            
            if nouveaux_combos:
                message += "Combinaisons importantes détectées :\n"
                message += "\n".join(f"🎯 {combo}" for combo in nouveaux_combos) + "\n\n"
            
            if nouveaux_keywords:
                message += "Mots-clés détectés :\n"
                message += "\n".join(f"• {keyword}" for keyword in nouveaux_keywords) + "\n\n"
            
            message += f"🔗 [Voir maintenant]({URL})"
            
            send_telegram_message(message)
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Alerte envoyée: {nouveaux}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Aucun mot-clé détecté.")

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Erreur:", e)

# Lancement programmé
schedule.every(CHECK_INTERVAL_MIN).minutes.do(verifier_disponibilite)

print("🚀 Script lancé. Vérification toutes les 5 minutes...")
send_telegram_message("🚀 Script PSG démarré avec succès!")
verifier_disponibilite()

while True:
    schedule.run_pending()
    time.sleep(1)