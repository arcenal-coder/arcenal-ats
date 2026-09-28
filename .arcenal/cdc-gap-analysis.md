# ARCenal ATS — écarts V1 constatés

Date d'observation : 2026-09-28. Source : CDC V1, code du commit `fb86898` et écrans de référence fournis.

| Domaine | État | Preuve et écart concret |
| --- | --- | --- |
| Installation, PostgreSQL, service et chemin `/ats` | OK et vérifié | Installation Onyx, mise à jour `0.1.0~ynh15`, santé et portail public ont répondu. |
| Portail public, offres, candidature et CV privé | Présent mais incomplet | Dépôt, confirmation, confidentialité et route protégée existent ; recherche, filtres, mentions configurables, conservation et indexation manquent. |
| Offres | Présent mais incomplet | Brouillon et publication existent ; modification, archivage, recherche, filtres et tableau de gestion complet sont absents. |
| Candidatures et pipeline | Présent mais incomplet | Étape et note existent, mais l'interface est un tableau : pas de Kanban, de détail candidat, d'historique lisible, d'étiquettes, de compteur ou de filtres. |
| Vivier | Présent mais incomplet | Une liste et une API de recherche incomplète existent ; pas de filtres métier, étiquettes, réactivation ni rattachement à une offre. |
| Documents | Présent mais incomplet | Stockage hors web et téléchargement contrôlé existent ; le dossier candidat ne liste pas les documents ni leur historique. |
| Paramètres et personnalisation | Absent | Pas de configuration entreprise, apparence, recrutement, indexation ou conservation en base et aucune interface d'administration. |
| Utilisateurs et rôles | Absent | Tout utilisateur SSOwat ayant accès à la zone interne peut agir ; aucun rôle applicatif recruteur/administrateur. |
| RGPD | Présent mais incomplet | Consentement daté existe ; version du texte, durée configurable, export et effacement contrôlés sont absents. |
| Journal d'activité | Présent mais incomplet | La table reçoit quelques événements ; aucun écran d'audit ni détail ancien/nouvel état. |
| ARCenal Agent / AACP/1 | Présent mais incomplet | Découverte statique de capacités seulement ; pas de configuration, authentification, révocation, journal, connecteur d'appel ni validation humaine. |
| Diffusion des annonces | Absent | Aucun connecteur de diffusion réel ni configuration. Aucune intégration externe ne doit être affichée comme active sans contrat et identifiants valides. |
| Tests fonctionnels | Présent mais incomplet | Tests purs sur domaine, stockage et rendu ; absence de tests d'intégration d'autorisation, RGPD, détail candidat et connecteur indisponible. |

## Priorité de rattrapage

1. Rôles applicatifs, données de réglages et contrôle d'accès : fondation de toutes les actions recruteur/administrateur.
2. Fiche candidat complète, historique d'étapes et documents contrôlés.
3. Pipeline Kanban réel, filtres, recherche, vivier et rattachement à une offre.
4. Cycle complet des offres : modifier, publier, archiver, rechercher, filtrer.
5. Paramètres : entreprise, apparence, recrutement, RGPD, utilisateurs et IA.
6. Export/effacement RGPD, activité, connecteur AACP/1 réellement configurable et tolérant aux pannes.
7. Diffusion d'offres, seulement lorsque chaque fournisseur possède un contrat technique et des identifiants configurés.
