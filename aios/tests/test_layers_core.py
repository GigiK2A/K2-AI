from aios.kernel import Kernel
from aios.tools import Tool
from aios.founder import default_founder_model
from aios.layers.context import ContextLayer
from aios.layers.data import DataLayer


def test_context_layer_includes_founder_and_knowledge():
    ctx = ContextLayer(founder=default_founder_model(),
                       knowledge=["Caso X: vinto in 30 giorni", "Norma Y si applica"])
    blob = ctx.assemble()
    assert "PMI" in blob
    assert "Caso X" in blob


def test_data_layer_unified_view_reads_registered_sensors():
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"Servizio": "A"}]))
    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
                         run=lambda **_: {"followers_count": 5}))
    view = DataLayer(k).vista_unica()
    assert view["servizi"] == [{"Servizio": "A"}]
    assert view["profilo_ig"]["followers_count"] == 5
    assert "leggi_inesistente" not in view
