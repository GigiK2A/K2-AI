/**
 * Mappa settore → bundle di skill.
 * La prima skill è sempre diagnosi-ai-operativa-pmi (base).
 * Le successive sono le skill verticali del settore.
 * NOTA: diagnosi-ai-operativa-pmi va CREATA (vedi Prompt K2).
 */
export const SECTOR_BUNDLES: Record<string, string[]> = {
  'studio-ingegneria': [
    'diagnosi-ai-operativa-pmi',
    'progettista-strutturale',
    'progettazione-architettonica',
    'direzione-lavori',
    'cse-coordinatore-sicurezza',
    'psc-coordinamento-sicurezza',
    'impianti-elettrici',
    'impianti-termici-hvac',
    'agibilita',
  ],
  'commercialista': [
    'diagnosi-ai-operativa-pmi',
    'contabilita-bilancio',
    'fiscale-tributario-italiano',
    'programmazione-controllo',
    'analisi-bilancio-pmi',
    'bilancio-consolidato-analisi',
    'budget-forecast-pmi',
    'diritto-societario-italiano',
  ],
  'manifatturiero': [
    'diagnosi-ai-operativa-pmi',
    'programmazione-controllo',
    'corporate-finance',
    'strategia-competitiva',
    'analisi-settore-pmi',
    'benchmark-italia-business',
    'budget-forecast-pmi',
    'cruscotto-direzionale',
  ],
  'servizi-b2b': [
    'diagnosi-ai-operativa-pmi',
    'strategia-competitiva',
    'posizionamento-strategico',
    'piano-crescita-pmi',
    'marketing-strategico',
    'pricing-optimizer',
    'analisi-settore-pmi',
    'crm-customer-experience',
  ],
  'hospitality': [
    'diagnosi-ai-operativa-pmi',
    'flusso-hostboost-ricettive',
    'marketing-strategico',
    'pricing-optimizer',
    'digital-marketing-performance',
    'crm-customer-experience',
  ],
  'commercio-ecommerce': [
    'diagnosi-ai-operativa-pmi',
    'marketing-strategico',
    'digital-marketing-performance',
    'pricing-optimizer',
    'ecommerce-marketing-pmi',
    'audit-seo-tecnico',
    'crm-customer-experience',
  ],
  'tlc': [
    'diagnosi-ai-operativa-pmi',
    'verifica-pe-terzi',
    'progettista-strutturale',
    'cse-coordinatore-sicurezza',
    'psc-coordinamento-sicurezza',
    'impianti-elettrici',
  ],
  'studio-legale': [
    'diagnosi-ai-operativa-pmi',
    'diritto-italiano',
    'diritto-societario-italiano',
    'diritto-processuale',
    'it-law-privacy-ai',
    'antitrust-concorrenza-ue',
  ],
  'pubblica-amministrazione': [
    'diagnosi-ai-operativa-pmi',
    'consulente-pa-operativa',
    'consulente-policy-ue',
    'consulente-finanza-pubblica',
    'it-law-privacy-ai',
  ],
}

/** Mapping slug settore → label leggibile */
export const SECTOR_LABELS: Record<string, string> = {
  'studio-ingegneria':      'Studio di ingegneria / architettura',
  'commercialista':         'Studio commercialista / CdL',
  'manifatturiero':         'Manifatturiero / produzione',
  'servizi-b2b':            'Servizi B2B / consulenza',
  'hospitality':            'Hospitality / ricettivo',
  'commercio-ecommerce':    'Commercio / e-commerce',
  'tlc':                    'TLC / infrastrutture',
  'studio-legale':          'Studio legale',
  'pubblica-amministrazione': 'Pubblica Amministrazione',
}

/** Keywords che indicano PATH A (consulenza automatica) */
export const PATH_A_KEYWORDS = [
  'analisi', 'verifica', 'check', 'report', 'bilancio', 'seo',
  'diagnosi', 'calcolo', 'valutazione', 'audit', 'controllo',
  'relazione', 'perizia', 'dichiarazione', 'indici', 'conformità',
]

/** Keywords che indicano PATH B (contatto personalizzato) */
export const PATH_B_KEYWORDS = [
  'progetto', 'partnership', 'preventivo', 'ristrutturazione',
  'implementare', 'sviluppare', 'costruire', 'tutto', 'intero',
  'riorganizzare', 'trasformare', 'cambiare', 'sistema',
  'consulenza continuativa', 'retainer', 'long term',
]
