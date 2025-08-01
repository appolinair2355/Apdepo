# Telegram Bot - Pack de Déploiement Render.com

## Description
Bot Telegram optimisé pour le déploiement sur Render.com avec système de prédictions automatiques pour les jeux de cartes.

## Configuration Render.com

### Variables d'Environnement Requises
```
BOT_TOKEN=7870922727:AAGXEEWNB7zz8M_k8WEyfEmEDMKxoFAaBwM
WEBHOOK_URL=https://telegram-deployment-bot.onrender.com
PORT=10000 (automatiquement configuré par Render.com)
```

### Configuration Service
- **Type**: Web Service
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload`
- **Health Check**: `/health`

## Fonctionnalités

### Système de Prédiction Automatique
- Détecte 3 costumes différents dans n'importe quelle parenthèse
- Génère prédiction pour le jeu suivant (+1)
- Format: "🔵[N+1] 🔵3K: statut :⏳"

### Système de Vérification
- Vérifie les prédictions existantes automatiquement
- Met à jour les statuts selon le décalage temporel
- Statuts: ✅0️⃣ ✅1️⃣ ✅2️⃣ ✅3️⃣ ou ⭕⭕

### Gestion Rate Limiting
- Retry automatique en cas de limite API Telegram
- Protection contre les erreurs 429

## Déploiement

1. Créer un nouveau service sur Render.com
2. Connecter ce repository ou uploader le ZIP
3. Configurer les variables d'environnement
4. Déployer

## Test après Déploiement

1. Vérifier `/health` pour la santé du service
2. Consulter les logs pour "✅ Webhook configuré avec succès"
3. Tester les commandes du bot
4. Vérifier les prédictions automatiques sur messages édités

## Support

Canal cible: Baccarat Kouamé (-1002682552255)
Fonctionnement: Webhook uniquement, messages édités avec ✅ ou 🔰