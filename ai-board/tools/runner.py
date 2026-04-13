#!/usr/bin/env python3
"""
CLI runner per testare gli agenti individualmente.

Utilizzo:
  python -m tools.runner --agent content_engine --task "Scrivi un post LinkedIn sul caso studio del sito"
  python -m tools.runner --agent market_intelligence --task "Analizza il mercato B&B in Italia"
  python -m tools.runner --list
"""

import argparse
import json

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from db.models import AgentName

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Board — Agent Runner CLI")
    parser.add_argument("--agent", "-a", type=str, help="Nome agente (es: content_engine)")
    parser.add_argument("--task", "-t", type=str, help="Task da eseguire")
    parser.add_argument("--context", "-c", type=str, help="Contesto JSON opzionale")
    parser.add_argument("--list", "-l", action="store_true", help="Lista tutti gli agenti")
    args = parser.parse_args()

    from core.orchestrator import list_agents, resolve_agent_name, run_agent

    if args.list:
        console.print("\n[bold]Agenti disponibili:[/bold]")
        for name in list_agents():
            console.print(f"  • {name}")
        return

    if not args.agent or not args.task:
        parser.print_help()
        return

    from core.memory import load_memory

    load_memory()

    try:
        agent_name = resolve_agent_name(AgentName(args.agent))
    except ValueError:
        console.print(f"[red]Agente non trovato: {args.agent}[/red]")
        console.print("Usa --list per vedere gli agenti disponibili")
        return

    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            console.print("[yellow]Contesto JSON non valido — ignorato[/yellow]")

    console.print(
        Panel.fit(
            f"[bold]Agente:[/bold] {agent_name.value}\n"
            f"[bold]Task:[/bold] {args.task[:100]}{'...' if len(args.task) > 100 else ''}",
            title="Esecuzione",
            border_style="dim",
        )
    )

    result = run_agent(agent_name, args.task, context)

    if result["status"] == "error":
        console.print(f"\n[red]Errore:[/red] {result.get('error', 'Errore sconosciuto')}")
        return

    console.print(f"\n[green]Status:[/green] {result['status']}")
    console.print(f"[dim]Approval ID:[/dim] {result.get('approval_id', 'N/A')}")
    console.print(f"[dim]Durata:[/dim] {result.get('duration_ms', 0)}ms\n")

    output = result.get("output", "")
    if output:
        console.print(Panel(Markdown(output), title="Output (Draft)", border_style="green"))


if __name__ == "__main__":
    main()
