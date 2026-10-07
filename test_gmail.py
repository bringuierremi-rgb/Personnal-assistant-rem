# ============================================================
#  TEST — Vérifie l'accès à tes deux boîtes Gmail
#  La 1re fois : une page Google s'ouvre pour chaque compte.
#  Lancer :  python test_gmail.py
# ============================================================
import gmail_outils
from config_emails import COMPTES_GMAIL

for compte, adresse in COMPTES_GMAIL.items():
    print(f"\n📬 {compte} ({adresse}) — 5 derniers emails non lus :")
    try:
        emails = gmail_outils.chercher(compte, "is:unread", 5)
        if not emails:
            print("   Aucun email non lu.")
        for e in emails:
            print(f"   • {e['sujet'][:60]}  —  {e['de'][:40]}")
    except Exception as erreur:
        print(f"   ❌ {erreur}")

print("\n✅ Test terminé.")
