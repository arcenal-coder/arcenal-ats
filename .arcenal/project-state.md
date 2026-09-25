# ARCenal ATS — état du projet

- Date : 2026-09-25
- Branche observée : `main`, commit initial `69bd1a7`
- Objectif : socle V1 Python/FastAPI/PostgreSQL autonome, avec portail carrière public et paquet YunoHost.

## État observé

Le dépôt distant était vide à l’exception de la licence. Les projets `arc-oskar-suite` et `arcenal-agent` restent hors de ce dépôt et n’ont pas été modifiés.

## Décisions actives

- FastAPI sert l’API publique et l’interface HTML minimale.
- PostgreSQL est l’unique base de données cible ; une migration initiale Alembic décrit le schéma.
- Les documents utilisent un répertoire privé configurable hors racine web.
- Le portail `/recrutement`, le widget et l’API `/public-api/v1` sont publics ; l’espace interne est protégé par l’identité injectée par SSOwat.
- Les CV et lettres passent par un endpoint dédié et restent dans le stockage privé ; seules leurs métadonnées sont en base.
- AACP/1 est préparé comme frontière métier, sans accès SQL, terminal ou fichiers pour ARCenal Agent.

## Validation à exécuter

1. `ruff check .`
2. `mypy src`
3. `python -m unittest discover -s tests -v` (sans dépendance externe) puis `pytest` dans l’environnement de développement.

## Limites connues

L’environnement de construction actuel ne contient ni FastAPI, ni SQLAlchemy, ni les outils de lint/type/test déclarés. Aucun paquet n’a été installé conformément à la règle de sobriété des dépendances.
