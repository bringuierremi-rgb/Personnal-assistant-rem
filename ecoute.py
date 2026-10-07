# ============================================================
#  ÉTAPE 3 — Enregistrer ta question et la transformer en texte
#  1) on enregistre jusqu'à ce que tu te taises
#  2) Whisper (en local sur ton Mac) transcrit l'audio en texte
#  Lancer :  python ecoute.py
# ============================================================
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from config import (TAUX_ECHANTILLONNAGE as SR, SEUIL_SILENCE,
                    DUREE_SILENCE, DUREE_MAX, MODELE_WHISPER)

_whisper = None


def _charger_whisper():
    """Charge Whisper une seule fois (c'est lent la première fois)."""
    global _whisper
    if _whisper is None:
        print("Chargement de Whisper (1re fois : téléchargement de quelques centaines de Mo)...")
        _whisper = WhisperModel(MODELE_WHISPER, device="cpu", compute_type="int8")
    return _whisper


def _vers_interface(valeur):
    try:
        import interface
        interface.niveau(valeur)
    except Exception:
        pass


def enregistrer_phrase(attente_max=8):
    """Enregistre par tranches de 0,1 s et s'arrête après un silence.
    attente_max : secondes d'attente maximum si personne ne parle."""
    pas = 0.1
    bloc_taille = int(SR * pas)
    morceaux, silence, duree, a_parle = [], 0.0, 0.0, False

    with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=bloc_taille) as flux:
        while duree < DUREE_MAX:
            bloc, _ = flux.read(bloc_taille)
            morceaux.append(bloc.copy())
            duree += pas

            volume = np.abs(bloc).mean()
            _vers_interface(volume / (SEUIL_SILENCE * 6))   # l'orbe pulse avec ta voix

            if volume > SEUIL_SILENCE:                # ça parle
                if not a_parle:
                    print("🎙️  Je t'entends...")
                a_parle, silence = True, 0.0
            else:                                     # c'est calme
                silence += pas

            if a_parle and silence >= DUREE_SILENCE:  # tu as fini ta phrase
                break
            if not a_parle and duree >= attente_max:            # personne n'a rien dit
                print("🤫 Je n'ai rien entendu.")
                return None

    print(f"⏹️  Fin de l'enregistrement ({duree:.1f} s)")
    return np.concatenate(morceaux).flatten()


def transcrire(audio):
    """Audio -> texte français."""
    if audio is None:          # rien enregistré : on n'envoie rien à Whisper
        return ""
    # Whisper veut des nombres entre -1 et 1, pas des entiers
    audio_float = audio.astype(np.float32) / 32768.0
    segments, _ = _charger_whisper().transcribe(
        audio_float,
        language="fr",
        beam_size=5,
        vad_filter=True,                   # retire les silences avant de transcrire
        condition_on_previous_text=False,  # évite qu'il invente une suite
    )
    texte = " ".join(s.text.strip() for s in segments).strip()

    # Phrases que Whisper "invente" quand il n'entend que du silence
    # (il a appris sur des vidéos sous-titrées, d'où ces génériques)
    hallucinations = ["amara.org", "sous-titres", "sous-titrage", "merci d'avoir regardé"]
    if any(h in texte.lower() for h in hallucinations):
        return ""
    return texte


if __name__ == "__main__":
    _charger_whisper()
    print("Pose une question, je t'écoute...")
    texte = transcrire(enregistrer_phrase())
    print(f"📝 J'ai compris : « {texte} »")
