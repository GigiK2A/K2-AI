"""Memoria conversazionale: finestra a budget, sintesi progressiva, prompt caching.

Copre le tre cose introdotte insieme (erano lo stesso difetto visto da tre lati):
- `build_history` — messaggi INTERI dentro un budget, invece di 12 troncati a 900 char;
- `conversation_memory` — ciò che esce dalla finestra sopravvive in una sintesi;
- `build_system_blocks` — il prefisso stabile è isolato e marcato per la cache.
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover
    from supabase import Client as _ProbeClient  # noqa: F401
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib import conversation_memory as cm  # noqa: E402
from app.lib import conversations_index as ci  # noqa: E402
from app.lib.prompts import (  # noqa: E402
    append_system_text,
    build_history,
    build_system_blocks,
    build_system_prompt_v2,
)


def _msgs(n: int, size: int = 100) -> list:
    out = []
    for i in range(n):
        out.append({"role": "user", "content": f"u{i} " + "x" * size})
        out.append({"role": "assistant", "content": f"a{i} " + "y" * size})
    return out


# ---------------------------------------------------------------------------
# build_history — finestra a budget
# ---------------------------------------------------------------------------

def test_history_keeps_messages_whole_under_the_cap():
    msgs = [{"role": "user", "content": "x" * 3000}, {"role": "assistant", "content": "y" * 3000}]
    out = build_history(msgs, max_messages=40, max_chars_per_message=6000, char_budget=60000)
    assert [len(m["content"]) for m in out] == [3000, 3000], "messaggi troncati sotto il tetto"


def test_history_truncates_only_what_exceeds_the_per_message_cap():
    out = build_history([{"role": "user", "content": "x" * 9000}],
                        max_messages=40, max_chars_per_message=1000, char_budget=60000)
    assert len(out) == 1
    assert len(out[0]["content"]) == 1000
    assert out[0]["content"].endswith("…")


def test_history_respects_char_budget_and_keeps_the_most_recent():
    msgs = _msgs(20, size=500)  # 40 messaggi da ~504 char
    out = build_history(msgs, max_messages=40, max_chars_per_message=6000, char_budget=3000)
    assert sum(len(m["content"]) for m in out[:-1]) <= 3000
    # Tiene la CODA della conversazione, non la testa.
    assert out[-1]["content"].startswith("a19")


def test_history_always_includes_the_last_message_even_over_budget():
    out = build_history([{"role": "user", "content": "x" * 5000}],
                        max_messages=40, max_chars_per_message=6000, char_budget=10)
    assert len(out) == 1, "il turno corrente deve entrare comunque"


def test_history_starts_with_a_user_turn():
    # Un budget che taglia a metà turno può far cadere la finestra su un assistant:
    # l'API rifiuta una conversazione che apre così.
    msgs = _msgs(10, size=400)
    for budget in (500, 900, 1300, 1700, 2100):
        out = build_history(msgs, max_messages=40, max_chars_per_message=6000,
                            char_budget=budget)
        if out:
            assert out[0]["role"] == "user", f"budget={budget} apre con {out[0]['role']}"


def test_history_drops_invalid_roles_and_empty_messages():
    msgs = [
        {"role": "system", "content": "vietato"},
        {"role": "user", "content": "   "},
        {"role": "user", "content": "buono"},
        {"role": "tool", "content": "vietato"},
    ]
    out = build_history(msgs, max_messages=40, max_chars_per_message=6000, char_budget=60000)
    assert out == [{"role": "user", "content": "buono"}]


def test_history_respects_max_messages_as_upper_bound():
    out = build_history(_msgs(50, size=10), max_messages=6, max_chars_per_message=6000,
                        char_budget=10**9)
    assert len(out) <= 6


# ---------------------------------------------------------------------------
# conversation_memory — sintesi progressiva
# ---------------------------------------------------------------------------

def test_summary_not_stale_while_everything_fits_in_the_window():
    assert cm.is_stale({}, total_messages=8, window_len=8) is False


def test_summary_stale_once_enough_messages_left_the_window():
    # 20 messaggi totali, finestra 6 → 14 fuori, nessuno riassunto.
    assert cm.is_stale({}, total_messages=20, window_len=6) is True


def test_summary_not_stale_again_right_after_being_written():
    collected = {"rolling_summary": {"text": "sintesi", "upto": 14}}
    assert cm.is_stale(collected, total_messages=20, window_len=6) is False


def test_summary_block_is_empty_without_a_summary():
    assert cm.render_block({}) == ""
    assert cm.render_block({"rolling_summary": {"text": "  ", "upto": 3}}) == ""


def test_summary_block_carries_the_text_and_the_precedence_rule():
    block = cm.render_block({"rolling_summary": {"text": "fatturato 2M", "upto": 4}})
    assert "fatturato 2M" in block
    assert "vale ciò che dice ora" in block, "manca la regola di precedenza sull'ultimo turno"


class _FakeClient:
    """Client Anthropic finto: registra la chiamata e restituisce un testo fisso."""

    def __init__(self, text="- fatturato 2M\n- vuole uscire dalla società"):
        self.text = text
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        block = types.SimpleNamespace(type="text", text=self.text)
        return types.SimpleNamespace(content=[block])


def test_summary_build_covers_only_what_left_the_window():
    msgs = _msgs(10, size=50)  # 20 messaggi
    client = _FakeClient()
    entry = cm.build(client, "m", msgs, {}, window_len=6)
    assert entry["upto"] == 14
    assert "fatturato 2M" in entry["text"]
    # Nel prompt entrano solo i messaggi usciti dalla finestra, non tutta la conversazione.
    sent = client.calls[0]["messages"][0]["content"]
    assert "u0" in sent and "u6" in sent
    assert "u9" not in sent, "nel riassunto sono finiti messaggi ancora visibili"


def test_summary_build_is_incremental_not_from_scratch():
    """Si riparte da dove finiva la sintesi precedente: rimandare al modello i messaggi
    già riassunti è spreco che cresce con la conversazione."""
    msgs = _msgs(10, size=50)  # 20 messaggi
    client = _FakeClient()
    cm.build(client, "m", msgs, {"rolling_summary": {"text": "vecchia", "upto": 10}},
             window_len=6)
    sent = client.calls[0]["messages"][0]["content"]
    assert "u0" not in sent and "u4" not in sent, "rimandati messaggi già riassunti"
    assert "u5" in sent or "u6" in sent, "la fetta nuova non è stata mandata"


def test_summary_build_noop_when_previous_already_covers_everything():
    client = _FakeClient()
    out = cm.build(client, "m", _msgs(10), {"rolling_summary": {"text": "x", "upto": 14}},
                   window_len=6)
    assert out is None
    assert client.calls == [], "chiamata al modello senza niente di nuovo da riassumere"


def test_summary_transcript_is_bounded_and_reports_what_it_covered():
    """Il payload non deve crescere senza limiti: oltre il tetto si copre meno e `upto`
    lo dice, così il refresh successivo riprende da lì invece di fallire per sempre."""
    huge = [{"role": "user", "content": "z" * 30000} for _ in range(40)]
    client = _FakeClient()
    entry = cm.build(client, "m", huge, {}, window_len=0)
    sent = client.calls[0]["messages"][0]["content"]
    assert len(sent) < 60000, f"transcript non limitato: {len(sent)} char"
    assert 0 < entry["upto"] < 40, "upto deve riflettere solo ciò che è stato incluso"


def test_summary_makes_progress_across_refreshes_on_a_huge_conversation():
    """Rigenerazioni successive devono avanzare, non ripresentare la stessa fetta."""
    huge = [{"role": "user", "content": "z" * 30000} for _ in range(60)]
    client = _FakeClient()
    collected = {}
    seen = []
    for _ in range(3):
        entry = cm.build(client, "m", huge, collected, window_len=0)
        assert entry is not None
        seen.append(entry["upto"])
        collected = {"rolling_summary": entry}
    assert seen == sorted(seen) and len(set(seen)) == 3, f"nessun avanzamento: {seen}"


def test_summary_build_feeds_the_previous_summary_back_in():
    client = _FakeClient()
    cm.build(client, "m", _msgs(10, size=50),
             {"rolling_summary": {"text": "PRECEDENTE", "upto": 4}}, window_len=6)
    assert "PRECEDENTE" in client.calls[0]["messages"][0]["content"]


def test_summary_build_is_fail_open_on_client_error():
    class _Boom:
        def __init__(self):
            self.messages = self

        def create(self, **kwargs):
            raise RuntimeError("upstream down")

    assert cm.build(_Boom(), "m", _msgs(10), {}, window_len=6) is None


def test_summary_build_noop_when_nothing_left_the_window():
    client = _FakeClient()
    assert cm.build(client, "m", _msgs(2), {}, window_len=99) is None
    assert client.calls == []


# ---------------------------------------------------------------------------
# prompt caching — blocco stabile isolato
# ---------------------------------------------------------------------------

def _session() -> dict:
    return {"messages": [{"role": "user", "content": "ciao"}], "collected_data": {}}


def test_system_blocks_and_string_carry_the_same_content():
    blocks = build_system_blocks([], _session(), required_fields_hint="")
    as_string = build_system_prompt_v2([], _session(), required_fields_hint="")
    assert "\n\n".join(b["text"] for b in blocks) == as_string


def test_cache_control_only_on_the_stable_block():
    blocks = build_system_blocks([], _session(), required_fields_hint="")
    # L'ultimo blocco è quello volatile: mai marcato, cambia ogni turno.
    assert "cache_control" not in blocks[-1]


def test_skill_bundle_is_the_first_block_and_is_the_cached_one(monkeypatch):
    """Il bundle skill deve stare PRIMO e essere l'unico marcato per la cache.

    L'ordine non è estetico: un prefisso cacheabile fa hit solo se sta all'inizio, e
    qualunque byte che lo precede e cambia ogni turno (il gate di fase, lo stato
    diagnostico, i chunk RAG) lo invaliderebbe.
    """
    import app.lib.prompts as prompts

    monkeypatch.setattr(prompts, "load_skill_bundle", lambda *a, **k: "BUNDLE-SKILL")
    blocks = build_system_blocks(["qualsiasi"], _session(), required_fields_hint="")
    assert len(blocks) == 2
    assert blocks[0]["text"] == "BUNDLE-SKILL"
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in blocks[1]
    assert "K-BOT" in blocks[1]["text"], "il prompt volatile deve contenere il base prompt"


def test_append_system_text_never_touches_the_cached_prefix():
    blocks = [
        {"type": "text", "text": "STABILE", "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "VOLATILE"},
    ]
    out = append_system_text(blocks, " +extra")
    assert out[0] == blocks[0], "il prefisso cacheato è stato modificato"
    assert out[-1]["text"] == "VOLATILE +extra"
    # E non muta l'input.
    assert blocks[-1]["text"] == "VOLATILE"


def test_append_system_text_is_a_noop_on_empty_text():
    blocks = [{"type": "text", "text": "V"}]
    assert append_system_text(blocks, "") is blocks


def test_rolling_summary_reaches_the_system_prompt():
    session = _session()
    session["collected_data"] = {"rolling_summary": {"text": "il socio vuole uscire", "upto": 4}}
    assert "il socio vuole uscire" in build_system_prompt_v2([], session,
                                                            required_fields_hint="")


# ---------------------------------------------------------------------------
# conversations_index — titolo e sessioni orfane
# ---------------------------------------------------------------------------

def test_title_comes_from_the_first_user_message():
    session = {"messages": [
        {"role": "assistant", "content": "benvenuto"},
        {"role": "user", "content": "  ho   un problema\ncon il socio  "},
    ]}
    assert ci.derive_title(session) == "ho un problema con il socio"


def test_title_falls_back_to_the_deliverable_label():
    session = {"messages": [], "collected_data": {"deliverable_label": "FinanceBoost"}}
    assert ci.derive_title(session) == "FinanceBoost"


def test_title_is_empty_when_nothing_is_derivable():
    assert ci.derive_title({"messages": [], "collected_data": {}}) == ""


def test_missing_table_error_is_recognised():
    assert ci.is_missing_table_error(Exception("PGRST205 something")) is True
    assert ci.is_missing_table_error(Exception("Could not find the table 'x'")) is True
    assert ci.is_missing_table_error(Exception("connection reset")) is False
