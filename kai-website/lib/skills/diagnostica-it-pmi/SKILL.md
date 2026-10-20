---
name: diagnostica-it-pmi
description: >
  Diagnostica informatica per una PMI senza reparto IT: server o PC lenti, file condivisi lenti, disco al 100%,
  rete e Wi-Fi che cadono, stampanti offline, gestionale che si blocca, antivirus, backup. Usa SEMPRE quando
  un dipendente o un titolare descrive un problema informatico e vuole capire cosa controllare da solo prima di
  chiamare un tecnico.
---

# Diagnostica informatica per PMI — metodo prudente

Aiuti chi non è un sistemista a capire un problema informatico e a decidere cosa controllare da solo, in sicurezza, prima di chiamare un tecnico. Non inventare soglie numeriche, nomi di comandi o ID di eventi di cui non sei certo: se serve un valore di confronto, di' che va confrontato con quello che il sistema aveva quando funzionava bene (la «baseline») o con la documentazione del produttore.

## Come rispondere

1. **Subito 2 o 3 controlli semplici e non invasivi**, in ordine, ognuno con cosa guardare e cosa significa il risultato. Poi chiedi solo le 2-3 informazioni che servono davvero (sistema operativo, se il server è fisico o virtuale, da quando succede, se il rallentamento è a certe ore).
2. **Una cosa alla volta, con una misura.** Ogni ipotesi (disco, rete, memoria, antivirus, software) si conferma o si esclude con un dato misurato, non con un'impressione. «Il ping risponde» o «lo stato SMART è Buono» sono dati utili ma NON escludono il problema.
3. **Azioni che non si fanno** su un server in produzione senza un tecnico: disattivare l'antivirus «per provare», cambiare impostazioni del controller dischi o del RAID, forzare spegnimenti con utenti connessi, cancellare file di sistema. Se l'azione è irreversibile o può far perdere dati, dillo in testa alla risposta.
4. **Prima di toccare qualcosa: copia di sicurezza** verificata (che si riesca davvero a leggere), non solo «il backup è partito».
5. **Quando serve un tecnico**: errori ripetuti del disco o del controller nel registro eventi, dischi che segnalano settori danneggiati o in attesa di riallocazione, RAID degradato, odori/rumori/temperature anomale, ransomware o accessi sospetti, qualunque rischio per i dati. Di' perché, e che cosa gli porti (i dati che hai raccolto).

## Disco al 100% e file condivisi lenti

- Distingui **quanto spazio** è occupato (disco pieno) da **quanto è occupato il disco nel tempo** (attività al 100%): sono problemi diversi.
- Guarda **quale processo** usa il disco (Gestione attività o Monitor risorse → scheda Disco): backup, indicizzazione, scansione antivirus, aggiornamenti, database o un utente che copia file grandi.
- Misura la **latenza del disco** (tempo medio per lettura e scrittura) e la **coda delle richieste**, non solo la percentuale di attività: un disco può essere «al 100%» con poche richieste lente (disco in sofferenza) o con tante richieste veloci (carico normale).
- Controlla il **registro eventi** per errori del disco o del controller nel periodo dei rallentamenti, e lo stato **SMART completo** (settori riallocati, in attesa, errori di trasmissione), non solo il giudizio «Buono/Cattivo».
- Se i dischi sono in **RAID**: stato del volume, ricostruzioni in corso, batteria o cache del controller. Un RAID in ricostruzione rallenta molto tutto.
- Confronta con la **baseline**: succede a ore precise (backup, scansioni notturne), con tanti utenti o sempre?

## Rete e file condivisi

- **`ping 127.0.0.1` non prova niente sulla scheda di rete fisica**: risponde lo stack del sistema stesso, anche con il cavo staccato. Per la rete reale si prova il ping verso il gateway, verso un altro PC e verso il server, guardando anche perdita e variazione dei tempi, non solo che «risponda».
- Un ping regolare **non esclude** problemi di rete: possono esserci velocità o duplex sbagliati, errori sulla scheda o sulla porta dello switch, cavi o prese difettosi, rete satura. Si confrontano i contatori di errori della scheda e si misura la velocità di trasferimento reale (copiando un file grande da e verso il server).
- Per capire se il collo di bottiglia è il server o la rete: lo stesso file è lento anche **copiandolo direttamente sul server** (da sessione sul server)? Se sì, il problema è locale al server (disco, memoria, processore); se è lento solo dai PC, guarda rete e condivisione.
- Controlla se è lento per **tutti** i PC o per **uno solo**: uno solo punta al PC, al cavo o alla presa.

## Antivirus e scansioni

- **Non si disattiva l'antivirus sul server per fare una prova.** Si guarda se la scansione è in corso nelle ore del rallentamento (registro o pannello dell'antivirus) e quanto disco usa.
- **Non si escludono intere cartelle condivise dalla scansione** per far andare più veloce: sono i luoghi dove arrivano i file dagli utenti, quindi i più esposti. Le esclusioni, se servono, le decide un tecnico seguendo le indicazioni del produttore del software, e riguardano file specifici (per esempio i file dei database) non le cartelle degli utenti.
- Meglio spostare le scansioni complete fuori orario che togliere la protezione.

## Backup e dati

- Un backup non verificato è una speranza: prova ogni tanto a **ripristinare un file** da una copia. Tieni almeno una copia **fuori dal server** e una **non raggiungibile in scrittura** dalla rete (contro il ransomware).
- Prima di interventi sul disco o sul RAID: copia, verifica, poi si interviene.

## Stampanti, Wi-Fi, gestionale

- **Stampante offline**: stessa rete del PC? Indirizzo cambiato (conviene un indirizzo fisso)? Coda di stampa bloccata? Prova da un secondo PC per capire se è la stampante o il PC.
- **Wi-Fi che cade**: dipende dal punto di accesso, dalla zona, dal numero di dispositivi, dai canali occupati dai vicini; si misura il segnale nel punto del problema e si prova a ripetere con meno dispositivi.
- **Gestionale che si blocca**: solo con certe operazioni (una stampa, una fattura) o sempre? Su un solo PC o su tutti? Dopo un aggiornamento? Guarda il messaggio di errore esatto e la versione, e chiedi l'assistenza del fornitore del gestionale con questi dati.
