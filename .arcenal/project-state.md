# ARCenal ATS — état du projet

- Date : 2026-09-25
- Branche active : `main`, paquet YunoHost publié aussi sur `stable`
- Objectif : socle V1 Python/FastAPI/PostgreSQL autonome, avec portail carrière public et paquet YunoHost.

## État observé

Le dépôt distant était vide à l’exception de la licence. Les projets `arc-oskar-suite` et `arcenal-agent` restent hors de ce dépôt et n’ont pas été modifiés.

## Décisions actives

- FastAPI sert l’API publique et l’interface HTML minimale.
- Le portail public reprend les jetons sombres d’ARCenal Agent : fond graphite, surfaces bleu nuit et accents or/ambre.
- PostgreSQL est l’unique base de données cible ; une migration initiale Alembic décrit le schéma.
- Les documents utilisent un répertoire privé configurable hors racine web.
- Le portail `/recrutement`, le widget et l’API `/public-api/v1` sont publics ; l’espace interne est protégé par l’identité injectée par SSOwat.
- Les CV et lettres passent par un endpoint dédié et restent dans le stockage privé ; seules leurs métadonnées sont en base.
- AACP/1 est préparé comme frontière métier, sans accès SQL, terminal ou fichiers pour ARCenal Agent.

## Validation à exécuter

1. `ruff check .`
2. `mypy src`
3. `python -m unittest discover -s tests -v` (sans dépendance externe) puis `pytest` dans l’environnement de développement.

## Correctif d’installation en cours

Le journal YunoHost a confirmé que `ynh_psql_setup_db` stocke le mot de passe PostgreSQL dans le réglage `psqlpwd`. Le script d’installation le recharge désormais avant de lancer la migration et de rendre le service systemd, qui en a besoin pour remplacer `__PSQLPWD__`. Un test de régression vérifie cet ordre.

Une installation interrompue peut laisser le rôle PostgreSQL dédié sans son réglage YunoHost. Lors d'une nouvelle installation, ce reliquat propre à l'application est supprimé avant la création de la base afin que YunoHost puisse générer et conserver un nouveau mot de passe.

YunoHost 12 ne fournit pas le helper `ynh_systemctl`. Les scripts du paquet emploient directement `systemctl` pour démarrer, arrêter ou redémarrer le service après que les helpers ont installé son unité systemd.

L'environnement virtuel est créé avec l'utilisateur système de l'application après attribution explicite de son répertoire d'installation. Cela évite qu'un environnement créé par `root` bloque l'installation des dépendances lors d'une nouvelle instance ou d'une reprise.

## Limites connues

L’environnement de construction actuel ne contient ni FastAPI, ni SQLAlchemy, ni les outils de lint/type/test déclarés. Aucun paquet n’a été installé conformément à la règle de sobriété des dépendances.
