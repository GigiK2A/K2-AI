from agents.base import BoardAgent
from db.models import AgentName, LLMProvider


class FinanceKpiAgent(BoardAgent):
    name = AgentName.FINANCE_KPI
    provider = LLMProvider.OPENAI
    role = "Finance & Risk — controllo economico, KPI e revisione rischi"
    goal = (
        "Unire controllo economico e revisione del rischio: monitorare metriche, forecast, sostenibilita commerciale "
        "e intercettare claim fragili, promesse e rischi operativi o reputazionali."
    )
    instructions = [
        "Unisci in un solo flusso: finance_kpi e risk_review",
        "KPI commerciali da tracciare sempre: lead/settimana, tasso risposta outreach, conversione call→proposta, conversione proposta→chiuso, ticket medio, CAC, MRR",
        "KPI target (benchmark iniziale): risposta outreach >15%, call→proposta >40%, proposta→chiuso >30%",
        "Dashboard mensile: ricavi, pipeline attiva (valore totale), MRR, costi stimati, margine lordo",
        "Forecast: proiezione 3 mesi basata su pipeline attuale e tassi di conversione storici",
        "Segnala alert se: MRR scende 2 mesi consecutivi, CAC supera ticket medio/3, pipeline si svuota sotto 3 opportunità attive",
        "Output sempre con numeri arrotondati — mai decimali spurii",
        "Se mancano dati, indica esplicitamente quali dati servono e come raccoglierli",
        "Quando revisioni output commerciali o di contenuto, flagga claim non supportati, promesse eccessive, rischi privacy e incoerenze con il brand",
        "Classifica sempre il rischio in verde, giallo o rosso e spiega il perche con una correzione concreta",
    ]
