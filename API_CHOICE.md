# API Choice

- **Étudiant :** (votre nom)
- **API choisie :** Frankfurter
- **URL base :** `https://api.frankfurter.app`
- **Documentation officielle :** https://www.frankfurter.app/docs/
- **Auth :** None (aucune clé requise)

## Endpoints testés

- `GET /latest?from=EUR` — taux de change EUR actuels
- `GET /latest?amount=100&from=EUR&to=USD` — conversion EUR→USD
- `GET /2024-01-15?from=EUR` — taux historiques à une date fixe
- `GET /currencies` — liste de toutes les devises supportées
- `GET /latest?from=ZZZ` — devise invalide (erreur attendue 4xx)
- `GET /9999-99-99` — date invalide (erreur attendue 4xx)

## Hypothèses de contrat (champs attendus, types, codes)

| Endpoint | HTTP attendu | Champs obligatoires | Types |
|----------|-------------|---------------------|-------|
| `/latest?from=EUR` | 200 | `base` (str), `date` (str), `rates` (object) | rates: float > 0 |
| `/latest?from=EUR` | 200 | `rates.USD` présent | float |
| `/2024-01-15` | 200 | `date` == "2024-01-15" | str |
| `/currencies` | 200 | dict non vide, clés à 3 lettres | str→str |
| `/latest?from=ZZZ` | 4xx | — | — |
| `/9999-99-99` | 4xx | — | — |

## Limites / rate limiting connu

- Pas de rate limiting officiel documenté
- Usage raisonnable recommandé : 1 run / 5 min (20 req max/run)
- Anti-spam implémenté dans `storage.py` (`MIN_INTERVAL = 300s`)

## Risques

- Données en temps réel : les taux varient (tests non déterministes sur les valeurs)
- Possible downtime rare (service externe)
- Pas de SLA garanti (API gratuite et open source)
