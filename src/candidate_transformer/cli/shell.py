import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console

from candidate_transformer.cli.commands import CommandDispatcher, workspace_manager
from candidate_transformer.cli.context import PipelineContext

console = Console()

COMMANDS = {
    "load": None,
    "build": None,
    "project": None,
    "status": None,
    "stats": None,
    "show": None,
    "sources": None,
    "projections": None,
    "connectors": None,
    "config": {"show": None, "begin": None, "set": None, "apply": None},
    "save": {"canonical": None},
    "loadcanonical": None,
    "export": None,
    "workspace": {"new": None, "open": None, "list": None, "delete": None},
    "server": {"start": None, "status": None, "stop": None},
    "help": None,
    "history": None,
    "reset": None,
    "clear": None,
    "exit": None
}

def main() -> None:
    console.print("[cyan bold]Candidate Transformer Shell[/cyan bold]")
    console.print("Version 1.0.1")
    
    # Initialize workspace
    # Load default or create it
    context = workspace_manager.load("default")
    if not context:
        context = PipelineContext(workspace_name="default")
        workspace_manager.save(context)
        
    console.print(f"Workspace: [green]{context.workspace_name}[/green]")
    console.print("Type [bold]HELP[/bold] for commands.\n")
    
    dispatcher = CommandDispatcher(context)
    
    history_file = os.path.expanduser("~/.ctsh_history")
    completer = NestedCompleter.from_nested_dict(COMMANDS)
    
    session: PromptSession[str] = PromptSession(
        history=FileHistory(history_file),
        completer=completer
    )
    
    while True:
        try:
            # We want prompt symbol in green, but prompt_toolkit uses its own styles.
            # Using rich to print prompt might interfere with prompt_toolkit input.
            # For simplicity, we just pass the raw string.
            # Prompt symbol is green, shell name cyan. We can format the prompt string using ANSI or prompt_toolkit FormattedText.
            from prompt_toolkit.formatted_text import HTML
            prompt_html = HTML('<ansicyan>ctsh</ansicyan><ansigreen>&gt; </ansigreen>')
            
            text = session.prompt(prompt_html)
            
            if not text.strip():
                continue
                
            if text.lower().strip() in ("exit", "quit"):
                break
                
            # Add to context history
            dispatcher.context.history.append(text)
            dispatcher.dispatch(text)
            
        except KeyboardInterrupt:
            # Ctrl-C
            continue
        except EOFError:
            # Ctrl-D
            break
        except Exception as e:
            console.print(f"[red]Fatal error:[/red] {str(e)}")

if __name__ == "__main__":
    main()
