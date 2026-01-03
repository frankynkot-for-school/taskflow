# TaskFlow 🚀

Application web complète de **gestion avancée des tâches** développée avec Django REST Framework et React.

## 📋 Fonctionnalités

### Gestion des Projets
- ✅ Création, modification et suppression de projets
- ✅ Ajout/retrait de membres aux projets
- ✅ Statistiques et progression par projet
- ✅ Vue d'ensemble avec indicateurs visuels

### Gestion des Tâches
- ✅ CRUD complet des tâches
- ✅ 4 statuts : À faire, En cours, En révision, Terminé
- ✅ 4 niveaux de priorité : Basse, Moyenne, Haute, Urgente
- ✅ Dates d'échéance avec alertes visuelles
- ✅ Attribution à des membres
- ✅ Filtres avancés et recherche

### Sous-tâches
- ✅ Ajout de sous-tâches aux tâches principales
- ✅ Suivi de progression automatique
- ✅ Basculement de l'état de complétion

### Tags et Catégories
- ✅ Système de tags colorés
- ✅ Filtrage par tags

### Commentaires & Pièces jointes
- ✅ Ajout de commentaires sur les tâches
- ✅ Upload de fichiers

### Tableau de bord
- ✅ Vue d'ensemble avec graphiques interactifs
- ✅ Tâches en retard et à venir
- ✅ Mes tâches assignées

### Authentification
- ✅ Inscription et connexion JWT
- ✅ Rafraîchissement automatique des tokens

## 🛠️ Technologies

### Backend
- **Django 5.0** - Framework web Python
- **Django REST Framework** - API REST
- **SimpleJWT** - Authentification JWT
- **django-filter** - Filtres avancés
- **drf-yasg** - Documentation Swagger/ReDoc

### Frontend
- **React 18** - Bibliothèque UI
- **Vite** - Build tool moderne
- **Tailwind CSS** - Styling utility-first
- **Zustand** - State management
- **React Router v6** - Navigation
- **Axios** - Requêtes HTTP
- **Recharts** - Graphiques
- **Framer Motion** - Animations

## 📁 Structure du Projet

```
taskflow/
├── backend/
│   ├── config/          # Configuration Django
│   ├── api/             # API REST (models, views, serializers)
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # Composants réutilisables
│   │   ├── pages/       # Pages de l'application
│   │   ├── services/    # Services API
│   │   └── store/       # State management
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Installation

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend : `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📝 Fonctionnalités

- ✅ Gestion de projets
- ✅ Création et organisation de tâches
- ✅ Système de priorités et statuts
- ✅ Assignation d'utilisateurs
- ✅ Commentaires et pièces jointes
- ✅ Tags et catégories
- ✅ Vue Kanban
- ✅ Calendrier
- ✅ Notifications
- ✅ Recherche avancée

## 👥 Auteur

Franky Nkot

## 📄 License

MIT
