import type { ReportData } from '../types/report'

export const mockReportData: ReportData = {
  meta: {
    title: 'Report di opportunita AI',
    subtitle: 'Automazione follow-up commerciali e aggiornamento CRM',
    category: 'Diagnosi operativa K2AI',
    code: 'K2AI-RPT-0426-CRM',
    date: '30 aprile 2026',
    version: 'Preview 1.0',
  },
  client: {
    name: 'Alfa Componenti S.r.l.',
    scope: 'PMI B2B italiana, circa 15 dipendenti, vendita tecnica a clienti industriali',
  },
  sections: {
    cover: true,
    executiveSummary: true,
    context: true,
    problem: true,
    analysis: true,
    opportunity: true,
    solution: true,
    roadmap: true,
    priorities: true,
    impact: true,
    recommendedPlan: true,
    nextSteps: true,
    disclaimer: true,
  },
  executiveSummary: {
    title: 'Executive summary',
    text: 'L azienda gestisce opportunita commerciali B2B con un ciclo di vendita consultivo. Dopo fiere, richieste inbound e preventivi inviati, il team perde continuita nei follow-up e aggiorna il CRM in modo irregolare. Un sistema AI operativo puo ridurre il lavoro manuale, standardizzare le risposte e mantenere il CRM aggiornato senza cambiare gli strumenti esistenti.',
    metrics: [
      { value: '8 ore/sett.', label: 'tempo commerciale recuperabile' },
      { value: '€1.200/mese', label: 'costo operativo stimato oggi' },
      { value: '3 giorni', label: 'ritardo medio nei follow-up' },
    ],
    operationalTakeaway: 'La priorita non e sostituire il commerciale, ma togliere attivita ripetitive dopo ogni contatto: sintesi, promemoria, email di follow-up e aggiornamento CRM.',
  },
  context: {
    title: 'Contesto aziendale',
    currentScenario: 'Il team commerciale lavora con email, fogli condivisi e CRM. Le informazioni sui clienti arrivano da conversazioni, allegati tecnici, form del sito e note prese durante call o fiere. La qualita del dato varia molto in base alla persona che segue l opportunita.',
    reportObjective: 'Valutare un primo sistema AI capace di leggere il contesto commerciale, proporre follow-up coerenti e aggiornare il CRM con campi essenziali, mantenendo approvazione umana prima dell invio.',
    tags: ['PMI B2B', 'CRM', 'Email follow-up', 'Vendita tecnica', 'AI operativa'],
  },
  problem: {
    title: 'Problema rilevato',
    main: 'Il processo commerciale contiene molte micro-attivita ripetitive che non generano valore diretto ma influenzano pipeline, tempi di risposta e qualita percepita dal cliente.',
    rows: [
      {
        area: 'Follow-up post preventivo',
        criticalIssue: 'Email scritte ogni volta da zero e spesso inviate in ritardo.',
        effect: 'Opportunita calde si raffreddano e il commerciale perde visibilita sulle priorita.',
        priority: 'Alta',
        priorityClass: 'high',
      },
      {
        area: 'Aggiornamento CRM',
        criticalIssue: 'Note, prossime azioni e stato opportunita non vengono aggiornati con continuita.',
        effect: 'Pipeline poco affidabile e riunioni commerciali basate su ricostruzioni manuali.',
        priority: 'Alta',
        priorityClass: 'high',
      },
      {
        area: 'Qualifica lead',
        criticalIssue: 'Richieste inbound lette manualmente e classificate senza criteri condivisi.',
        effect: 'Tempi di risposta variabili e priorita non sempre coerenti con il potenziale cliente.',
        priority: 'Media',
        priorityClass: 'medium',
      },
      {
        area: 'Report direzionale',
        criticalIssue: 'Sintesi commerciale preparata a mano prima delle riunioni.',
        effect: 'Tempo sottratto alla vendita e rischio di perdere segnali utili.',
        priority: 'Media',
        priorityClass: 'medium',
      },
    ],
  },
  analysis: {
    title: 'Analisi operativa',
    intro: 'Il caso e adatto a una prima automazione perche unisce testi ricorrenti, dati gia disponibili e un controllo umano chiaro. Il valore principale nasce dall orchestrazione tra email, CRM e agenda.',
    cards: [
      {
        title: 'Processo ripetibile',
        description: 'Le attivita successive a un contatto commerciale seguono pattern stabili: riepilogo, prossima azione, follow-up e aggiornamento opportunita.',
      },
      {
        title: 'Dati sufficienti',
        description: 'Email, note call, preventivi e campi CRM contengono gia il contesto minimo per generare bozze affidabili.',
      },
      {
        title: 'Rischio controllabile',
        description: 'L AI puo lavorare in modalita assistita: propone testi e aggiornamenti, ma il team approva prima di inviare o salvare.',
      },
    ],
    table: [
      {
        parameter: 'Volume',
        detectedStatus: '25-40 interazioni commerciali rilevanti al mese',
        evaluation: 'Adeguato',
        note: 'Volume sufficiente per recuperare tempo senza introdurre complessita eccessiva.',
      },
      {
        parameter: 'Standardizzazione',
        detectedStatus: 'Template parziali e prassi individuali',
        evaluation: 'Migliorabile',
        note: 'Serve una libreria minima di casi e toni di comunicazione.',
      },
      {
        parameter: 'Integrazione',
        detectedStatus: 'CRM e posta elettronica gia in uso',
        evaluation: 'Buona',
        note: 'Si puo partire con integrazione leggera e validazione manuale.',
      },
      {
        parameter: 'Governance',
        detectedStatus: 'Responsabilita commerciale chiara',
        evaluation: 'Buona',
        note: 'Il responsabile commerciale puo validare criteri, priorita e casi limite.',
      },
    ],
  },
  opportunity: {
    title: 'Opportunita AI',
    intro: 'Le opportunita piu concrete sono concentrate nei passaggi subito dopo un interazione commerciale, dove il contesto e fresco e la perdita di tempo e ricorrente.',
    items: [
      {
        title: 'Bozze follow-up assistite',
        description: 'Generazione di email coerenti con ultimo scambio, stato del preventivo e prossima azione desiderata.',
        impact: 'Alto',
        effort: 'Medio',
      },
      {
        title: 'Aggiornamento CRM guidato',
        description: 'Proposta automatica di stato opportunita, note sintetiche, prossima attivita e data di ricontatto.',
        impact: 'Alto',
        effort: 'Medio',
      },
      {
        title: 'Prioritizzazione lead',
        description: 'Classificazione delle richieste in base a urgenza, valore potenziale e completezza delle informazioni.',
        impact: 'Medio',
        effort: 'Basso',
      },
      {
        title: 'Riepilogo settimanale pipeline',
        description: 'Sintesi automatica delle opportunita ferme, azioni scadute e clienti da ricontattare.',
        impact: 'Medio',
        effort: 'Basso',
      },
    ],
  },
  solution: {
    title: 'Soluzione proposta',
    description: 'Realizzare un assistente AI interno, collegato ai canali gia usati dal team, che prepara bozze e aggiornamenti operativi senza inviare comunicazioni in autonomia. La prima versione deve essere focalizzata su follow-up e CRM, con misurazione chiara del tempo risparmiato.',
    components: [
      'Raccolta contesto da email, note commerciali e campi CRM essenziali.',
      'Generazione bozze follow-up con tono aziendale e riferimenti al caso specifico.',
      'Scheda di approvazione umana per modificare, confermare o scartare il suggerimento.',
      'Aggiornamento CRM assistito con note sintetiche, prossimo step e data consigliata.',
      'Dashboard minimale per opportunita ferme, azioni scadute e follow-up suggeriti.',
    ],
    expectedResult: 'Entro il primo prototipo il team dovrebbe ridurre il lavoro amministrativo commerciale e aumentare la puntualita dei ricontatti, senza cambiare processo di vendita.',
  },
  roadmap: {
    title: 'Roadmap di implementazione',
    items: [
      {
        phaseTitle: 'Fase 1 - Setup e criteri',
        timeframe: 'Settimana 1',
        owner: 'K2AI + Responsabile commerciale',
        phaseDescription: 'Mappatura campi CRM, raccolta esempi reali di email, definizione criteri di priorita e tono comunicativo.',
      },
      {
        phaseTitle: 'Fase 2 - Prototipo assistito',
        timeframe: 'Settimane 2-3',
        owner: 'K2AI',
        phaseDescription: 'Costruzione del flusso che genera bozze follow-up e suggerisce aggiornamenti CRM con revisione manuale.',
      },
      {
        phaseTitle: 'Fase 3 - Test su casi reali',
        timeframe: 'Settimana 4',
        owner: 'Team commerciale',
        phaseDescription: 'Uso controllato su un sottoinsieme di opportunita, raccolta feedback e confronto con tempi precedenti.',
      },
      {
        phaseTitle: 'Fase 4 - Consolidamento',
        timeframe: 'Settimane 5-6',
        owner: 'K2AI + Direzione',
        phaseDescription: 'Correzione casi limite, definizione metriche ricorrenti e decisione su eventuale estensione ad altri flussi.',
      },
    ],
  },
  priorities: {
    title: 'Priorita operative',
    items: [
      {
        priorityLevel: 'Alta',
        priorityClass: 'high',
        action: 'Automatizzare bozze follow-up post preventivo',
        reason: 'E il punto con maggiore perdita di continuita commerciale.',
        impact: 'Riduzione ritardi e maggiore uniformita delle comunicazioni.',
        timing: 'Subito',
      },
      {
        priorityLevel: 'Alta',
        priorityClass: 'high',
        action: 'Suggerire aggiornamenti CRM dopo ogni interazione',
        reason: 'La qualita del CRM condiziona pipeline e riunioni.',
        impact: 'Dato piu affidabile e meno ricostruzioni manuali.',
        timing: 'Subito',
      },
      {
        priorityLevel: 'Media',
        priorityClass: 'medium',
        action: 'Creare riepilogo settimanale opportunita ferme',
        reason: 'Aiuta il responsabile commerciale a intervenire prima.',
        impact: 'Migliore controllo del ciclo vendita.',
        timing: 'Dopo prototipo',
      },
      {
        priorityLevel: 'Bassa',
        priorityClass: 'low',
        action: 'Estendere ad analisi documentale dei preventivi',
        reason: 'Interessante, ma meno urgente rispetto al follow-up.',
        impact: 'Supporto a offerte tecniche piu complesse.',
        timing: 'Fase successiva',
      },
    ],
  },
  impact: {
    title: 'Impatto atteso',
    metrics: [
      { value: '-35%', label: 'tempo su attivita commerciali ripetitive' },
      { value: '+20%', label: 'follow-up entro 48 ore' },
      { value: '6 sett.', label: 'orizzonte per validare il prototipo' },
    ],
    rows: [
      {
        dimension: 'Tempo',
        expectedImpact: 'Riduzione delle ore dedicate a scrittura ripetitiva e aggiornamento CRM.',
        indicator: 'Ore settimanali risparmiate dal team commerciale.',
      },
      {
        dimension: 'Qualita pipeline',
        expectedImpact: 'Migliore completezza di note, stati e prossime azioni.',
        indicator: 'Percentuale opportunita con prossimo step valorizzato.',
      },
      {
        dimension: 'Esperienza cliente',
        expectedImpact: 'Comunicazioni piu puntuali, coerenti e contestuali.',
        indicator: 'Tempo medio tra preventivo e primo follow-up.',
      },
      {
        dimension: 'Controllo direzionale',
        expectedImpact: 'Riunioni commerciali basate su dati piu aggiornati.',
        indicator: 'Numero di opportunita ferme evidenziate ogni settimana.',
      },
    ],
  },
  recommendedPlan: {
    title: 'Piano consigliato',
    summary: 'Si consiglia un prototipo limitato, misurabile e reversibile. La prima release deve dimostrare valore su un flusso stretto prima di ampliare automazioni e integrazioni.',
    steps: [
      {
        step: '01',
        activity: 'Selezione campione casi reali',
        output: '10-15 opportunita recenti con email, note e stato CRM',
        owner: 'Cliente',
      },
      {
        step: '02',
        activity: 'Definizione tono e criteri',
        output: 'Linee guida per follow-up e priorita commerciali',
        owner: 'Cliente + K2AI',
      },
      {
        step: '03',
        activity: 'Costruzione prototipo',
        output: 'Assistente con bozze email e suggerimenti CRM',
        owner: 'K2AI',
      },
      {
        step: '04',
        activity: 'Validazione operativa',
        output: 'Report su tempo risparmiato, qualita bozze e limiti',
        owner: 'Team commerciale',
      },
    ],
  },
  nextSteps: {
    title: 'Next step',
    immediateActions: [
      'Confermare CRM, caselle email e strumenti oggi usati dal team.',
      'Individuare un referente commerciale per validazione tono e priorita.',
      'Raccogliere esempi reali di follow-up riusciti e casi problematici.',
    ],
    requiredDecisions: [
      'Definire se il prototipo lavora su tutti i lead o solo su opportunita post preventivo.',
      'Stabilire quali campi CRM possono essere aggiornati in modalita assistita.',
      'Confermare il perimetro privacy e i dati esclusi dal primo test.',
    ],
    suggestedNextStep: 'Avviare una sessione di allineamento di 60 minuti per trasformare questo report in backlog di prototipo.',
  },
  disclaimer: {
    title: 'Disclaimer',
    text: 'Questo documento e una preview consulenziale con dati mock. Le stime sono indicative e non costituiscono garanzia di risultato. Prima di qualunque implementazione reale e necessario validare processi, dati, integrazioni, vincoli privacy e responsabilita operative.',
  },
}
