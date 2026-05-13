---
name: rag-pipeline
description: >-
  Progettazione e valutazione pipeline RAG (Retrieval-Augmented Generation)
  per knowledge base aziendali di PMI italiane. Copre architettura, chunking,
  embedding, retrieval strategy, valutazione qualità e casi d'uso pratici.
---

# RAG Pipeline — Progettazione per PMI

## Architettura RAG in 5 fasi

```
DOCUMENTI → INGESTIONE → CHUNKING → EMBEDDING → RETRIEVAL → GENERAZIONE
  PDF/DOCX     parsing      split      vector       search       LLM
  Email        estrazione   overlap    store         score        answer
  Wiki         cleaning     metadata   (FAISS/       rerank       citazioni
```

## Fase 1: Ingestione e preprocessing

| Tipo documento | Strumento | Note |
|----------------|-----------|------|
| PDF (digitale) | PyMuPDF, pdfplumber | Estrae testo + tabelle |
| PDF (scansione) | OCR (Tesseract, AWS Textract) | Qualità dipende da scan |
| DOCX/XLSX | python-docx, openpyxl | Preserva struttura |
| Email (.eml) | email library Python | Estrai corpo, rimuovi firma |
| HTML/Wiki | BeautifulSoup | Rimuovi navigation, ads |
| Immagini | Vision model | Solo se testo critico |

Preprocessing obbligatorio:
- Rimuovi header/footer ripetuti (numeri pagina, logo)
- Normalizza encoding (UTF-8)
- Elimina blocchi boilerplate ("Documento riservato", date, versioni)
- Preserva struttura gerarchica (H1 > H2 > paragrafo)

## Fase 2: Chunking — scelta strategia

| Strategia | Chunk size | Overlap | Quando usare |
|-----------|------------|---------|--------------|
| Fixed size | 512 token | 50 token | Testo uniforme, narrativo |
| Sentence splitter | 3-5 frasi | 1 frase | FAQ, documentazione tecnica |
| Semantic chunking | Variabile | Nessuno | Testo strutturato per sezioni |
| Recursive splitter | 1000 token | 200 token | Default sicuro per misto |

**Regola empirica PMI**: chunk da 512-768 token con overlap 10-15% per documenti aziendali misti.

## Fase 3: Embedding e vector store

Modelli embedding consigliati:
- **Italiano**: `intfloat/multilingual-e5-large` o `text-embedding-3-large` (OpenAI)
- **Multilingua**: `BAAI/bge-m3`
- **Lightweight**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Vector store per PMI:

| Store | Hosting | Costo | Quando |
|-------|---------|-------|--------|
| **Supabase pgvector** | Cloud EU | Gratis/low | Default PMI, già usato K2-AI |
| **Chroma** | Self-host | Gratis | Dev locale, piccoli dataset |
| **Pinecone** | Cloud | $$ | > 1M documenti |
| **Qdrant** | Cloud/self | Low | High-performance search |

## Fase 4: Retrieval strategy

**Semantic search** (base): cosine similarity tra query embedding e document embeddings.

**Hybrid search** (raccomandato): `score_final = α × score_semantic + (1-α) × score_BM25`
- α = 0.7 per documenti tecnici
- α = 0.5 per mix tecnico/narrativo

**Reranking** (opzionale, migliora precision): usa cross-encoder dopo retrieval iniziale.
- Top-k retrieval: k=20, poi rerank → top-5

**Metadata filtering**: filtra per:
- `tipo_documento` (manuale, policy, contratto, FAQ)
- `data_aggiornamento` (preferisci documenti recenti)
- `settore` / `prodotto`
- `lingua`

## Valutazione qualità RAG

| Metrica | Misura | Target |
|---------|--------|--------|
| **Faithfulness** | Risposta fedele ai documenti recuperati | > 0.85 |
| **Answer Relevancy** | Risposta pertinente alla domanda | > 0.80 |
| **Context Precision** | Documenti recuperati tutti rilevanti | > 0.70 |
| **Context Recall** | Tutti i documenti utili sono recuperati | > 0.65 |

Framework valutazione: **RAGAS** (open source, integrabile con LangChain).

## Casi d'uso PMI italiane

**Manuale operativo aziendale**: procedure interne, policy HR, guide strumenti
- Chunk: paragrafo per procedura
- Metadata: `reparto`, `versione`, `data_revisione`

**Knowledge base legale/contrattuale**: contratti fornitori, NDA, policy GDPR
- Chunk: per clausola
- Retrieval: hybrid search, priorità a documenti recenti

**FAQ prodotti/servizi**: risposte a domande frequenti, specifiche tecniche
- Chunk: coppia domanda-risposta
- Retrieval: semantic search puro

**Knowledge base tecnica** (ingegneria, IT): manuali, datasheet, norme tecniche
- Chunk: per sezione/articolo
- Metadata: `norma`, `rev`, `applicazione`

## Architettura K2-AI consigliata per PMI

```
Stack: Supabase pgvector + text-embedding-3-large + Claude 3.5 Haiku
Chunk: 600 token, overlap 80 token
Retrieval: hybrid (0.6 semantic + 0.4 BM25), top-10, rerank top-5
Costo stimato: < 20€/mese per 50k documenti, 1k query/giorno
```
