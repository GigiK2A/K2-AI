# Integrazione Piattaforma SaaS — SafetyBoost

## Tool custom in modalita piattaforma

### `database_rischi(lavorazione, settore)`
Restituisce rischi tipici con P, D, misure standard da database INAIL/AUSL.

### `catalogo_dpi(rischio, norma_en)`
Restituisce DPI compatibili con specifiche e costi.

### `prezzario_sicurezza(regione, voce)`
Costi unitari apprestamenti e misure di sicurezza.

### `verifica_formazione(cf_lavoratore)`
Verifica attestati in corso di validita e scadenze.

### `template_psc(tipo_cantiere)`
Template PSC precompilato per tipologia cantiere.

## Degradazione in modalita consulenziale
- Rischi: analisi basata su esperienza e normativa D.Lgs. 81/2008.
- DPI: indicazione generica con norma EN, senza catalogo.
- Costi: benchmark da references e prezzari regionali.
- Formazione: verifica dichiarativa dall'utente.
