"""
PreventFire — backend Flask
Proxy sécurisé vers l'API Anthropic + compression des plans PDF via PyMuPDF.
Génération .docx, persistance SQLite des dossiers.
"""

import base64, io, json, os, re, sqlite3, uuid


def extract_json(text: str) -> dict:
    """Extrait le premier objet JSON valide du texte, même entouré de markdown."""
    text = re.sub(r"```json|```", "", text).strip()
    # Cherche le premier { ... } englobant
    start = text.find("{")
    if start == -1:
        raise ValueError("Aucun JSON trouvé dans la réponse")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i+1])
    raise ValueError("JSON incomplet dans la réponse")
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
from anthropic import Anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGIN", "*")}})

API_KEY   = os.getenv("ANTHROPIC_API_KEY")
MODEL     = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_PAGES = int(os.getenv("MAX_PDF_PAGES", "4"))
RENDER_DPI= int(os.getenv("PDF_RENDER_DPI", "120"))

BASE     = Path(__file__).parent
TMPL_DIR = BASE.parent / "app" / "templates"
DB_PATH  = BASE / "preventfire.db"
PROJ_DIR = BASE.parent / "projets"
PROJ_DIR.mkdir(exist_ok=True)

client = Anthropic(api_key=API_KEY, timeout=90.0) if API_KEY else None

# ── Textes complets des articles AR ──────────────────────────────────────────

ARTICLES = {
    "1.1": ("Accessibilité permanente — voie d'accès",
            {"BB": "Annexe 2/1 art.1.1", "BM": "Annexe 3/1 art.1.1"},
            {"BB": "Voie d'accès ≥ 4 m (libre), hauteur libre ≥ 4 m, rayon braquage int. 11 m / ext. 15 m, pente ≤ 6 %, portance 13 t/essieu. Véhicule à ≤ 60 m d'une façade (bâtiment plain-pied).",
             "BM": "Idem BB, et voie permettant 3 véhicules de 15 t simultanément ; distance voie–façade entre 4 et 10 m. Accessible en permanence."}),
    "1.2": ("Constructions annexes",
            {"BB": "Annexe 2/1 art.1.2", "BM": "Annexe 3/1 art.1.2"},
            "Auvents, encorbellements et adjonctions ne peuvent compromettre ni l'évacuation ni l'action des secours. Toitures dominées par façades vitrées : EI 60 (BB) / EI 120 (BM) à moins d'1 m."),
    "1.3": ("Distance horizontale entre bâtiments",
            {"BB": "Annexe 2/1 art.1.3", "BM": "Annexe 3/1 art.1.3"},
            {"BB": "Distance ≥ (h+10)/2,5 · cos α ou rayonnement ≤ 15 kW/m². Parois contiguës portantes REI 60 ou EI 60 ; communication par porte EI₁ 30.",
             "BM": "Distance selon (1+7·cos α) ou rayonnement ≤ 15 kW/m². Parois contiguës REI 120 ou EI 120 ; communication par sas (2 portes EI₁ 30, parois EI 60, ≥ 2 m²)."}),
    "1.4": ("Accessibilité des façades (BM)",
            {"BM": "Annexe 3/1 art.1.4"},
            {"BM": "Au moins une longue façade longée par voie accessible aux services d'incendie ; distance bord de voie–façade entre 4 et 10 m. Sinon : baies réputées inaccessibles aux auto-échelles."}),
    "2.1": ("Superficie maximale des compartiments",
            {"BB": "Annexe 2/1 art.2.1", "BM": "Annexe 3/1 art.2.1"},
            {"BB": "< 2500 m² (3500 m² pour plain-pied, L ≤ 90 m). Au-delà : sprinklage + EFC.",
             "BM": "< 2500 m² ; un compartiment par niveau en principe. Au-delà : sprinklage + EFC."}),
    "2.2.1": ("Nombre de sorties par compartiment",
              {"BB": "Annexe 2/1 art.2.2.1", "BM": "Annexe 3/1 art.2.2.1"},
              {"BB": "1 sortie si < 100 pers. ; 2 si 100–< 500 ; 2 + n si ≥ 500 (n = entier sup. de N/1000).",
               "BM": "1 sortie si baie/terrasse accessible auto-échelle ; 2 dès 50 pers. (< 500) ; 2 + n si ≥ 500."}),
    "2.2.2": ("Disposition des sorties",
              {"BB": "Annexe 2/1 art.2.2.2", "BM": "Annexe 3/1 art.2.2.2"},
              "Sorties dans des zones opposées du compartiment. Sous-sol : chemin vers extérieur, parois EI 30, portes EI₁ 30."),
    "3.1": ("Traversées des parois RF — Annexe 7 ch.1",
            {"BB": "Annexe 2/1 art.3.1 + Annexe 7 ch.1", "BM": "Annexe 3/1 art.3.1 + Annexe 7 ch.1"},
            "Traversées (fluides, électricité) et joints de dilatation ne peuvent altérer le Rf exigé. Manchons intumescents, mortier RF, caissons coupe-feu selon Annexe 7 ch.1."),
    "3.2": ("Éléments structuraux — stabilité au feu (R)",
            {"BB": "Annexe 2/1 art.3.2 tableau 2.1", "BM": "Annexe 3/1 art.3.2 tableau 3.1"},
            {"BB": "Au-dessus Ei : R 30 (1 niveau) / R 60 (plusieurs niveaux). Sous Ei : R 60. Toiture : R 30 sauf si séparée par EI 30.",
             "BM": "Au-dessus Ei : R 60. Sous Ei (plancher Ei compris) : R 120. Attestation ingénieur en stabilité à remettre à la réception."}),
    "3.3": ("Parois verticales — locaux à occupation nocturne",
            {"BB": "Annexe 2/1 art.3.3", "BM": "Annexe 3/1 art.3.3"},
            {"BB": "Parois EI 30 (1 niveau) / EI 60 (plusieurs niveaux) ; EI 60 sous Ei. Porte d'entrée de logement EI₁ 30.",
             "BM": "Parois EI 60 ; porte d'entrée EI₁ 30."}),
    "3.4": ("Faux-plafonds dans chemins d'évacuation",
            {"BB": "Annexe 2/1 art.3.4", "BM": "Annexe 3/1 art.3.4"},
            "Faux-plafonds EI 30 dans les chemins d'évacuation et locaux accessibles au public. Espace entre plafond et faux-plafond : divisé en volumes ≤ 25 m × 25 m (écrans EI 30, classe A1/A2-s1,d0)."),
    "3.5.1.1": ("Façade simple paroi — jonction compartiment/plancher",
                {"BB": "Annexe 2/1 art.3.5.1.1", "BM": "Annexe 3/1 art.3.5.1.1"},
                "Fixations ossature R 60 à chaque niveau. Liaison parois compartiment/façade EI 60. Joints dalle/façade au droit des séparations horizontales EI 60."),
    "3.5.1.2": ("Façades en vis-à-vis — propagation entre compartiments",
                {"BB": "Annexe 2/1 art.3.5.1.2", "BM": "Annexe 3/1 art.3.5.1.2"},
                {"BB": "Parties sans E 30 : distance ≥ (h+10)/2,5 · cos α, ou rayonnement ≤ 15 kW/m².",
                 "BM": "Parties sans E 60 : distance ≥ (h+10)/2,5 · cos α, ou rayonnement ≤ 15 kW/m²."}),
    "3.5.2": ("Façade double paroi — cavité interrompue",
              {"BB": "Annexe 2/1 art.3.5.2", "BM": "Annexe 3/1 art.3.5.2"},
              "Cavité d'une façade double paroi interrompue par un élément E 60 au droit de chaque paroi de compartiment et des planchers."),
    "5/1 art.2": ("Réaction au feu — type d'occupation (1/2/3)",
                  {"BB": "Annexe 5/1 art.2", "BM": "Annexe 5/1 art.2"},
                  "Classement selon risque : type 1 (non-autonomes), type 2 (autonomes dormants), type 3 (autonomes vigilants). Le MO le détermine et le communique à l'autorité compétente."),
    "5/1 tab.I": ("Réaction au feu — locaux à risque accru",
                  {"BB": "Annexe 5/1 art.3 tableau I", "BM": "Annexe 5/1 art.3 tableau I"},
                  "Locaux techniques, parkings, cuisines, gaines : revêtements A2-s3,d2 (parois), A2-s3,d0 (plafonds), A2FL-s2 ou BFL-s2 (sols). Preuve à la réception."),
    "5/1 tab.II": ("Réaction au feu — locaux selon occupation",
                   {"BB": "Annexe 5/1 art.3 tableau II", "BM": "Annexe 5/1 art.3 tableau II"},
                   "Classes de réaction au feu selon tableau II pour les locaux. Preuve à la réception : marquage CE, rapport de classement ou BENOR/ATG + attestation de pose."),
    "5/1 tab.III": ("Réaction au feu — chemins d'évacuation & cages d'escalier",
                    {"BB": "Annexe 5/1 art.4/1 tableau III", "BM": "Annexe 5/1 art.4/1 tableau III"},
                    "Classes de réaction au feu selon tableau III pour les chemins et cages. Attestations à remettre à la réception."),
    "5/1 art.6": ("Réaction au feu — façades extérieures",
                  {"BB": "Annexe 5/1 art.6.1.1", "BM": "Annexe 5/1 art.6.1.1"},
                  "Revêtement extérieur ≥ B-s3,d1. Composants substantiels ≥ A2-s3,d0. Montants ossature A1. Attestations à remettre à la réception."),
    "5/1 art.8": ("Réaction au feu — toitures BROOF(t1)",
                  {"BB": "Annexe 5/1 art.8.1+8.3", "BM": "Annexe 5/1 art.8.1+8.3"},
                  "Produits de toiture : classe BROOF(t1). Idem pour balcons, terrasses, lanterneaux, panneaux PV. Attestations à remettre à la réception."),
    "4.1": ("Parois entre compartiments",
            {"BB": "Annexe 2/1 art.4.1", "BM": "Annexe 3/1 art.4.1"},
            {"BB": "EI 30 (1 niveau au-dessus Ei) / EI 60 (plusieurs niveaux ou sous Ei). Communication : porte EI₁ 30 FA.",
             "BM": "EI 120. Communication : sas (parois EI 120, portes EI₁ 30 FA, ≥ 2 m²)."}),
    "4.2.1": ("Encloisonnement des cages d'escalier",
              {"BB": "Annexe 2/1 art.4.2.1", "BM": "Annexe 3/1 art.4.2.1"},
              "Escaliers reliant plusieurs compartiments : encloisonnés. Prescriptions de compartimentage applicables."),
    "4.2.2.1": ("Parois intérieures des cages ≥ EI 60",
                {"BB": "Annexe 2/1 art.4.2.2.1", "BM": "Annexe 3/1 art.4.2.2.1"},
                {"BB": "Parois intérieures des cages d'escalier : EI 60.",
                 "BM": "Parois intérieures des cages d'escalier : EI 120."}),
    "4.2.2.2": ("Accès au niveau d'évacuation depuis chaque cage",
                {"BB": "Annexe 2/1 art.4.2.2.2", "BM": "Annexe 3/1 art.4.2.2.2"},
                "Chaque cage donne accès, directement ou par chemin d'évacuation, à un niveau d'évacuation."),
    "4.2.2.3": ("Communication compartiment / cage — porte EI₁ 30",
                {"BB": "Annexe 2/1 art.4.2.2.3", "BM": "Annexe 3/1 art.4.2.2.3"},
                "À chaque niveau : porte EI₁ 30 FA entre compartiment et cage. Idem pour toutes les portes intérieures donnant dans la cage."),
    "4.2.2.4": ("Cages communes à plusieurs compartiments",
                {"BB": "Annexe 2/1 art.4.2.2.4", "BM": "Annexe 3/1 art.4.2.2.4"},
                "Cage commune à plusieurs compartiments : chaque compartiment y accède par une porte EI₁ 30 FA."),
    "4.2.2.5": ("Séparation cages sous-sol / cages niveaux supérieurs",
                {"BB": "Annexe 2/1 art.4.2.2.5", "BM": "Annexe 3/1 art.4.2.2.5"},
                "Cages sous-sol ≠ prolongement des cages supérieures. Si superposées : parois EI 60, portes EI₁ 30."),
    "4.2.2.6": ("Baie de ventilation ≥ 1 m² en tête de cage",
                {"BB": "Annexe 2/1 art.4.2.2.6", "BM": "Annexe 3/1 art.4.2.2.6"},
                "Baie à l'air libre ≥ 1 m² (0,5 m² si cage ≤ 300 m², max 2 niveaux) en tête de cage. Commande manuelle au niveau Ei entre 1,4 et 2 m à ≤ 2 m de la porte de cage. Conforme NBN S21-208/3."),
    "4.2.3.1": ("Escaliers — R 30, giron, hauteur de marche, pente",
                {"BB": "Annexe 2/1 art.4.2.3.1", "BM": "Annexe 3/1 art.4.2.3.1"},
                {"BB": "Escaliers R 30. Giron ≥ 20 cm. Marche ≤ 18 cm. Pente ≤ 75 %. Mains courantes (une si largeur < 120 cm).",
                 "BM": "Escaliers R 60. Contre-marches pleines. Giron ≥ 20 cm. Marche ≤ 18 cm. Pente ≤ 75 %. Mains courantes."}),
    "4.2.3.2": ("Largeur utile escaliers & paliers ≥ 0,80 m",
                {"BB": "Annexe 2/1 art.4.2.3.2", "BM": "Annexe 3/1 art.4.2.3.2"},
                "Largeur utile ≥ 0,80 m. Différence ≤ 1 unité de passage entre volées et paliers d'une même cage."),
    "4.3": ("Escaliers extérieurs — classe A1",
            {"BB": "Annexe 2/1 art.4.3", "BM": "Annexe 3/1 art.4.3"},
            "Donnent accès au niveau d'évacuation. Aucune stabilité au feu requise, mais matériau de classe A1. BM : cages extérieures à parois, communication par porte EI₁ 30, aucun point à < 1 m d'une façade sans EI 60."),
    "4.4.1.1": ("Largeur utile chemins d'évacuation ≥ 0,80 m",
                {"BB": "Annexe 2/1 art.4.4.1.1", "BM": "Annexe 3/1 art.4.4.1.1"},
                "Chemins et portes d'évacuation ≥ 0,80 m. Coursives ≥ 0,60 m. Largeur ≥ unité de passage requise."),
    "4.4.1.2": ("Définition d'une sortie de compartiment",
                {"BB": "Annexe 2/1 art.4.4.1.2", "BM": "Annexe 3/1 art.4.4.1.2"},
                "Sortie = cage int. (art.4.2), cage ext. (art.4.3), accès direct extérieur au niveau Ei, ou chemin d'évacuation au niveau Ei conforme à art.4.4.2."),
    "4.4.1.3": ("Portes — pas de verrouillage côté évacuation",
                {"BB": "Annexe 2/1 art.4.4.1.3", "BM": "Annexe 3/1 art.4.4.1.3"},
                "Sur parcours d'évacuation : portes s'ouvrant facilement et immédiatement dans le sens de l'évacuation, sans clé."),
    "4.4.2": ("Chemins d'évacuation au niveau Ei",
              {"BB": "Annexe 2/1 art.4.4.2", "BM": "Annexe 3/1 art.4.4.2"},
              {"BB": "Parois verticales intérieures EI 60. Portes d'accès EI₁ 30 FA.",
               "BM": "Parois verticales intérieures EI 120. Portes d'accès EI₁ 60 FA."}),
    "4.4.3": ("Chemins d'évacuation aux autres niveaux",
              {"BB": "Annexe 2/1 art.4.4.3", "BM": "Annexe 3/1 art.4.4.3"},
              "Parois EI 30 ; portes EI₁ 30 FA. Exception : occupation exclusivement diurne et superficie < 1250 m²."),
    "4.4.4": ("Sas d'accès à la cage — > 6 appts/niveau (BM)",
              {"BM": "Annexe 3/1 art.4.4.4"},
              {"BM": "Si > 6 appartements par cage et par niveau : accès à la cage via un sas (parois EI 60, deux portes EI₁ 30 FA)."}),
    "4.5": ("Signalisation — numéros de niveaux dans les cages",
            {"BB": "Annexe 2/1 art.4.5", "BM": "Annexe 3/1 art.4.5"},
            "Numéro de niveau visible à chaque accès à la cage d'escalier, sur les paliers et dans les dégagements."),
    "5.1.1": ("Local technique = compartiment distinct",
              {"BB": "Annexe 2/1 art.5.1.1", "BM": "Annexe 3/1 art.5.1.1"},
              "Local technique = compartiment distinct. Parois REI 60 ou EI 60, portes EI₁ 30 FA. Distinct des caves."),
    "5.1.2.2": ("Chaufferie — Annexe 7, point 4",
                {"BB": "Annexe 2/1 art.5.1.2.2", "BM": "Annexe 3/1 art.5.1.2.2"},
                "Chaufferies (locaux de chauffe ≥ 30 kW) conformes aux dispositions de l'Annexe 7, point 4."),
    "5.1.3": ("Cabine haute tension — NBN C18-200",
              {"BB": "Annexe 2/1 art.5.1.3", "BM": "Annexe 3/1 art.5.1.3"},
              "Cabines HT : compartiment distinct, conformes à NBN C18-200."),
    "5.1.4": ("Gaines verticales & horizontales (BM)",
              {"BM": "Annexe 3/1 art.5.1.4"},
              {"BM": "Gaines verticales EI 120, portillons EI₁ 60. Gaines horizontales EI 120 au droit des parois de compartiment."}),
    "5.2.1": ("Parking — éléments structuraux, EFC, cloisonnement",
              {"BB": "Annexe 2/1 art.5.2.1", "BM": "Annexe 3/1 art.5.2.1"},
              "R 120. Si > 625 m² : EFC. Paroi parking/bâtiment EI 60 + sas (EI 60 + portes EI₁ 30) ou porte EI₁ 60. ≥ 2 cages d'escalier, distance ≤ 45 m."),
    "5.2.4": ("Parking — DAI si superficie > 1250 m²",
              {"BB": "Annexe 2/1 art.5.2.4", "BM": "Annexe 3/1 art.5.2.4"},
              "Parking > 1250 m² : installation de détection automatique d'incendie conforme NBN S21-100."),
    "6.4": ("Ascenseurs — gaine EI 60, rappel au niveau Ei",
            {"BB": "AR 09/03/2009 + Annexe 2/1 art.6.4", "BM": "AR 09/03/2009 + Annexe 3/1 art.6.4"},
            {"BB": "Gaine + paliers EI 60. Portes palières E 30. Rappel au niveau Ei (NBN EN 81-73). Pas d'extinction eau dans la gaine.",
             "BM": "Gaine + paliers EI 60 formant sas à tous les niveaux. Portes d'accès sas EI₁ 30. Portes palières E 30. Rappel au niveau Ei. Pas d'extinction eau dans la gaine."}),
    "6.5.1": ("Installations électriques BT — RGIE",
              {"BB": "Annexe 2/1 art.6.5.1", "BM": "Annexe 3/1 art.6.5.1"},
              "Conformité RGIE. Contrôle par organisme agréé (SPF Économie) avant mise en service. Copie PV à remettre à la zone de secours."),
    "6.5.2": ("Canalisations circuits de sécurité PH 60 (BM)",
              {"BM": "Annexe 3/1 art.6.5.2"},
              {"BM": "Canalisations des circuits de sécurité (éclairage urgence, alarme, détection, désenfumage) : PH 60 ou Rf 1 h (NBN 713-020)."}),
    "6.5.4": ("Éclairage de sécurité ≥ 1 lux / 5 lux aux endroits dangereux",
              {"BB": "Annexe 2/1 art.6.5.4", "BM": "Annexe 3/1 art.6.5.4"},
              "Éclairage de sécurité ≥ 1 lux (5 lux aux endroits dangereux). Appareils autonomes admis. Conformité NBN EN 1838/50172/60598-2-22. Copie attestation à remettre."),
    "6.6": ("Installations de gaz — NBN D 51-003",
            {"BB": "Annexe 2/1 art.6.6", "BM": "Annexe 3/1 art.6.6"},
            "Conformité NBN D 51-003. Attestation à remettre. Canalisation peinte jaune ocre (RAL 1004). Vanne trottoir signalée 'G'."),
    "6.7": ("Installations aérauliques — clapets RF, arrêt sur détection",
            {"BB": "Annexe 2/1 art.6.7", "BM": "Annexe 3/1 art.6.7"},
            "Clapets RF aux traversées, coupe-fumée, arrêt groupes sur détection. Contrôle par organisme indépendant. Copie PV à remettre."),
    "6.8.1": ("Dispositifs d'extinction obligatoires",
              {"BB": "Annexe 2/1 art.6.8.1", "BM": "Annexe 3/1 art.6.8.1"},
              "Type, nombre et emplacement déterminés en accord avec les services d'incendie. ≥ 1 dévidoir par compartiment > 500 m². Bouches/bornes ≤ 100 m zone dense."),
    "6.8.4": ("Alarme incendie — signal perceptible en tout point",
              {"BB": "Annexe 2/1 art.6.8.4", "BM": "Annexe 3/1 art.6.8.4"},
              "Boutons-poussoirs sous vitre + sirène audible partout. Boutons à proximité des baies vers extérieur, paliers, dégagements. Fonctionne sans alimentation principale."),
    "6.8.5.2": ("Extincteurs portatifs ≥ 6 kg ABC / 6 L eau pulvérisée",
                {"BB": "Annexe 2/1 art.6.8.5.2", "BM": "Annexe 3/1 art.6.8.5.2"},
                "≥ 1 extincteur 6 kg poudre ABC ou 6 L eau pulv. + additif par 150 m² et par niveau. Marquage CE (BENOR recommandé). Fixé au mur et signalé."),
    "6.8.5.3": ("Robinets d'incendie armés — BM",
                {"BM": "Annexe 3/1 art.6.8.5.3"},
                {"BM": "RIA conformes EN 671-1. Pression ≥ 2,5 bar, débit ≥ 72 L/min (3 RIA simultanés, 30 min). Canalisations rouges (RAL 3000)."}),
    "6.8.5.4.2": ("Borne incendie ≤ 100 m (zone commerciale) / 200 m",
                  {"BB": "Annexe 2/1 art.6.8.5.4.2", "BM": "Annexe 3/1 art.6.8.5.4.2"},
                  "Borne/bouche aérienne ≤ 100 m (zone commerciale dense) ou ≤ 200 m (ailleurs) de l'entrée. Sinon : installer borne conforme NBN S21-019."),
    "AGW": ("Détecteurs de fumée dans les logements",
            {"BB": "AGW du 21/10/2004", "BM": "AGW du 21/10/2004"},
            "≥ 1 détecteur optique certifié BOSEC par niveau de logement. ≥ 2 si superficie > 80 m². Si ≥ 4 détecteurs : interconnectés ou sur centrale. Conformité AGW art.4."),
}

ALL_IDS = list(ARTICLES.keys())

# ── SQLite ────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            reference TEXT,
            name TEXT,
            address TEXT,
            type TEXT DEFAULT 'BB',
            zone TEXT DEFAULT '',
            agent TEXT DEFAULT '',
            date TEXT,
            hyp TEXT DEFAULT '{}',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS items (
            project_id TEXT,
            item_id TEXT,
            status TEXT DEFAULT '',
            comment TEXT DEFAULT '',
            measure TEXT DEFAULT '',
            PRIMARY KEY (project_id, item_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """)


init_db()

# ── PDF helpers ───────────────────────────────────────────────────────────────

def pdf_to_image_blocks(pdf_bytes: bytes, max_pages: int = MAX_PAGES, dpi: int = RENDER_DPI):
    blocks = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for page in doc[:max_pages]:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            jpeg = pix.tobytes("jpeg", jpg_quality=75)
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.b64encode(jpeg).decode("ascii"),
                },
            })
    finally:
        doc.close()
    return blocks


def file_to_blocks(b64: str, media_type: str, is_pdf: bool) -> list:
    raw = base64.b64decode(b64)
    if is_pdf:
        return pdf_to_image_blocks(raw)
    return [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}]


def files_to_blocks(files: list, max_total: int = 12) -> list:
    """Convertit une liste de fichiers [{base64, mediaType, isPdf}] en blocs image.
    Limite à max_total blocs pour rester dans les limites de l'API."""
    blocks = []
    for f in files:
        if len(blocks) >= max_total:
            break
        b64 = f.get("base64", "")
        media_type = f.get("mediaType", "image/jpeg")
        is_pdf = bool(f.get("isPdf"))
        remaining = max_total - len(blocks)
        try:
            if is_pdf:
                raw = base64.b64decode(b64)
                new_blocks = pdf_to_image_blocks(raw, max_pages=min(MAX_PAGES, remaining))
            else:
                new_blocks = [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}]
            blocks.extend(new_blocks[:remaining])
        except Exception:
            continue
    return blocks


def request_to_blocks(data: dict) -> list:
    """Résout indifféremment l'ancien format (base64 unique) et le nouveau (files:[])."""
    files_list = data.get("files")
    if files_list:
        return files_to_blocks(files_list)
    # Rétrocompatibilité avec l'ancien format champ unique
    b64 = data.get("base64")
    if not b64:
        return []
    return file_to_blocks(b64, data.get("mediaType", "image/png"), bool(data.get("isPdf")))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "model": MODEL, "key_loaded": bool(API_KEY)})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Pré-analyse libre du plan (résumé + observations par catégorie)."""
    if client is None:
        return jsonify({"error": "Clé ANTHROPIC_API_KEY absente côté serveur."}), 500

    data = request.get_json(silent=True) or {}
    building_type = data.get("buildingType", "BB")
    categories    = data.get("categories") or []

    try:
        content_blocks = request_to_blocks(data)
        if not content_blocks:
            return jsonify({"error": "Aucun plan reçu ou fichier illisible."}), 400
    except Exception as exc:
        return jsonify({"error": f"Traitement du plan impossible : {exc}"}), 400

    type_label = "Bâtiment Bas (Annexe 2/1)" if building_type == "BB" else "Bâtiment Moyen (Annexe 3/1)"
    cats = " ; ".join(f"{c['id']} = {c['title']}" for c in categories)
    prompt = (
        "Tu assistes un agent de prévention incendie belge qui examine un plan "
        "d'architecte (souvent un avant-projet, AVP). Référentiel : AR du "
        f"07/07/1994 — {type_label}.\n"
        "N'analyse QUE ce qui est réellement lisible sur un plan : implantation, "
        "accès, sorties et leur répartition, distances d'évacuation, cages "
        "d'escaliers, compartimentage apparent, locaux à risque identifiables. "
        "N'invente PAS de verdict de conformité sur des éléments non figurés.\n"
        f"Catégories disponibles (utilise exactement ces identifiants pour \"cat\") : {cats}.\n"
        "Réponds UNIQUEMENT en JSON valide, sans texte ni balises autour :\n"
        '{"synthese":"2-3 phrases sur ce que montre le plan","observations":'
        '[{"cat":"<id>","point":"titre court","constat":"ce qui est observé ou '
        'à vérifier","gravite":"info|attention|manquement"}]}'
    )

    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=1500,
            messages=[{"role": "user", "content": content_blocks + [{"type": "text", "text": prompt}]}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        parsed = extract_json(text)
        return jsonify({"synthese": parsed.get("synthese", ""), "observations": parsed.get("observations", [])})
    except Exception as exc:
        return jsonify({"error": f"Échec de l'analyse : {exc}"}), 500


@app.route("/api/extract", methods=["POST"])
def extract():
    """Extrait les infos administratives du plan via Claude."""
    if client is None:
        return jsonify({"error": "Clé API absente."}), 500

    data  = request.get_json(silent=True) or {}

    try:
        content_blocks = request_to_blocks(data)[:4]
        if not content_blocks:
            return jsonify({"error": "Aucun plan reçu."}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    prompt = """Tu es expert en prévention incendie belge.
Analyse ces plans d'architecture et extrait les informations administratives.
Retourne UNIQUEMENT ce JSON sans markdown :
{
  "nom": "dénomination du projet",
  "adresse": "adresse complète",
  "commune": "nom de la commune",
  "mo": "nom du maître d'ouvrage",
  "architecte": "nom et adresse du bureau d'architectes",
  "type_batiment": "BB ou BM",
  "hauteur_h": "hauteur h calculée si visible, sinon vide",
  "hypotheses": {
    "logements": true,
    "ss": false,
    "parking": false,
    "ascenseur": false,
    "gaz": false,
    "chaufferie": false,
    "esc_ext": false,
    "ht": false
  }
}"""
    content_blocks.append({"type": "text", "text": prompt})

    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=1000,
            messages=[{"role": "user", "content": content_blocks}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return jsonify(extract_json(text))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/analyze_plans", methods=["POST"])
def analyze_plans():
    """Analyse article par article et retourne les statuts (ok/nok/q/na)."""
    if client is None:
        return jsonify({"error": "Clé API absente."}), 500

    data    = request.get_json(silent=True) or {}
    bat     = data.get("buildingType", "BB")
    hyp     = data.get("hyp", {})

    try:
        content_blocks = request_to_blocks(data)
        if not content_blocks:
            return jsonify({"error": "Aucun plan reçu."}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    # Auto-NA selon hypothèses + type bâtiment
    auto_na = set()
    if bat == "BB":
        auto_na.update(["1.4", "4.4.4", "5.1.4", "6.5.2", "6.8.5.3"])
    if not hyp.get("ss"):
        auto_na.add("4.2.2.5")
    if not hyp.get("ascenseur"):
        auto_na.add("6.4")
    if not hyp.get("gaz"):
        auto_na.add("6.6")
    if not hyp.get("parking"):
        auto_na.update(["5.2.1", "5.2.4"])
    if not hyp.get("logements", True):
        auto_na.update(["3.3", "AGW"])
    if not hyp.get("chaufferie"):
        auto_na.add("5.1.2.2")
    if not hyp.get("ht"):
        auto_na.add("5.1.3")
    if not hyp.get("esc_ext"):
        auto_na.add("4.3")

    to_analyze = [i for i in ALL_IDS if i not in auto_na]
    ids_str = "{\n" + ",\n".join([f'"{i}":"ok|nok|q"' for i in to_analyze]) + "\n}"

    prompt = f"""Tu es agent de prévention incendie belge expert en AR 07.07.1994.
Type bâtiment : {bat} | Annexe : {"2/1" if bat == "BB" else "3/1"}

Ce que tu PEUX lire sur les plans : dimensions espaces, présence/absence éléments (cages, baies, sas, parking, sous-sol), programme niveaux, superficies, mode chauffage si indiqué, hauteur si cotée.
Ce que tu NE PEUX PAS lire (mettre "q") : résistances au feu (EI, R, REI), installations électriques/alarme/extincteurs, matériaux.

Règles : "ok" = visible ET conforme. "nok" = problème détecté (ex: largeur < 80 cm visible, baie absente). "q" = non déterminable depuis les plans.

Retourne UNIQUEMENT ce JSON sans markdown :
{{"statuses":{ids_str},"observations":"observations générales"}}"""

    content_blocks.append({"type": "text", "text": prompt})

    try:
        msg = client.messages.create(
            model=MODEL, max_tokens=2000,
            messages=[{"role": "user", "content": content_blocks}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        result = extract_json(text)
        # Injecter les auto-NA
        if "statuses" in result:
            for aid in auto_na:
                result["statuses"][aid] = "na"
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/generate_text", methods=["POST"])
def generate_text():
    """Retourne les textes complets des articles pour les points nok/q."""
    data    = request.get_json(silent=True) or {}
    bat     = data.get("type_batiment", "BB").upper()
    nok_ids = data.get("nok_ids", [])
    q_ids   = data.get("q_ids", [])

    points = []
    num = 1

    def _entry(pid, status):
        if pid not in ARTICLES:
            return None
        titre, ann_dict, texte_data = ARTICLES[pid]
        ann_ref = ann_dict.get(bat, list(ann_dict.values())[0])
        texte = (texte_data.get(bat, texte_data.get("BB", texte_data))
                 if isinstance(texte_data, dict) else texte_data)
        if status == "q":
            texte += "\n\nN'apparaît pas sur les plans transmis. Des informations complémentaires sont demandées à l'architecte."
        return {"num": num, "id": pid, "titre": titre, "ref": ann_ref, "texte": texte, "status": status}

    for pid in nok_ids:
        e = _entry(pid, "nok")
        if e:
            points.append(e)
            num += 1
    for pid in q_ids:
        e = _entry(pid, "q")
        if e:
            points.append(e)
            num += 1

    return jsonify({"points": points})


@app.route("/api/generate", methods=["POST"])
def generate():
    """Génère un .docx à partir des templates de zone."""
    data     = request.get_json(silent=True) or {}
    zone     = data.get("zone", "ZSBW")
    bat      = data.get("type_batiment", "BB").upper()

    tmpl_path = TMPL_DIR / f"{zone}_{bat}.docx"
    if not tmpl_path.exists():
        return jsonify({"error": f"Template {zone}/{bat} introuvable ({tmpl_path})"}), 404

    try:
        import zipfile

        with open(str(tmpl_path), "rb") as f:
            tmpl_bytes = f.read()

        tmpl_zip = zipfile.ZipFile(io.BytesIO(tmpl_bytes))
        doc_xml  = tmpl_zip.read("word/document.xml").decode("utf-8")

        now = datetime.now().strftime("%d/%m/%Y")
        fields = {
            "[DOS_DOS_NAME]":      data.get("nom", ""),
            "[DOS_DOS_STREET]":    data.get("adresse", ""),
            "[DOS_DOS_ZIPCODE]":   data.get("codepostal", ""),
            "[DOS_DOS_TOWN]":      data.get("commune", ""),
            "[DOS_DOS_CODE]":      data.get("reference", ""),
            "[DOS_DOS_TYPE]":      data.get("fonction", ""),
            "[DOS_OWN_NAME]":      data.get("mo", ""),
            "[DOS_OWN_STREET]":    "",
            "[DOS_OWN_ZIPCODE]":   "",
            "[DOS_OWN_TOWN]":      "",
            "[MIS_REFNR]":         data.get("reference", ""),
            "[MIS_DATE_REG]":      data.get("vref", ""),
            "[DOC_DATE]":          data.get("date", now),
            "[MIS_DEP_NAME]":      data.get("commune", ""),
            "[MIS_PREVENTIONIST]": data.get("agent", ""),
            "[MIS_PREV_EMAIL]":    data.get("prev_email", ""),
            "[MIS_PREV_FBNAME]":   data.get("commune", ""),
            "[MIS_TYPE]":          data.get("mission", "Avis sur plan"),
            "[MIS_ARCH_NAME]":     data.get("architecte", ""),
            "[MIS_REQ_NAME]":      data.get("mo", ""),
        }
        for k, v in fields.items():
            doc_xml = doc_xml.replace(k, str(v))

        doc_xml = re.sub(r'<w:highlight w:val="[^"]+"/>', "", doc_xml)

        out_buf = io.BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as out_zip:
            for item in tmpl_zip.infolist():
                if item.filename == "word/document.xml":
                    out_zip.writestr(item, doc_xml.encode("utf-8"))
                else:
                    out_zip.writestr(item, tmpl_zip.read(item.filename))
        tmpl_zip.close()

        safe_name = re.sub(r"[^\w\-]", "_", data.get("nom", "rapport"))[:40]
        out_name  = f"PreventFire_{zone}_{bat}_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
        out_path  = PROJ_DIR / out_name
        out_path.write_bytes(out_buf.getvalue())

        return send_file(
            str(out_path), as_attachment=True, download_name=out_name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Projects CRUD ─────────────────────────────────────────────────────────────

@app.route("/api/projets", methods=["GET"])
def list_projects():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, reference, name, address, type, zone, agent, date, updated_at "
            "FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/projets", methods=["POST"])
def save_project():
    data = request.get_json(silent=True) or {}
    project_id = data.get("id") or str(uuid.uuid4())
    now = datetime.now().isoformat()

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE projects SET reference=?, name=?, address=?, type=?, zone=?, agent=?, date=?, hyp=?, updated_at=? WHERE id=?",
                (data.get("reference", ""), data.get("name", ""), data.get("address", ""),
                 data.get("type", "BB"), data.get("zone", ""), data.get("agent", ""),
                 data.get("date", ""), json.dumps(data.get("hyp", {})), now, project_id),
            )
        else:
            conn.execute(
                "INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (project_id, data.get("reference", ""), data.get("name", ""),
                 data.get("address", ""), data.get("type", "BB"), data.get("zone", ""),
                 data.get("agent", ""), data.get("date", ""),
                 json.dumps(data.get("hyp", {})), now, now),
            )
        # Save items
        items = data.get("items", {})
        conn.execute("DELETE FROM items WHERE project_id=?", (project_id,))
        for item_id, val in items.items():
            conn.execute(
                "INSERT INTO items VALUES (?,?,?,?,?)",
                (project_id, item_id, val.get("status", ""), val.get("comment", ""), val.get("measure", "")),
            )

    return jsonify({"id": project_id, "saved": True})


@app.route("/api/projets/<project_id>", methods=["GET"])
def load_project(project_id):
    with get_db() as conn:
        p = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not p:
            return jsonify({"error": "Dossier introuvable"}), 404
        rows = conn.execute("SELECT * FROM items WHERE project_id=?", (project_id,)).fetchall()
    proj = dict(p)
    proj["hyp"] = json.loads(proj.get("hyp") or "{}")
    proj["items"] = {r["item_id"]: {"status": r["status"], "comment": r["comment"], "measure": r["measure"]} for r in rows}
    return jsonify(proj)


@app.route("/api/projets/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    with get_db() as conn:
        conn.execute("DELETE FROM items WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    return jsonify({"deleted": True})


@app.route("/api/zones", methods=["GET"])
def list_zones():
    zones = []
    for f in TMPL_DIR.glob("*_BB.docx"):
        zone = f.stem.replace("_BB", "")
        zones.append(zone)
    return jsonify(sorted(zones))


# ── Serve frontend (production build) ────────────────────────────────────────

FRONTEND_DIST = BASE.parent / "frontend" / "dist"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        from flask import abort
        abort(404)
    target = FRONTEND_DIST / path
    if path and target.exists():
        return send_file(str(target))
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return send_file(str(index))
    return jsonify({"error": "Frontend non compilé. Lancez npm run build dans frontend/"}), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
