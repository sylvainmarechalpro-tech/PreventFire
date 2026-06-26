"""
PreventFire Pro v3.5 - Serveur local Flask
http://localhost:5174
"""
import os, sys, json, re, shutil, tempfile, subprocess, threading, webbrowser
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory

BASE        = Path(__file__).parent.resolve()
TMPL_DIR    = BASE / "templates"
ENGINE_DIR  = BASE / "engine"
SCRIPTS_DIR = BASE / "scripts" / "office"
PROJETS_DIR = BASE.parent / "projets"
PROJETS_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE / "static"))

@app.after_request
def no_cache(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

TEMPLATES = {
    "ZSBW":    {"BB": TMPL_DIR/"ZSBW_BB.docx",   "BM": TMPL_DIR/"ZSBW_BM.docx"},
    "NAGE":    {"BB": TMPL_DIR/"NAGE_BB.docx",    "BM": TMPL_DIR/"NAGE_BM.docx"},
    "DINAPHI": {"BB": TMPL_DIR/"DINAPHI_BB.docx", "BM": TMPL_DIR/"DINAPHI_BM.docx"},
}

# Textes complets des articles AR pour chaque point
ARTICLES = {
    "1.1":  ("Accessibilité permanente — chemins d'accès", "Annexe {ann} art.1.1",
             "Les véhicules des services d'incendie doivent pouvoir atteindre, en un point au moins, une façade donnant accès à chaque niveau. La voie d'accès présente une largeur libre d'au moins 4m, une hauteur libre d'au moins 4m, un rayon de braquage intérieur d'au moins 11m et extérieur d'au moins 15m, une pente maximale de 6% et une capacité portante suffisante."),
    "1.2":  ("Constructions annexes — auvents, encorbellements", "Annexe {ann} art.1.2",
             "Les constructions annexes, auvents, ouvrages en encorbellement ou autres adjonctions éventuelles ne peuvent pas empêcher l'évacuation des personnes ni l'intervention des services d'incendie."),
    "1.3":  ("Distance horizontale entre bâtiments", "Annexe {ann} art.1.3",
             "La distance horizontale entre les façades de bâtiments différents est au moins égale à (h+10)/2,5 × cosα mètres, où h est la hauteur du bâtiment le plus élevé et α l'angle formé par les façades. Si les bâtiments sont contigus, les parois séparatives présentent REI 60 ou EI 60."),
    "2.1":  ("Superficie maximale des compartiments", "Annexe {ann} art.2.1",
             "La superficie d'un compartiment ne peut pas dépasser 2500m² (3500m² pour les bâtiments bas plain-pied, avec une longueur maximale de 90m). Une dérogation est possible avec sprinklage + EFC appropriés."),
    "2.2.1":("Nombre de sorties par compartiment", "Annexe {ann} art.2.2.1",
             "Chaque compartiment doit disposer d'au moins une sortie si le nombre d'occupants est inférieur à 100. Si le nombre d'occupants est ≥ 100, deux sorties au minimum sont requises."),
    "2.2.2":("Sorties et chemins d'évacuation", "Annexe {ann} art.2.2.2",
             "Les sorties donnent accès à une cage d'escalier, à l'extérieur ou à un chemin d'évacuation conforme. Pour les niveaux en sous-sol, le chemin d'évacuation vers l'extérieur présente des parois EI 30 et des portes EI₁ 30."),
    "3.1":  ("Traversées de parois résistantes au feu", "Annexe {ann} art.3.1 + Annexe 7 ch.1",
             "Les traversées de parois par des conduites de fluides ou d'électricité et les joints de dilatation des parois ne peuvent pas altérer le degré de résistance au feu exigé pour cet élément de construction. Les dispositions de l'annexe 7 - chapitre 1er sont d'application (manchons intumescents, mortier RF, etc.)."),
    "3.2":  ("Éléments structuraux — stabilité au feu", "Annexe {ann} art.3.2 (tableau {tab})",
             "Tous les éléments structuraux du bâtiment (colonnes, poutres, planchers, parois portantes) doivent présenter la stabilité au feu R selon leur situation. BB: R30 (1 niveau au-dessus Ei), R60 (plusieurs niveaux), R60 (sous Ei). BM: R60 (au-dessus Ei), R120 (sous Ei y compris plancher Ei). Lors de la réception, une attestation d'un ingénieur en stabilité certifiant le respect de ces prescriptions sera transmise à la zone de secours."),
    "3.3":  ("Parois verticales intérieures — locaux nocturnes", "Annexe {ann} art.3.3",
             "Les parois verticales intérieures délimitant chaque logement doivent présenter au moins EI 60. La porte d'entrée de chaque logement doit présenter EI₁ 30."),
    "3.4":  ("Faux-plafonds dans chemins d'évacuation", "Annexe {ann} art.3.4.1 + 3.4.2",
             "Dans les chemins d'évacuation et les locaux accessibles au public, les faux-plafonds présentent EI 30 ou une stabilité au feu d'au moins ½h. Les parois RF sont prolongées dans l'espace entre le plafond et le faux-plafond. Si cet espace n'est pas sprinklé, il est divisé en volumes de 25m × 25m maximum par des écrans A1/A2-s1,d0 EI 30."),
    "3.5.1.1":("Façade simple paroi — jonction compartiment", "Annexe {ann} art.3.5.1.1",
             "Les montants constituant l'ossature de façade sont fixés à chaque niveau à l'ossature du bâtiment avec une résistance R 60. La liaison des parois de compartiment avec la façade présente au moins EI 60. Les joints entre les dalles et les parois verticales (façades) au droit des séparations horizontales entre compartiments présentent au moins EI 60."),
    "3.5.1.2":("Façades se faisant face — propagation entre compartiments", "Annexe {ann} art.3.5.1.2",
             "Afin d'éviter la propagation d'un incendie entre deux compartiments, soit la distance entre les parties de façade ne présentant pas E30 est au moins égale à (h+10)/2,5 × cosα mètres, soit le rayonnement thermique entre façades appartenant à différents compartiments ne dépasse pas 15 kW/m²."),
    "3.5.2":("Façades double paroi", "Annexe {ann} art.3.5.2",
             "La cavité d'une façade double paroi est interrompue par un élément présentant E 60 au droit de chaque paroi de compartiment et des planchers."),
    "4.1":  ("Parois entre compartiments", "Annexe {ann} art.4.1 (tableau {tab2})",
             "Les parois entre compartiments présentent au moins : EI 30 (bâtiment à un seul niveau au-dessus du plancher de Ei), EI 60 (bâtiment à plusieurs niveaux au-dessus de Ei ou en-dessous de Ei). La communication entre deux compartiments n'est autorisée qu'au moyen d'une porte EI₁ 30 à fermeture automatique."),
    "4.2.1":("Cages d'escalier — encloisonnement", "Annexe {ann} art.4.2.1",
             "Les escaliers qui relient plusieurs compartiments sont encloisonnés. Les principes de base énoncés au point 2 - compartimentage et évacuation - leur sont applicables."),
    "4.2.2.1":("Parois intérieures des cages d'escalier ≥ EI 60", "Annexe {ann} art.4.2.2.1",
             "Les parois intérieures des cages d'escaliers présentent au moins EI 60. Les parois intérieures délimitant chaque cage d'escalier doivent présenter EI 60."),
    "4.2.2.2":("Cages d'escalier — accès au niveau d'évacuation", "Annexe {ann} art.4.2.2.2",
             "Chaque cage d'escalier intérieure donne accès, directement ou par l'intermédiaire d'un chemin d'évacuation, à un niveau d'évacuation."),
    "4.2.2.3":("Communication compartiment/cage d'escalier — porte EI₁ 30", "Annexe {ann} art.4.2.2.3",
             "À chaque niveau, la communication entre le compartiment et la cage d'escalier est assurée par une porte EI₁ 30. Toutes les portes intérieures donnant dans chaque cage d'escalier doivent présenter EI₁ 30 à fermeture automatique."),
    "4.2.2.4":("Cages communes à plusieurs compartiments", "Annexe {ann} art.4.2.2.4",
             "Si une cage d'escalier est commune à plusieurs compartiments, chaque compartiment y a accès par une porte EI₁ 30 à fermeture automatique."),
    "4.2.2.5":("Cages sous-sol ≠ cages niveaux supérieurs", "Annexe {ann} art.4.2.2.5",
             "Les cages d'escalier desservant des niveaux en sous-sol ne sont pas dans le prolongement direct des cages desservant les niveaux au-dessus du plancher de Ei. Si elles sont superposées, elles sont séparées par des parois EI 60 et des portes EI₁ 30."),
    "4.2.2.6":("Baie de ventilation ≥ 1m² en tête de cage", "Annexe {ann} art.4.2.2.6",
             "Une baie de ventilation débouchant à l'air libre, d'une section de 1 m² minimum (0,5m² si superficie ≤ 300m² sur max 2 niveaux), est prévue à la partie supérieure de chaque cage d'escalier intérieure. La commande d'ouverture est manuelle, placée au niveau d'évacuation entre 1,4m et 2m de hauteur, à moins de 2m de la porte d'accès à la cage. Conforme NBN S21-208/3."),
    "4.2.3.1":("Escaliers — caractéristiques (R30, giron, hauteur, pente)", "Annexe {ann} art.4.2.3.1",
             "Les escaliers présentent R 30 (ou même conception qu'une dalle béton R30). Le giron des marches est en tout point ≥ 20cm. La hauteur des marches ne dépasse pas 18cm. La pente ne dépasse pas 75%. Mains courantes de chaque côté (une seule si largeur utile < 120cm)."),
    "4.2.3.2":("Largeur utile escaliers et paliers ≥ 0,80m", "Annexe {ann} art.4.2.3.2",
             "La largeur utile des escaliers et paliers est d'au moins 0,80m. Les volées et paliers d'une même cage d'escalier ne diffèrent pas de plus d'une unité de passage."),
    "4.3":  ("Escaliers extérieurs — classe A1", "Annexe {ann} art.4.3",
             "Les escaliers extérieurs donnent accès à un niveau d'évacuation. Aucune stabilité au feu n'est requise, mais le matériau est de classe A1."),
    "4.4.1.1":("Largeur utile chemins d'évacuation ≥ 0,80m", "Annexe {ann} art.4.4.1.1",
             "La largeur utile des chemins d'évacuation, des coursives, de leurs portes d'accès, de sortie ou de passage est de 0,80m au moins pour les chemins d'évacuation et les portes, et de 0,60m au moins pour les coursives."),
    "4.4.1.2":("Définition d'une sortie de compartiment", "Annexe {ann} art.4.4.1.2",
             "Est considéré comme une sortie d'un compartiment : une cage d'escaliers intérieure conforme au point 4.2, une cage d'escaliers extérieure conforme au point 4.3, un accès direct à ciel ouvert à un niveau d'évacuation, ou un chemin d'évacuation situé à un niveau d'évacuation conforme au point 4.4.2."),
    "4.4.1.3":("Portes — pas de verrouillage côté évacuation", "Annexe {ann} art.4.4.1.3",
             "Sur le parcours des chemins d'évacuation, les portes ne peuvent comporter de verrouillage empêchant leur utilisation dans le sens de l'évacuation. Toutes les portes situées sur le parcours des évacuations doivent pouvoir s'ouvrir facilement et immédiatement sans verrouillage."),
    "4.4.2":("Chemins d'évacuation au niveau Ei — EI 60", "Annexe {ann} art.4.4.2",
             "Les parois verticales intérieures des chemins d'évacuation situés au niveau d'évacuation présentent EI 60. Les portes y donnant accès présentent EI₁ 30 et sont à fermeture automatique."),
    "4.4.3":("Chemins d'évacuation autres niveaux — EI 30", "Annexe {ann} art.4.4.3",
             "Les parois verticales intérieures des chemins d'évacuation situés à un niveau autre que le niveau d'évacuation présentent EI 30. Les portes y donnant accès présentent EI₁ 30 et sont à fermeture automatique. Exception: si les compartiments ont une occupation exclusivement diurne et une superficie < 1250m²."),
    "4.4.4":("Sas — accès à la cage d'escalier (BM)", "Annexe 3/1 art.4.4.4",
             "En bâtiment moyen, si le nombre d'appartements par cage d'escalier et par niveau est supérieur à 6, l'accès à la cage d'escalier depuis le palier commun s'effectue via un sas (parois EI 60, deux portes EI₁ 30 FA)."),
    "4.5":  ("Signalisation — numéros de niveaux dans cages", "Annexe {ann} art.4.5",
             "Le numéro d'ordre de chaque niveau est indiqué de manière visible dans la cage d'escalier, à chaque accès à la cage d'escalier."),
    "5.1.1":("Local technique = compartiment distinct", "Annexe {ann} art.5.1.1",
             "Un local technique ou un ensemble de locaux techniques constitue un compartiment distinct. Les prescriptions relatives aux compartiments sont applicables : parois REI 60 ou EI 60, portes EI₁ 30 à fermeture automatique. Le local technique est distinct des caves."),
    "5.1.2.2":("Chaufferie — conception selon annexe 7 point 4", "Annexe {ann} art.5.1.2.2",
             "La conception, la construction et l'aménagement des chaufferies satisfont aux dispositions du point 4 de l'annexe 7."),
    "5.1.3":("Cabine haute tension", "Annexe {ann} art.5.1.3",
             "Les cabines haute tension constituent un compartiment distinct et satisfont aux prescriptions de la norme NBN C18-200."),
    "5.1.4":("Gaines verticales et horizontales (BM)", "Annexe 3/1 art.5.1.4",
             "En bâtiment moyen, les prescriptions de l'article 5.1.4 relatives aux gaines verticales et horizontales sont d'application."),
    "5.2.1":("Parking — généralités", "Annexe {ann} art.5.2.1",
             "Les éléments structuraux du parking présentent R 120. Si la superficie est > 625m², une installation d'évacuation des fumées et de la chaleur (EFC) est requise. Si la superficie est > 1250m², une installation de détection automatique d'incendie (DAI) est requise."),
    "5.2.4":("Parking — protection active si > 1250m²", "Annexe {ann} art.5.2.4",
             "Si la superficie du parking est supérieure à 1250m², une installation de détection automatique d'incendie conforme à la norme NBN S21-100 est obligatoire."),
    "6.4":  ("Ascenseurs — AR 09/03/2009", "AR 09/03/2009 + Annexe {ann} art.6.4",
             "Les prescriptions de l'AR du 09/03/2009 relatif à la sécurité des ascenseurs sont applicables. La gaine de l'ascenseur présente EI 60. Les portes palières présentent une résistance au feu appropriée. Un dispositif de rappel au niveau d'évacuation est prévu."),
    "6.5.1":("Installations électriques — RGIE", "Annexe {ann} art.6.5.1",
             "Les installations électriques de basse tension, de force motrice, d'éclairage et de signalisation sont conformes au Règlement Général sur les Installations Électriques (RGIE). Elles sont contrôlées par un organisme agréé par le SPF Économie avant leur mise en fonction. Une copie du rapport de contrôle sera remise à la zone de secours."),
    "6.5.2":("Canalisations circuits de sécurité (BM)", "Annexe 3/1 art.6.5.2",
             "En bâtiment moyen, les canalisations électriques alimentant des installations ou appareils dont le maintien en service est indispensable en cas de sinistre (éclairage de sécurité, alarme, détection, désenfumage) présentent PH 60 (câbles ≤ Ø20mm, section ≤ 2,5mm²) ou Rf 1h selon NBN 713-020."),
    "6.5.4":("Éclairage de sécurité ≥ 1 lux / 5 lux", "Annexe {ann} art.6.5.4",
             "Un éclairage de sécurité doit être prévu dans tous les locaux pour permettre l'évacuation sans danger du bâtiment (niveau d'éclairement minimal de 1 lux et 5 lux aux endroits dangereux). Il peut être fourni par des appareils autonomes branchés sur le circuit alimentant l'éclairage normal. La conformité aux normes NBN EN 1838, NBN EN 50172 et NBN EN 60598-2-22 est vérifiée par un organisme agréé. Une copie de l'attestation sera remise à la zone de secours."),
    "6.6":  ("Installations de gaz — NBN D 51-003", "Annexe {ann} art.6.6",
             "Les installations alimentées en gaz combustible répondent aux prescriptions de la norme NBN D 51-003. Une attestation certifiant la conformité des installations sera remise à la zone de secours. Les canalisations de gaz sont peintes en couleur jaune ocre (RAL 1004). Le branchement privé est équipé d'une vanne en trottoir signalée 'G'."),
    "6.7":  ("Installations aérauliques — art. 6.7.1 à 6.7.6", "Annexe {ann} art.6.7",
             "La conformité des éventuelles installations aérauliques aux prescriptions imposées par les articles 6.7.1 à 6.7.6 de l'annexe de l'AR du 7 juillet 1994 doit être vérifiée par un organisme indépendant. Une copie du PV de contrôle sera remise à la zone de secours."),
    "6.8.1":("Dispositifs d'extinction obligatoires", "Annexe {ann} art.6.8.1",
             "Les dispositifs d'extinction sont obligatoires. Leur type, nombre et emplacement sont déterminés en accord avec les services d'incendie selon les lignes directrices suivantes."),
    "6.8.4":("Alarme incendie — signal perceptible par tous", "Annexe {ann} art.6.8.4",
             "Il y a lieu d'équiper le bâtiment d'une installation d'alarme incendie constituée de boutons poussoirs sous vitre à briser ou à pousser actionnant une sirène audible de manière significative par tous les occupants en tout point du bâtiment. Les boutons sont placés à proximité des baies de passage vers l'extérieur, sur les paliers et dans les dégagements. L'installation fonctionne même en cas de coupure d'alimentation électrique."),
    "6.8.5.2":("Extincteurs portatifs ≥ 6kg ABC / 6L eau", "Annexe {ann} art.6.8.5.2",
             "Il y a lieu d'installer au minimum un extincteur de 6kg de poudre ABC ou de 6 litres à eau pulvérisée avec additif par 150m² de surface totale et par niveau. Il doit obligatoirement être porteur de la marque CE. Le label BENOR est vivement recommandé. Les extincteurs sont fixés au mur et signalés conformément à la réglementation."),
    "6.8.5.3":("Robinets d'incendie armés (RIA)", "Annexe 3/1 art.6.8.5.3",
             "Le bâtiment est équipé d'un réseau de robinets d'incendie armés conformes à la norme EN 671-1. La section de la colonne d'alimentation est calculée afin de respecter une pression d'au moins 2,5 bars et un débit d'au moins 72 L/min (3 RIA simultanément pendant 30 minutes). Les canalisations d'alimentation du réseau d'extinction sont peintes en rouge (RAL 3000)."),
    "6.8.5.4.2":("Borne incendie ≤ 100m / 200m", "Annexe {ann} art.6.8.5.4.2",
             "La présence d'une bouche ou d'une borne aérienne d'incendie à moins de 100 mètres (zone commerciale) ou 200 mètres (ailleurs) de l'entrée du bâtiment est indispensable. Si tel n'est pas le cas, il y a lieu de faire installer à proximité de l'entrée du bâtiment au moins une borne aérienne d'incendie conforme à la norme NBN S21-019."),
    "5/1 art.2":("Réaction au feu — type d'occupation (1/2/3)", "Annexe 5/1 art.2",
             "Le bâtiment est réparti dans les classes suivantes selon le risque lié au type d'occupation : type 1 (occupants non-autonomes), type 2 (occupants autonomes et dormants), type 3 (occupants autonomes et vigilants). Le maître d'ouvrage ou l'exploitant détermine le type et le communique à l'autorité compétente."),
    "5/1 tab.I":("Réaction au feu — locaux à risque accru", "Annexe 5/1 art.3 tableau I",
             "Les locaux techniques, parkings, salles des machines, gaines techniques et cuisines collectives présentent des revêtements de classe A2-s3,d2 (parois verticales), A2-s3,d0 (plafonds et faux-plafonds) et A2FL-s2 ou BFL-s2 (sols)."),
    "5/1 tab.II":("Réaction au feu — locaux selon type d'occupation", "Annexe 5/1 art.3 tableau II",
             "Les revêtements de parois intérieures, plafonds et sols dans les locaux respectent les classes de réaction au feu du tableau II de l'annexe 5/1 selon le type d'occupation. Lors de la réception des travaux, la preuve du respect de ces prescriptions (marquage CE, rapport de classement ou agrément BENOR/ATG + attestation de pose) sera transmise à la zone de secours."),
    "5/1 tab.III":("Réaction au feu — chemins d'évacuation et cages", "Annexe 5/1 art.4/1 tableau III",
             "Les revêtements de parois verticales, plafonds et sols dans les chemins d'évacuation et les cages d'escalier respectent les classes de réaction au feu du tableau III de l'annexe 5/1. Lors de la réception, attestations à transmettre à la zone de secours."),
    "5/1 art.6":("Réaction au feu — façades extérieures", "Annexe 5/1 art.6.1.1",
             "Les produits utilisés pour les revêtements de façades respectent les exigences du tableau V de l'annexe 5/1 : revêtement extérieur ≥ B-s3,d1, composants substantiels ≥ A2-s3,d0, montants ossature A1. Lors de la réception, attestations à transmettre."),
    "5/1 art.8":("Réaction au feu — toitures BROOF(t1)", "Annexe 5/1 art.8.1 + 8.3",
             "Les produits pour les revêtements des toitures présentent la classe BROOF(t1). Les revêtements des balcons, coursives et terrasses présentent la même réaction au feu. Les éléments suivants doivent être classés BROOF(t1) : étanchéité des toitures plates, couverture des versants, revêtement des balcons/terrasses, lanterneaux, panneaux solaires/photovoltaïques. Lors de la réception, la preuve du respect de ces prescriptions sera transmise à la zone de secours."),
    "AGW":  ("Détecteurs de fumée dans les logements", "AGW du 21/10/2004",
             "Chaque logement doit être équipé d'au moins un détecteur de fumée optique certifié BOSEC en parfait état de fonctionnement, par niveau comportant au moins une pièce d'habitation. Si la superficie d'un niveau est supérieure à 80m², au moins deux détecteurs sont requis pour ce niveau. Si l'installation d'au moins 4 détecteurs est nécessaire, ceux-ci doivent être interconnectés ou raccordés à une centrale de détection. L'installation est conforme à l'article 4 de l'AGW du 21/10/2004."),
}

def get_api_key():
    try:
        cfg = json.loads((BASE.parent / "config.json").read_text(encoding="utf-8"))
        k = cfg.get("api_key","")
        if k and "VOTRE_CLE" not in k and k.startswith("sk-"):
            return k
    except: pass
    return os.environ.get("ANTHROPIC_API_KEY","")

# ── Statique ──────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(BASE/"static","index.html")

@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory(BASE/"static",p)

# ── Analyse IA ────────────────────────────────────────────────


def _default_statuses(bat_type, hyp):
    """Statuts par défaut quand pas d'API: na pour les items non applicables, q pour le reste."""
    na_always = []
    if bat_type == "BB":
        na_always = ["4.4.4","5.1.4","6.5.2","6.8.5.3"]
    if not hyp.get("logements", True):
        na_always += ["3.3","AGW"]
    if not hyp.get("parking", False):
        na_always += ["5.2.1","5.2.4"]
    if not hyp.get("ascenseur", False):
        na_always += ["6.4"]
    if not hyp.get("gaz", False):
        na_always += ["6.6"]
    if not hyp.get("ss", False):
        na_always += ["4.2.2.5"]
    if not hyp.get("esc_ext", False):
        na_always += ["4.3"]

    all_ids = ["1.1","1.2","1.3","2.1","2.2.1","2.2.2","3.1","3.2","3.3","3.4",
               "3.5.1.1","3.5.1.2","3.5.2","4.1","4.2.1","4.2.2.1","4.2.2.2",
               "4.2.2.3","4.2.2.4","4.2.2.5","4.2.2.6","4.2.3.1","4.2.3.2",
               "4.3","4.4.1.1","4.4.1.2","4.4.1.3","4.4.2","4.4.3","4.4.4","4.5",
               "5.1.1","5.1.2.2","5.1.3","5.1.4","5.2.1","5.2.4","6.4","6.5.1",
               "6.5.2","6.5.4","6.6","6.7","6.8.1","6.8.4","6.8.5.2","6.8.5.3",
               "6.8.5.4.2","5/1 art.2","5/1 tab.I","5/1 tab.II","5/1 tab.III",
               "5/1 art.6","5/1 art.8","AGW"]

    statuses = {}
    # Toujours NA
    always_na = ["3.5.2","5.1.2.2","5.1.3"]
    for pid in all_ids:
        if pid in always_na or pid in na_always:
            statuses[pid] = "na"
        else:
            statuses[pid] = "q"
    return statuses

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    images = data.get("images",[])
    # Accepter context ou project_info
    ctx = data.get("context", data.get("project_info",{}))
    hyp = ctx.get("hypotheses", ctx)
    bat_type = ctx.get("type_batiment","BB")

    api_key = get_api_key()
    print(f"  /api/analyze: {len(images)} image(s) reçue(s), type={bat_type}, api={'OK' if api_key else 'MANQUANTE'}")

    # Fallback sans API: tout passe en "q" sauf les items non applicables selon les hypothèses
    if not api_key:
        defaults = _default_statuses(bat_type, hyp)
        return jsonify({"statuses": defaults, "type_batiment": bat_type,
                        "hauteur_h": "", "observations": "Analyse manuelle requise (clé API non configurée)",
                        "error_api": True})

    prompt_file = ENGINE_DIR / "analyze_prompt.txt"
    base_prompt = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

    context = f"""
Projet: {ctx.get('nom', data.get('nom',''))}
Type bâtiment: {bat_type}
Hypothèses: logements={hyp.get('logements',True)}, parking={hyp.get('parking',False)}, ascenseur={hyp.get('ascenseur',False)}, gaz={hyp.get('gaz',False)}, sous-sol={hyp.get('ss',False)}
"""

    content = []
    import base64 as _b64, tempfile as _tmp, os as _os
    for img in images[:5]:
        b64 = img.get("b64",""); mime = img.get("mime_type","image/jpeg")
        if not b64: continue
        if mime == "application/pdf":
            pdf_bytes = _b64.b64decode(b64)
            converted = False
            # Méthode 1: pymupdf
            try:
                import fitz
                with _tmp.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
                    t.write(pdf_bytes); tp = t.name
                doc = fitz.open(tp)
                for page in list(doc)[:3]:
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5))
                    content.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":_b64.b64encode(pix.tobytes("jpeg")).decode()}})
                doc.close(); _os.unlink(tp)
                print(f"  PDF→images via pymupdf ({min(len(doc),3)} pages)")
                converted = True
            except: pass
            # Méthode 2: pdftoppm
            if not converted:
                try:
                    import subprocess, glob
                    with _tmp.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
                        t.write(pdf_bytes); tp = t.name
                    op = tp.replace(".pdf","_pg")
                    subprocess.run(["pdftoppm","-jpeg","-r","100","-f","1","-l","3",tp,op],capture_output=True,timeout=30)
                    for pp in sorted(glob.glob(op+"*.jpg"))[:3]:
                        content.append({"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":_b64.b64encode(open(pp,"rb").read()).decode()}})
                        _os.unlink(pp)
                    _os.unlink(tp); converted = True
                    print("  PDF→images via pdftoppm")
                except: pass
            # Méthode 3: document Claude
            if not converted:
                content.append({"type":"document","source":{"type":"base64","media_type":"application/pdf","data":b64}})
                print("  PDF envoyé comme document")
        else:
            content.append({"type":"image","source":{"type":"base64","media_type":mime,"data":b64}})

    content.append({"type":"text","text": context + "\n\n" + base_prompt})

    try:
        import anthropic
        http_client = httpx.Client(verify=False)
        client = anthropic.Anthropic(api_key=api_key, http_client=http_client)
        msg = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2000,
            messages=[{"role":"user","content":content}]
        )
        text = re.sub(r"```json|```","",msg.content[0].text).strip()
        result = json.loads(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# ── Génération rapport texte ──────────────────────────────────

@app.route("/api/generate_text", methods=["POST"])
def generate_text():
    """Génère le texte complet de la section 6 du rapport."""
    api_key = get_api_key()
    data = request.json
    zone = data.get("zone","ZSBW")
    bat_type = data.get("type_batiment","BB").upper()
    ann = "2/1" if bat_type == "BB" else "3/1"
    tab = "2.1" if bat_type == "BB" else "3.1"
    tab2 = "2.3" if bat_type == "BB" else "3.3"

    nok_ids = data.get("nok_ids",[])
    q_ids = data.get("q_ids",[])
    project = data.get("project",{})

    # Construire les points du rapport
    points = []
    num = 1

    # Points non conformes
    for pid in nok_ids:
        if pid in ARTICLES:
            titre, art_ref, texte = ARTICLES[pid]
            art_ref = art_ref.replace("{ann}",ann).replace("{tab}",tab).replace("{tab2}",tab2)
            texte_final = texte
            # Ajouter le détail spécifique si fourni
            detail = data.get("points_nok_details",{}).get(pid,"")
            if detail:
                texte_final += f"\n\n{detail}"
            points.append({"num":num, "id":pid, "titre":titre, "ref":art_ref, "texte":texte_final, "status":"nok"})
            num += 1

    # Points avec info manquante
    for pid in q_ids:
        if pid in ARTICLES:
            titre, art_ref, texte = ARTICLES[pid]
            art_ref = art_ref.replace("{ann}",ann).replace("{tab}",tab).replace("{tab2}",tab2)
            texte_final = texte + "\n\nN'apparaît pas sur les plans transmis. Des informations complémentaires sont demandées à l'architecte."
            points.append({"num":num, "id":pid, "titre":titre, "ref":art_ref, "texte":texte_final, "status":"q"})
            num += 1

    return jsonify({"points": points, "annexe": ann, "bat_type": bat_type})

# ── Génération .docx ──────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    zone = data.get("zone","ZSBW")
    bat_type = data.get("type_batiment","BM").upper()

    tmpl = TEMPLATES.get(zone,{}).get(bat_type)
    if not tmpl or not Path(tmpl).exists():
        return jsonify({"error":f"Template {zone}/{bat_type} introuvable"}), 404

    try:
        # Lire le template docx (= zip)
        with open(str(tmpl), "rb") as f:
            tmpl_bytes = f.read()

        import zipfile as zf, io
        # Ouvrir le template
        tmpl_zip = zf.ZipFile(io.BytesIO(tmpl_bytes))
        doc_xml = tmpl_zip.read("word/document.xml").decode("utf-8")

        # Remplir les champs
        now = datetime.now().strftime("%d/%m/%Y")
        fields = {
            "[DOS_DOS_NAME]":      data.get("nom",""),
            "[DOS_DOS_STREET]":    data.get("adresse",""),
            "[DOS_DOS_ZIPCODE]":   "",
            "[DOS_DOS_TOWN]":      data.get("commune",""),
            "[DOS_DOS_CODE]":      data.get("ref_dossier",""),
            "[DOS_DOS_TYPE]":      data.get("fonction",""),
            "[DOS_OWN_NAME]":      data.get("mo",""),
            "[DOS_OWN_STREET]":    "",
            "[DOS_OWN_ZIPCODE]":   "",
            "[DOS_OWN_TOWN]":      "",
            "[MIS_REFNR]":         data.get("ref_dossier",""),
            "[MIS_DATE_REG]":      data.get("vref",""),
            "[DOC_DATE]":          now,
            "[MIS_DEP_NAME]":      data.get("commune",""),
            "[MIS_PREVENTIONIST]": data.get("agent",""),
            "[MIS_PREV_EMAIL]":    data.get("prev_email",""),
            "[MIS_PREV_FBNAME]":   data.get("commune",""),
            "[MIS_TYPE]":          data.get("mission","Avis sur plan"),
            "[MIS_ARCH_NAME]":     data.get("architecte",""),
            "[MIS_REQ_NAME]":      data.get("mo",""),
        }
        for k, v in fields.items():
            doc_xml = doc_xml.replace(k, str(v))

        # Supprimer surlignages
        doc_xml = re.sub(r'<w:highlight w:val="[^"]+"/>', "", doc_xml)

        # Créer le nouveau docx
        out_buf = io.BytesIO()
        with zf.ZipFile(out_buf, "w", zf.ZIP_DEFLATED) as out_zip:
            for item in tmpl_zip.infolist():
                if item.filename == "word/document.xml":
                    out_zip.writestr(item, doc_xml.encode("utf-8"))
                else:
                    out_zip.writestr(item, tmpl_zip.read(item.filename))
        tmpl_zip.close()

        # Sauvegarder dans projets/
        safe = re.sub(r"[^\w\-]","_", data.get("nom","rapport"))[:40]
        out_name = f"PreventFire_{zone}_{bat_type}_{safe}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
        out_path = PROJETS_DIR / out_name
        out_path.write_bytes(out_buf.getvalue())

        return send_file(
            str(out_path), as_attachment=True, download_name=out_name,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        print(f"  /api/generate ERREUR: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/test_api")
def test_api():
    """Test simple de connexion API sans image."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"ok": False, "error": "Cle API manquante"})
    try:
        import httpx
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 50,
                  "messages": [{"role": "user", "content": "Dis juste OK"}]},
            verify=False, timeout=30.0
        )
        print(f"  /api/test_api status: {resp.status_code}")
        if resp.status_code == 200:
            return jsonify({"ok": True, "reponse": resp.json()["content"][0]["text"]})
        else:
            return jsonify({"ok": False, "status": resp.status_code, "body": resp.text[:200]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


def compress_for_api(images_raw, max_total_kb=800):
    """Compresse les images/PDFs - max 800Ko total, 1 page PDF."""
    import base64, io
    content = []
    total_kb = 0

    for img in images_raw[:2]:
        b64 = img.get("b64", "")
        mime = img.get("mime_type", "image/jpeg")
        if not b64:
            continue

        raw_bytes = base64.b64decode(b64)
        raw_kb = len(raw_bytes) // 1024
        print(f"  Fichier: {img.get('name','?')} | {raw_kb}Ko")

        if mime == "application/pdf":
            try:
                import fitz
                doc = fitz.open(stream=raw_bytes, filetype="pdf")
                # 1 seule page, résolution très basse (0.5 = 36dpi)
                page = doc[0]
                mat = fitz.Matrix(0.5, 0.5)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("jpeg")
                doc.close()
                kb = len(img_bytes) // 1024
                print(f"    PDF->JPEG page 1: {kb}Ko")
                if total_kb + kb <= max_total_kb:
                    total_kb += kb
                    content.append({"type": "image", "source": {
                        "type": "base64", "media_type": "image/jpeg",
                        "data": base64.b64encode(img_bytes).decode()}})
                continue
            except Exception as e:
                print(f"  Erreur PDF: {e}")
                continue

        # Image: réduire si nécessaire
        try:
            from PIL import Image
            img_obj = Image.open(io.BytesIO(raw_bytes))
            img_obj.thumbnail((800, 800), Image.LANCZOS)
            buf = io.BytesIO()
            img_obj.save(buf, format="JPEG", quality=60)
            raw_bytes = buf.getvalue()
            mime = "image/jpeg"
        except Exception:
            pass

        kb = len(raw_bytes) // 1024
        if total_kb + kb <= max_total_kb:
            total_kb += kb
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": mime,
                "data": base64.b64encode(raw_bytes).decode()}})

    print(f"  Total: {total_kb}Ko, {len(content)} bloc(s)")
    return content

@app.route("/api/extract", methods=["POST"])
def extract_info():
    """Extrait les infos administratives des plans via Claude."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "Clé API non configurée"}), 400

    data = request.json
    images = data.get("images", [])

    content = compress_for_api(images)
    if not content:
        return jsonify({"error": "Aucun fichier valide ou conversion echouee"}), 400

    prompt = """Tu es expert en prevention incendie belge.
Analyse ces plans d architecture et extrait les informations administratives du projet.

Retourne UNIQUEMENT ce JSON sans markdown:
{
  "nom_projet": "denomination du projet",
  "type_mission": "Avis sur plan - permis d urbanisme",
  "description_mission": "description complete de la mission",
  "demandeur": "nom de la societe ou du demandeur",
  "representant": "nom du representant",
  "adresse": "adresse complete du batiment",
  "commune": "nom de la commune",
  "conditions_acces": "distance au poste de secours le plus proche",
  "ressources_eau": "Reseau public.",
  "vref": "reference precedente du dossier si visible",
  "nref": "nouvelle reference si visible",
  "architecte": "nom et adresse du bureau d architectes",
  "plans_recus": "liste des plans recus avec echelles",
  "antecedents": "Neant. ou description",
  "type_batiment": "BB ou BM",
  "hauteur_h": "calcul de la hauteur h si visible",
  "niveaux": {
    "ss": "description sous-sol si present",
    "rdc": "description rez-de-chaussee",
    "r1": "description 1er etage",
    "r2": "description 2eme etage si present",
    "r3": "",
    "toit": "description toiture"
  },
  "chauffage": "type de chauffage si indique",
  "hypotheses": {
    "logements": true,
    "commerces": false,
    "ss": false,
    "parking": false,
    "ascenseur": false,
    "gaz": false
  }
}"""

    content.append({"type": "text", "text": prompt})

    try:
        import httpx, re as _re
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": content}]
            },
            verify=False,
            timeout=30.0
        )
        print(f"  /api/extract status: {resp.status_code}")
        data = resp.json()
        text = data["content"][0]["text"]
        text = _re.sub(r"```json|```", "", text).strip()
        result = json.loads(text)
        return jsonify(result)
    except Exception as e:
        print(f"  /api/extract ERREUR: {type(e).__name__}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze_plans", methods=["POST"])
def analyze_plans():
    """Analyse les plans et retourne les statuts AR via Claude."""
    api_key = get_api_key()
    if not api_key:
        return jsonify({"error": "Clé API non configurée"}), 400

    data = request.json
    images = data.get("images", [])
    project_info = data.get("project_info", {})

    content = compress_for_api(images)
    if not content:
        return jsonify({"error": "Aucun fichier valide ou conversion echouee"}), 400

    bat = project_info.get("type_batiment", "BB")
    nom = project_info.get("nom", "")
    hyp = project_info.get("hypotheses", {})
    ids = project_info.get("ids", [])

    ids_str = "{\n" + ",\n".join([f'"{i}":"ok|nok|q"' for i in ids]) + "\n}"

    # Determiner les NA automatiquement selon hypotheses
    auto_na = set()
    if bat == "BB":
        auto_na.update(["4.4.4","5.1.4","6.5.2","6.8.5.3"])
    if not hyp.get("ss", False):
        auto_na.add("4.2.2.5")
    if not hyp.get("ascenseur", False):
        auto_na.add("6.4")
    if not hyp.get("gaz", False):
        auto_na.add("6.6")
    if not hyp.get("parking", False):
        auto_na.update(["5.2.1","5.2.4"])
    if not hyp.get("logements", True):
        auto_na.update(["3.3","AGW"])

    # IDs a analyser = tous sauf les NA automatiques
    ids_to_analyze = [i for i in ids if i not in auto_na]

    # Construire ids_str uniquement pour les IDs a analyser
    ids_str_analyze = "{\n" + ",\n".join([f'"{i}":"ok|nok|q"' for i in ids_to_analyze]) + "\n}"

    prompt = f"""Tu es agent de prevention incendie belge expert en AR 07.07.1994.
Projet: {nom} | Type: {bat} | Annexe: {"2/1" if bat == "BB" else "3/1"}

REGLE FONDAMENTALE - Ce que tu PEUX lire sur les plans architecturaux:
- Dimensions des espaces (largeurs couloirs, escaliers, compartiments)
- Presence/absence elements (cage escalier, baie ventilation, sas, parking, sous-sol)
- Programme des niveaux et superficies
- Mode de chauffage si indique sur les plans
- Hauteur du batiment si cotee
- Annotations specifiques de l architecte

Ce que tu NE PEUX PAS determiner (mettre "q" systematiquement):
- Resistances au feu (EI, REI, R) : jamais annotees sur plans AVP
- Installations electriques, alarme, extincteurs, detecteurs
- Materiaux de construction et leurs classes de reaction au feu
- Conformite des elements structuraux

REGLES DE COTATION:
- "ok" = element clairement visible ET conforme sur les plans
- "nok" = element clairement visible ET probleme detecte (ex: largeur < 80cm visible, baie ventilation absente alors qu elle devrait etre presente)
- "q" = non visible ou non determinable depuis les plans

ARTICLES OU TU PEUX VRAIMENT STATUER:
- 1.1: Y a-t-il une voie d acces visible? Largeur suffisante visible?
- 1.3: La distance avec les batiments voisins est-elle visible sur le plan masse?
- 2.1: La superficie des compartiments est-elle calculable depuis les plans?
- 2.2.1: Le nombre de sorties est-il visible?
- 4.2.1: Y a-t-il une cage d escalier encloisonnee visible?
- 4.2.2.6: Y a-t-il une baie de ventilation en tete de cage visible?
- 4.2.3.2: La largeur des escaliers est-elle cotee et suffisante (>=80cm)?
- 4.3: Y a-t-il un escalier exterieur? Le materiau est-il indique?
- 4.4.1.1: Les largeurs des couloirs/portes sont-elles cotees? >= 80cm?
- 4.4.4: BM seulement - y a-t-il un sas visible entre hall et cage?
- 5.1.1: Le local technique est-il separe des caves?
- 5.2.1: Y a-t-il un parking? Superficie estimable?
- 6.4: Y a-t-il un ascenseur visible sur les plans?

Pour tous les autres articles: mettre "q" directement.

Retourne UNIQUEMENT ce JSON sans markdown:
{{"type_batiment":"BB ou BM","hauteur_h":"cote visible ou vide","statuses":{ids_str_analyze},"observations":"elements importants notes sur les plans"}}"""

    content.append({"type": "text", "text": prompt})

    try:
        import httpx, re as _re
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": content}]
            },
            verify=False,
            timeout=30.0
        )
        print(f"  /api/analyze_plans status: {resp.status_code}")
        data = resp.json()
        text = data["content"][0]["text"]
        text = _re.sub(r"```json|```", "", text).strip()
        result = json.loads(text)
        # Ajouter les NA automatiques au résultat
        if "statuses" in result:
            for aid in auto_na:
                result["statuses"][aid] = "na"
        return jsonify(result)
    except Exception as e:
        print(f"  /api/analyze_plans ERREUR: {type(e).__name__}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/projets")
def list_projets():
    out = []
    for f in sorted(PROJETS_DIR.glob("*.docx"), key=lambda x: x.stat().st_mtime, reverse=True):
        out.append({"nom":f.name,"taille":f"{f.stat().st_size//1024} Ko",
                    "date":datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")})
    return jsonify(out)

@app.route("/api/projets/<nom>")
def dl_projet(nom):
    p = PROJETS_DIR/nom
    return send_file(str(p),as_attachment=True,download_name=nom) if p.exists() \
           else (jsonify({"error":"non trouvé"}),404)

@app.route("/api/config")
def cfg_route():
    try:
        c = json.loads((BASE.parent/"config.json").read_text(encoding="utf-8"))
        api_key = get_api_key()
        c["api_configured"] = bool(api_key)
        c["api_raw"] = api_key  # Clé brute pour appel direct depuis le navigateur
        c["api_key"] = "***"
        zones = [z for z,types in TEMPLATES.items() if any(Path(p).exists() for p in types.values())]
        c["zones_disponibles"] = zones
        return jsonify(c)
    except:
        return jsonify({"api_configured":False,"api_raw":"","zones_disponibles":["ZSBW","NAGE","DINAPHI"]})

@app.route("/api/debug")
def debug():
    return jsonify({
        "python":sys.version,"base":str(BASE),
        "api_configured":bool(get_api_key()),
        "templates":{z:{t:str(p)+" [OK]" if Path(p).exists() else "[MANQUANT]" for t,p in types.items()} for z,types in TEMPLATES.items()},
    })

# ── Lancement ─────────────────────────────────────────────────

def _open():
    import time; time.sleep(1.5)
    webbrowser.open("http://localhost:5174")

if __name__ == "__main__":
    print("="*50)
    print("  PreventFire Pro v3.5")
    print(f"  API : {'OK' if get_api_key() else 'NON CONFIGURÉE'}")
    for zone,types in TEMPLATES.items():
        for t,p in types.items():
            print(f"  {zone}/{t} : {'OK' if Path(p).exists() else 'MANQUANT'}")
    print("  http://localhost:5174")
    print("="*50)
    threading.Thread(target=_open,daemon=True).start()
    app.run(host="127.0.0.1",port=5174,debug=False)
