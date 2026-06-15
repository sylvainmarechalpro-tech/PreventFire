# PreventFire Pro — Guide d'installation

## Installation (une seule fois)

1. Double-cliquez sur **install.bat**
   - Installe Python automatiquement si nécessaire
   - Installe les librairies requises
   - Ouvre config.json pour configuration

2. Dans **config.json**, renseignez votre clé API Anthropic :
   - Allez sur https://console.anthropic.com
   - Créez une clé API (Settings → API Keys)
   - Collez-la dans le fichier : `"api_key": "sk-ant-..."`

## Utilisation quotidienne

1. Double-cliquez sur **preventfire.bat**
2. L'interface s'ouvre dans votre navigateur
3. Uploadez vos plans → Analysez → Générez le rapport

## Structure des fichiers

```
PreventFire/
├── preventfire.bat     ← LANCER ICI
├── install.bat         ← Installation (1 seule fois)
├── config.json         ← Configuration (clé API, agent)
├── app/
│   ├── server.py       ← Serveur local (ne pas modifier)
│   ├── engine/         ← Moteur de génération
│   ├── templates/      ← Templates Word officiels
│   │   ├── ZSBW_BB.docx
│   │   ├── ZSBW_BM.docx
│   │   ├── NAGE_BB.dotm
│   │   └── NAGE_BM.dotm
│   └── static/         ← Interface web
└── projets/            ← Rapports générés (sauvegardés ici)
```

## Ajouter une zone de secours

Pour ajouter une nouvelle zone (ex: SIAMU, Liège) :
1. Placez les fichiers .docx/.dotm dans app/templates/
   Nommage : `{ZONE}_{TYPE}.docx` (ex: SIAMU_BB.docx)
2. Ajoutez la zone dans config.json : `"zones_actives": ["ZSBW", "NAGE", "SIAMU"]`
3. Relancez preventfire.bat

## Configuration clé API

La clé API Anthropic est nécessaire pour l'analyse automatique des plans.
Sans clé API, vous pouvez toujours :
- Saisir manuellement les données projet
- Cocher manuellement les flags
- Générer le .docx officiel

Sans clé API, l'analyse IA des plans est désactivée.

## En cas de problème

- **"Python non trouvé"** → Relancez install.bat
- **"Erreur d'analyse"** → Vérifiez la clé API dans config.json
- **"Erreur de génération"** → Vérifiez que les templates sont dans app/templates/
- **L'interface ne s'ouvre pas** → Ouvrez manuellement http://localhost:5174

## Support

Rapports générés sauvegardés dans le dossier **projets/**
