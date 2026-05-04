---
name: notion-schema
description: Schema verificato dei database Notion del board K2-AI e regole di scrittura
---

# Notion Schema K2-AI

## DATABASE TASK

Campi: Titolo (title, obbligatorio), Stato (select: Backlog/Da fare/In corso/In review/Approvato/Fatto/Bloccato),
Priorità (select: Critica/Alta/Media/Bassa), Tipo (select: Operativo/Tecnico/Documento/Commerciale/Revisione/Sopralluogo/Automazione/AI),
Richiesto da (select: Founder/Cliente/K-BOT/Telegram/AI Agent/Interno),
Descrizione, Output, Blocco/rischio, Scadenza (date YYYY-MM-DD),
Cliente (relation → Clienti), Commessa (relation → Commesse), Lead collegato (relation → Pipeline Lead).

Tool: `create_board_task` (crea, accetta client_name), `update_board_task` (aggiorna), `list_open_tasks` (leggi).

## DATABASE PIPELINE LEAD

Campi: Nome lead (title, obbligatorio), Azienda, Settore, Pain point, Fit offerta,
Stato (Identificato/Qualificato/Contattato/Call fissata/Proposta inviata/Vinto/Perso),
Canale (Sito/K-BOT/Referral/LinkedIn/Telefonata/Email/Interno/agent),
Score (0-100), Prossima azione, Data prossima azione, Note, Cliente collegato (relation → Clienti).

Tool: `add_lead_to_pipeline` (crea), `update_pipeline_lead` (aggiorna), `list_pipeline_status` (leggi).

## DATABASE CLIENTI

Campi: Nome cliente/società (title, obbligatorio),
Stato relazione (select: Lead/Cliente attivo/Cliente passato/Partner/Interno),
Settore (select: Immobiliare/Servizi/Studio tecnico/Ingegneria/Edilizia/PMI/Altro/Tech/Software),
Referente, Email, Telefono, Note.

Tool: `list_clients` (leggi), `search_client` (cerca per nome), `create_or_update_client` (crea/aggiorna).

## DATABASE MEMORIA / DECISIONI

Campi: Titolo (title, chiave semantica), Valore/contenuto (text),
Categoria (select: Metodo/Cliente/Offerta/Processo/Tecnico/Commerciale/Decisione),
Fonte (Founder/Cliente/AI/Riunione/Documento).

Tool: `save_to_memory` (scrivi). Usa per decisioni strategiche e contesto persistente.

## DATABASE COMMESSE (sola lettura)

Gli agenti non scrivono su Commesse — è il fondatore a gestirle. Usare solo per lettura di contesto.

## Regole di scrittura

- Campi obbligatori: Task→titolo; Lead→nome; Cliente→nome azienda. Non creare record incompleti.
- Se il fondatore ragiona ("come la imposteresti?") NON toccare Notion. Se dice "fai", "aggiungi", "crea" → scrivi.
- Dopo una write: riferisci solo l'esito dell'azione principale. Non mescolare successo e problemi secondari.
- Catena di navigazione: Pipeline Lead → Cliente → Commessa → Fasi → Task → Approvazioni/Log AI.
- Quando crei un task, collega sempre Cliente (via client_name) se disponibile.
