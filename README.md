# PreventFire

Générateur de rapports de prévention incendie — référentiel **AR 07/07/1994**
(Annexe 2/1 Bâtiments Bas / Annexe 3/1 Bâtiments Moyens).

Application autonome en deux parties :

- **frontend/** — interface React (Vite). Workflow 6 étapes, checklist adaptée au
  type de bâtiment, rapport avec avis officiel et impression PDF.
- **backend/** — serveur Flask qui détient la clé API, **compresse les plans PDF
  via PyMuPDF** et appelle l'API Anthropic pour la pré-analyse.

```
preventfire/
├── backend/
│   ├── app.py            # endpoint /api/analyze + compression pymupdf
│   ├── requirements.txt
│   └── .env.example      # → copier en .env et y mettre la clé
└── frontend/
    ├── src/
    │   ├── PreventFire.jsx
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── .env.example      # → copier en .env (URL du backend)
```

---

## Démarrage

### 1. Backend (Flask)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # puis éditez .env : ANTHROPIC_API_KEY=sk-ant-...
python app.py                    # http://localhost:5000
```

Vérification : `http://localhost:5000/api/health` doit renvoyer `"key_loaded": true`.

### 2. Frontend (Vite + React)

```bash
cd frontend
npm install
cp .env.example .env             # VITE_API_URL=http://localhost:5000
npm run dev                      # http://localhost:5173
```

Ouvrez **http://localhost:5173**. Les deux serveurs doivent tourner en parallèle.

---

## Utilisation depuis un autre PC / téléphone

Sur le réseau local, lancez le backend avec `host=0.0.0.0` (déjà configuré) puis,
dans `frontend/.env`, remplacez `localhost` par l'IP de la machine serveur
(ex. `VITE_API_URL=http://192.168.1.20:5000`). Les autres appareils ouvrent
`http://192.168.1.20:5173`.

Pour un déploiement durable : `npm run build` génère un dossier `dist/` statique
que le Flask (ou un Nginx) peut servir.

---

## Réglages utiles (backend/.env)

| Variable | Rôle | Défaut |
|---|---|---|
| `ANTHROPIC_API_KEY` | Clé API (obligatoire) | — |
| `ANTHROPIC_MODEL` | Modèle utilisé | `claude-sonnet-4-6` |
| `MAX_PDF_PAGES` | Pages du plan envoyées au modèle | `4` |
| `PDF_RENDER_DPI` | Résolution de rendu (↓ = plus léger) | `120` |
| `CORS_ORIGIN` | Origine autorisée | `http://localhost:5173` |

---

## Référentiel de la checklist

Les points de contrôle, références d'articles et valeurs (R, EI, distances…) sont
repris du **texte coordonné officiel de l'AR du 7 juillet 1994** (SPF Intérieur,
Sécurité civile, version coordonnée au 20 mai 2022) et du **tableau comparatif
officiel des annexes 2/1 (BB), 3/1 (BM) et 4/1 (BE)**. Les indications basculent
automatiquement entre les valeurs BB et BM selon le type sélectionné.

Couverture actuelle : Annexes 1 (terminologie), 2/1 (BB) et 3/1 (BM) sur les
6 chapitres, plus renvois à l'Annexe 5 (réaction au feu) et à l'Annexe 7
(dispositions communes : traversées, parkings, chaufferies). À intégrer
ultérieurement : l'Annexe 6 (bâtiments industriels) comme 3ᵉ type de bâtiment.

> ⚠️ Restitution d'aide à la rédaction : vérifiez toujours les références au
> regard du texte en vigueur avant transmission officielle.

## À faire ensuite (idées pour Claude Code)

- Réintégrer les raffinements de **PreventFire Pro v5.8** : déploiement USB portable,
  vue « manquements uniquement » persistée, modèles de rapport par zone.
- Export **.docx** au modèle de la Zone de secours (au lieu de l'impression PDF).
- Aligner les **références d'articles** (actuellement indicatives) sur vos citations
  PREV2 réelles, article par article.
- Persistance des dossiers (SQLite) pour reprendre une inspection en cours.

> ⚠️ Les références d'articles de la checklist sont des gabarits indicatifs et
> doivent être validées au regard du texte en vigueur avant toute transmission officielle.
