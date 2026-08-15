# POS

## Delivery Integrations

Connects the POS's catalog and order flow to third-party delivery marketplaces (Uber Eats, Glovo, Deliveroo, Just Eat) via per-tenant credentials and inbound webhooks. Today every provider adapter is a sandbox stub — no real marketplace API is called yet.

### Language

**Statut de connexion**:
Badge à 5 valeurs affiché sur la carte d'un provider : *Non configuré*, *Déconnecté*, *En attente de test*, *Connecté*, *Erreur API*.
_Avoid_: le champ brut `connection_status` seul (il ne couvre que 3 des 5 valeurs), "actif/inactif"

**Non configuré**:
Aucune ligne `DeliveryMarketplaceIntegration` n'existe encore pour ce provider et ce tenant (le provider apparaît dans le catalogue mais n'a jamais été enregistré).

**Déconnecté**:
Intégration enregistrée mais `enabled = false` — désactivée volontairement par le gérant.

**En attente de test**:
`enabled = true` mais `last_test_ok` est encore `null` — jamais testée depuis son activation. État neutre par défaut, pour ne pas afficher un vert ou un rouge trompeur sur une intégration jamais vérifiée.

**Connecté**:
`enabled = true` et dernier test de connexion réussi (`last_test_ok = true`).

**Erreur API**:
`enabled = true` et dernier test de connexion en échec (`last_test_ok = false`).

**Pause rapide**:
Action en un clic, depuis l'en-tête (non dépliée) de la carte provider, qui bascule `enabled` sans ouvrir la configuration avancée. Alias UX du champ `enabled` existant — ce n'est pas un nouvel état de données.
_Avoid_: "désactivation" comme concept distinct de la pause

**Établissement lié**:
Le nom affiché à la place de la clé technique du provider (`provider_key`, ex. `uber_eats`) dans l'UI manager. Correspond à `tenant.name` : un tenant représente un seul établissement physique dans le modèle actuel (pas de modèle Location/Store séparé).
_Avoid_: "site", "boutique" comme concept de données séparé — n'existe pas aujourd'hui

**Dernière commande reçue**:
Horodatage du dernier événement `webhook_order` du journal (`DeliveryIntegrationEventLog`) pour cette intégration.
_Avoid_: "dernière synchronisation" — retiré du vocabulaire tant qu'aucun job de synchro périodique du menu n'existe

**Opérateur de livraison**:
Entrée du catalogue de providers (`provider_key` technique + `display_name` public). Catalogue actuel : Uber Eats, Glovo, Deliveroo (stubs sandbox), Just Eat (marché France/Belgique).

**Indicateur de correspondance menu**:
Deux mesures affichées côte à côte sur la carte provider, calculées à partir des données déjà enregistrées (aucun tirage du menu du provider, cf. "Opérateur de livraison") :
1. Nombre de correspondances enregistrées (`DeliveryCatalogMapping` count) + date de dernière modification — état de la configuration.
2. Nombre de commandes rejetées pour SKU non mappé sur les 7 derniers jours, tiré des événements `import_error` / `missing_external_item_ids` du journal — signal d'alerte terrain.
_Avoid_: "X/Y items synchronisés" — suppose un total côté provider qu'on ne connaît pas tant qu'aucune vraie API de menu n'est branchée

**Pastille de marque**:
Icône dans la carte provider identifiant visuellement chaque marketplace. Décision révisée : les vrais tracés de marque (Uber Eats, Glovo, Deliveroo, Just Eat) sont utilisés, sourcés du projet Simple Icons (données SVG CC0 ; chaque marque reste la propriété de son titulaire), colorés avec la couleur de marque officielle. Réservé à cet écran de configuration interne (jamais dans une UI orientée client) — usage nominatif pour identifier une intégration réelle, pas une association de marque. Les `provider_key` sans tracé connu (ex. `stub`) retombent sur une pastille avec l'initiale du nom.
_Avoid_: pastille neutre générique pour les 4 marques connues — décision initiale (Q8) abandonnée au profit des vrais logos

## Hyper-Adaptation Marché France / Afrique de l'Ouest

Positionnement multi-marché (France vs Sénégal, Côte d'Ivoire, etc.) couvrant 4 chantiers largement indépendants : fiscalité (NF525 vs conformité DGI locale), paiements (CB/Titres-Restaurant vs Mobile Money), devises (EUR vs XOF/XAF), expérience client (QR/borne vs WhatsApp/social). Axe traité en premier : la devise — c'est un correctif de fond qui bloque silencieusement les 3 autres chantiers si une devise sans décimales est utilisée avant lui. Les 3 autres axes sont mis en réserve, pas abandonnés.

### Language

**Devise sans décimales (zero-decimal currency)**:
Devise dont la plus petite unité n'a pas de sous-division (ex. XOF, XAF, JPY, KRW) — contrairement à l'EUR, un montant de "1500" représente 1500 unités entières, pas 15,00. Portée : la liste officielle Stripe des devises zero-decimal (pas seulement XOF/XAF), pour ne pas refaire ce travail au prochain marché.
_Avoid_: traiter XOF/XAF comme un cas particulier isolé — c'est une catégorie de devises, pas deux exceptions

**Champs `*_cents`**:
Conservent leur nom historique (`price_cents`, etc.) même pour les devises sans décimales, où leur valeur est alors le montant complet (pas des "centimes"). Toute conversion affichage ↔ stockage passe par un helper central par devise (`toDisplayUnits`/`toMinorUnits`), jamais par une division ou multiplication par 100 codée en dur.
_Avoid_: renommer les champs (`price_minor_units`) — jugé disproportionné pour une devise sans tenant existant ; diviser/multiplier par 100 en dur dans un nouveau call site — c'est exactement le bug que le helper corrige

**Chemins visibles / internes** (portée du nettoyage des ~93 sites `/100` et `*100` dupliqués aujourd'hui) :
*Visibles* (corrigés dans cette passe) — prix menu, ticket caisse, reçus, checkout, totaux rapports, éditeur de produit, prix libre en caisse, pourboire. *Internes* (passe de nettoyage séparée, différée) — logs, dashboards admin techniques.
_Avoid_: "tout nettoyer d'un coup" comme prérequis — la correction du bug ×100 ne dépend que des chemins visibles

**Nombre de décimales (par tenant)**:
Champ explicite sur `Tenant` (`currency_decimal_places`, 0/2/3...) qui pilote le helper central — pas seulement une déduction automatique depuis `currency_code`. Valeur par défaut suggérée depuis la liste Stripe des devises zero-decimal quand le gérant choisit sa devise (EUR→2, XOF/XAF→0), mais reste modifiable explicitement dans les réglages du tenant : le gérant a le dernier mot, pas la devise seule.
_Avoid_: dériver les décimales uniquement de `currency_code` sans champ de dérogation — certains gérants peuvent vouloir un affichage différent de la convention par défaut de leur devise
