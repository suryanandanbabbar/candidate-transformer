import json
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from candidate_transformer.api.transformer import CandidateTransformer
from candidate_transformer.cli.context import PipelineContext, DirtyState
from candidate_transformer.cli.workspace import WorkspaceManager

console = Console()
workspace_manager = WorkspaceManager()

class CommandDispatcher:
    def __init__(self, context: PipelineContext):
        self.context = context
        self.in_config_transaction = False
        
    def dispatch(self, cmd: str) -> None:
        if not cmd:
            return
            
        parts = cmd.split()
        command = parts[0].lower()
        args = parts[1:]
        
        try:
            if command == "load":
                self.handle_load(args)
            elif command == "build":
                self.handle_build()
            elif command == "project":
                self.handle_project(args)
            elif command == "status":
                self.handle_status()
            elif command == "stats":
                self.handle_stats()
            elif command == "show":
                self.handle_show(args)
            elif command == "sources":
                self.handle_sources()
            elif command == "projections":
                self.handle_projections()
            elif command == "connectors":
                self.handle_connectors()
            elif command == "config":
                self.handle_config(args)
            elif command == "save":
                self.handle_save(args)
            elif command == "loadcanonical":
                self.handle_loadcanonical(args)
            elif command == "export":
                self.handle_export(args)
            elif command == "workspace":
                self.handle_workspace(args)
            elif command in ("help", "?"):
                self.handle_help()
            elif command == "history":
                self.handle_history()
            elif command == "clear":
                console.clear()
            else:
                console.print(f"[red]Unknown command:[/red] {command}. Type 'help' for available commands.")
        except Exception as e:
            console.print(f"[red]Error executing command:[/red] {str(e)}")
            
    def handle_load(self, args: list[str]) -> None:
        if len(args) != 2:
            console.print("[red]Usage:[/red] load <connector> <file>")
            return
            
        connector, file_path = args
        self.context.loaded_sources.append((connector, file_path))
        self.context.mark_dirty(DirtyState.CANONICAL)
        console.print(f"[green]Loaded[/green] {connector} from {file_path}")
        
    def handle_build(self) -> None:
        if not self.context.loaded_sources:
            console.print("[yellow]No sources loaded. Run 'load' first.[/yellow]")
            return
            
        console.print("[blue]Building canonical dataset...[/blue]")
        engine = CandidateTransformer(self.context.runtime_config)
        
        for connector, file_path in self.context.loaded_sources:
            try:
                with open(file_path, "r") as f:
                    engine.load(connector, f)
            except FileNotFoundError:
                console.print(f"[red]File not found:[/red] {file_path}")
                return
                
        dataset = engine.build()
        self.context.dataset = dataset
        self.context.clear_dirty()
        workspace_manager.save(self.context)
        
        console.print(f"[green]Build {dataset.build_id} complete![/green]")
        console.print(f"Candidates generated: {len(dataset.candidates)}")
        console.print(f"Duration: {dataset.build_metadata.get('duration', 0):.2f}s")
        
    def handle_project(self, args: list[str]) -> None:
        if not args:
            console.print("[red]Usage:[/red] project <projection_name>")
            return
            
        if self.context.dirty_state in (DirtyState.CANONICAL, DirtyState.WORKSPACE):
            console.print("[yellow]Configuration changed. Canonical model is stale. Run BUILD.[/yellow]")
            return
            
        if self.context.dataset is None:
            console.print("[red]No canonical dataset built. Run 'build' first.[/red]")
            return
            
        proj_name = args[0]
        self.context.current_projection = proj_name
        self.context.mark_dirty(DirtyState.PROJECTION)
        workspace_manager.save(self.context)
        
        engine = CandidateTransformer(self.context.runtime_config)
        engine._dataset = self.context.dataset
        
        console.print(f"[blue]Projecting using[/blue] {proj_name}...")
        try:
            results = engine.project(proj_name)
            console.print(f"[green]Previewing first 10 candidates:[/green]")
            preview = results[:10]
            console.print(json.dumps(preview, indent=2))
        except Exception as e:
            console.print(f"[red]Projection failed:[/red] {str(e)}")

    def handle_status(self) -> None:
        table = Table(title="Pipeline Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Workspace", self.context.workspace_name)
        table.add_row("Loaded Sources", str(len(self.context.loaded_sources)))
        built = "Yes" if self.context.dataset else "No"
        table.add_row("Canonical Model Built?", built)
        if self.context.dataset:
            table.add_row("Build ID", self.context.dataset.build_id)
            table.add_row("Build Timestamp", self.context.dataset.build_timestamp)
            table.add_row("Candidate Count", str(len(self.context.dataset.candidates)))
        table.add_row("Current Projection", self.context.current_projection or "None")
        table.add_row("Dirty State", self.context.dirty_state.name)
        
        console.print(table)
        
    def handle_stats(self) -> None:
        if not self.context.dataset:
            console.print("[red]No canonical dataset built.[/red]")
            return
            
        stats = self.context.dataset.statistics
        table = Table(title=f"Statistics for {self.context.dataset.build_id}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for k, v in stats.items():
            if isinstance(v, float):
                table.add_row(k.replace("_", " ").title(), f"{v:.2f}")
            else:
                table.add_row(k.replace("_", " ").title(), str(v))
                
        console.print(table)

    def handle_show(self, args: list[str]) -> None:
        if not args:
            console.print("[red]Usage:[/red] show <Candidate ID or Name or Index>")
            return
            
        if not self.context.dataset or not self.context.dataset.candidates:
            console.print("[red]No canonical dataset built.[/red]")
            return
            
        query = " ".join(args)
        found = None
        
        if query.isdigit():
            idx = int(query)
            if 0 <= idx < len(self.context.dataset.candidates):
                found = self.context.dataset.candidates[idx]
        else:
            for c in self.context.dataset.candidates:
                if query.lower() in c.full_name.lower() or c.candidate_id == query:
                    found = c
                    break
                    
        if found:
            console.print(Panel(json.dumps(found.model_dump(), indent=2), title=found.full_name, border_style="blue"))
        else:
            console.print(f"[yellow]Candidate not found:[/yellow] {query}")

    def handle_sources(self) -> None:
        if not self.context.loaded_sources:
            console.print("[yellow]No sources loaded.[/yellow]")
            return
            
        table = Table(title="Loaded Sources")
        table.add_column("Connector", style="cyan")
        table.add_column("File Path", style="green")
        for c, f in self.context.loaded_sources:
            table.add_row(c, f)
        console.print(table)

    def handle_projections(self) -> None:
        proj_dir = os.path.join(os.getcwd(), "configs", "projections")
        if not os.path.exists(proj_dir):
            console.print("[yellow]No configs/projections directory found.[/yellow]")
            return
            
        files = [f for f in os.listdir(proj_dir) if f.endswith(".json")]
        if not files:
            console.print("[yellow]No projections found.[/yellow]")
            return
            
        table = Table(title="Available Projections")
        table.add_column("Name", style="cyan")
        for f in files:
            table.add_row(f.replace(".json", ""))
        console.print(table)

    def handle_connectors(self) -> None:
        from candidate_transformer.connectors import connector_registry
        table = Table(title="Available Connectors")
        table.add_column("Name", style="cyan")
        for name in connector_registry.all():
            table.add_row(name)
        console.print(table)

    def handle_config(self, args: list[str]) -> None:
        if not args:
            console.print("[red]Usage:[/red] config [show | set | begin | apply]")
            return
            
        subcmd = args[0].lower()
        if subcmd == "show":
            console.print(Panel(json.dumps(self.context.runtime_config.model_dump(), indent=2), title="Pipeline Configuration", border_style="cyan"))
        elif subcmd == "begin":
            self.in_config_transaction = True
            console.print("[green]Configuration transaction started. Use 'config apply' to commit.[/green]")
        elif subcmd == "apply":
            self.in_config_transaction = False
            workspace_manager.save(self.context)
            console.print("[green]Configuration applied.[/green]")
        elif subcmd == "set":
            if len(args) < 3:
                console.print("[red]Usage:[/red] config set <key> <value>")
                return
            key = args[1]
            value = args[2].lower()
            
            # Simple parsing for common types
            if value == "true": val = True
            elif value == "false": val = False
            else: val = args[2]
            
            if key == "include_confidence":
                self.context.runtime_config.output.include_confidence = val
                self.context.mark_dirty(DirtyState.PROJECTION)
            elif key == "include_provenance":
                self.context.runtime_config.output.include_provenance = val
                self.context.mark_dirty(DirtyState.PROJECTION)
            elif key == "on_missing":
                self.context.runtime_config.output.on_missing = val
                self.context.mark_dirty(DirtyState.PROJECTION)
            else:
                console.print(f"[yellow]Unknown config key (or unsupported for interactive edit):[/yellow] {key}")
                return
                
            console.print(f"[green]Set {key} = {val}[/green]")
            if not self.in_config_transaction:
                workspace_manager.save(self.context)
        else:
            console.print(f"[red]Unknown config subcommand:[/red] {subcmd}")

    def handle_save(self, args: list[str]) -> None:
        if len(args) < 2 or args[0] != "canonical":
            console.print("[red]Usage:[/red] save canonical <filename>")
            return
            
        if not self.context.dataset:
            console.print("[red]No canonical dataset built.[/red]")
            return
            
        filename = args[1]
        with open(filename, "w") as f:
            f.write(self.context.dataset.model_dump_json(indent=2))
        console.print(f"[green]Saved Canonical Dataset to[/green] {filename}")

    def handle_loadcanonical(self, args: list[str]) -> None:
        if not args:
            console.print("[red]Usage:[/red] loadcanonical <filename>")
            return
            
        filename = args[0]
        try:
            from candidate_transformer.domain.models import CanonicalDataset
            with open(filename, "r") as f:
                data = json.load(f)
                self.context.dataset = CanonicalDataset.model_validate(data)
                self.context.clear_dirty()
                workspace_manager.save(self.context)
            console.print(f"[green]Loaded Canonical Dataset from[/green] {filename}")
        except Exception as e:
            console.print(f"[red]Failed to load:[/red] {str(e)}")

    def handle_export(self, args: list[str]) -> None:
        if len(args) < 2:
            console.print("[red]Usage:[/red] export <projection_name> <filename>")
            return
            
        if self.context.dirty_state in (DirtyState.CANONICAL, DirtyState.WORKSPACE):
            console.print("[yellow]Configuration changed. Canonical model is stale. Run BUILD.[/yellow]")
            return
            
        if not self.context.dataset:
            console.print("[red]No canonical dataset built. Run 'build' first.[/red]")
            return
            
        proj_name, filename = args[0], args[1]
        engine = CandidateTransformer(self.context.runtime_config)
        engine._dataset = self.context.dataset
        try:
            engine.export(proj_name, filename)
            console.print(f"[green]Exported to[/green] {filename}")
        except Exception as e:
            console.print(f"[red]Export failed:[/red] {str(e)}")

    def handle_workspace(self, args: list[str]) -> None:
        if not args:
            console.print("[red]Usage:[/red] workspace [new|open|list|delete] [name]")
            return
            
        subcmd = args[0].lower()
        if subcmd == "list":
            workspaces = workspace_manager.list_workspaces()
            if not workspaces:
                console.print("No workspaces found.")
                return
            table = Table(title="Workspaces")
            table.add_column("Name", style="cyan")
            for w in workspaces:
                table.add_row(w + (" (active)" if w == self.context.workspace_name else ""))
            console.print(table)
        elif subcmd in ("new", "open"):
            if len(args) < 2:
                console.print(f"[red]Usage:[/red] workspace {subcmd} <name>")
                return
            name = args[1]
            loaded = workspace_manager.load(name)
            if loaded:
                self.context = loaded
                console.print(f"[green]Opened workspace:[/green] {name}")
            else:
                if subcmd == "open":
                    console.print(f"[yellow]Workspace not found:[/yellow] {name}")
                else:
                    self.context.workspace_name = name
                    self.context.mark_dirty(DirtyState.WORKSPACE)
                    workspace_manager.save(self.context)
                    console.print(f"[green]Created and opened workspace:[/green] {name}")
        elif subcmd == "delete":
            if len(args) < 2:
                console.print("[red]Usage:[/red] workspace delete <name>")
                return
            name = args[1]
            if name == self.context.workspace_name:
                console.print("[red]Cannot delete active workspace.[/red]")
                return
            if workspace_manager.delete_workspace(name):
                console.print(f"[green]Deleted workspace:[/green] {name}")
            else:
                console.print(f"[yellow]Workspace not found:[/yellow] {name}")
        else:
            console.print(f"[red]Unknown workspace subcommand:[/red] {subcmd}")

    def handle_help(self) -> None:
        help_text = """
[bold cyan]Loading[/bold cyan]
-------
load <connector> <file>

[bold cyan]Pipeline[/bold cyan]
--------
build
project <projection_name>

[bold cyan]Inspection[/bold cyan]
----------
status
stats
show <name|id|index>
sources
projections
connectors

[bold cyan]Configuration[/bold cyan]
-------------
config show
config begin
config set <key> <value>
config apply

[bold cyan]Persistence[/bold cyan]
-----------
save canonical <file>
loadcanonical <file>
export <projection_name> <file>

[bold cyan]Workspace[/bold cyan]
---------
workspace new <name>
workspace open <name>
workspace list
workspace delete <name>

[bold cyan]Utility[/bold cyan]
-------
help
history
clear
exit
"""
        console.print(Panel(help_text, title="Command Reference", border_style="blue"))
        
    def handle_history(self) -> None:
        for i, cmd in enumerate(self.context.history, 1):
            console.print(f"{i}: {cmd}")
