from typing import Any
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

from candidate_transformer.config.models import OutputConfig
from candidate_transformer.domain.models import Candidate

console = Console()

class ProjectionRenderer:
    def __init__(self, config: OutputConfig, candidates: list[Candidate]):
        self.config = config
        self.candidates = candidates

    def _na(self) -> Text:
        return Text("—", style="dim")
        
    def _format_val(self, val: Any, fmt: str | None) -> Text | str:
        if val is None or val == "":
            return self._na()
            
        if fmt == "len":
            if isinstance(val, list):
                return str(len(val))
            return "0"
            
        if fmt:
            try:
                # Basic string formatting
                return fmt.format(val=val)
            except Exception:
                return str(val)
                
        # Handle confidence specially across all projections
        if isinstance(val, float):
            return f"{val:.2f}"
            
        return str(val)
        
    def _confidence_style(self, conf: Any) -> str:
        try:
            val = float(conf)
            if val >= 0.90:
                return "green"
            if val >= 0.70:
                return "yellow"
            if val >= 0.50:
                return "orange3"
            return "red"
        except (ValueError, TypeError):
            return "default"

    def render_overview(self, results: list[dict[str, Any]]) -> Group:
        if not self.config.display:
            # Fallback if no display metadata
            table = Table(box=None)
            table.add_column("Result")
            for i, r in enumerate(results):
                table.add_row(f"Candidate {i}")
            return Group(Text("Projection Overview", style="bold magenta"), table)

        d = self.config.display
        title = Text(d.title, style="bold magenta")
        
        table = Table()
        table.add_column("#", style="bold cyan")
        
        # Add columns defined in metadata
        for col in d.overview_columns:
            table.add_column(col.header, style="bold blue")
            
        for idx, row in enumerate(results):
            canonical = self.candidates[idx]
            row_data = [str(idx)]
            for col in d.overview_columns:
                
                # Special logic for Candidate Name Lookup
                if col.header == "Candidate":
                    # Look for explicit mapped name
                    name_val = row.get(col.path)
                    # If not present or it's a UUID, replace with canonical name
                    if not name_val or str(name_val).count("-") == 4: 
                        name_val = canonical.full_name
                    row_data.append(Text(str(name_val)))
                    continue
                    
                val = row.get(col.path)
                formatted = self._format_val(val, col.format)
                
                if "Experience" in col.header and formatted != self._na():
                    formatted = Text(str(formatted), style="yellow")
                    
                if "Confidence" in col.header and val is not None:
                    formatted = Text(str(formatted), style=self._confidence_style(val))
                    
                row_data.append(formatted)
                
            table.add_row(*row_data)
            
        return Group(title, table)

    def render_detail(self, result: dict[str, Any], index: int) -> Group:
        canonical = self.candidates[index]
        if not self.config.display:
            return Group(Text(f"Candidate {index}", style="bold cyan"))
            
        d = self.config.display
        sections = []
        
        header = Text(f"\n{d.title}\nCandidate #{index}\n", style="bold cyan", justify="center")
        sections.append(header)
        
        for sec in d.detail_sections:
            if sec.title == "Data Quality":
                sections.append(Text("Data Quality", style="bold magenta"))
                t = Table(show_header=False, box=None)
                t.add_column("Key", style="bold blue", width=25)
                t.add_column("Value")
                
                # Dynamic counters from list paths
                for f in sec.fields:
                    val = result.get(f["path"])
                    count = len(val) if isinstance(val, list) else 0
                    if f["path"] == "provenance":
                        t.add_row(f["label"], f"{count} entries")
                    else:
                        t.add_row(f["label"], str(count))
                        
                sections.append(t)
                
                conf_val = result.get("overall_confidence", 0)
                sections.append(Text("Confidence Meter", style="bold blue"))
                p = Progress(
                    BarColumn(bar_width=20, style="dim", complete_style=self._confidence_style(conf_val)),
                    TextColumn("{task.percentage:>3.0f}%")
                )
                p.add_task("", total=100, completed=conf_val * 100)
                sections.append(p)
                sections.append(Text("──────────────────────────────", style="dim"))
                continue

            if sec.fields:
                sections.append(Text(sec.title, style="bold magenta"))
                t = Table(show_header=False, box=None)
                t.add_column("Key", style="bold blue", width=25)
                t.add_column("Value")
                
                for f in sec.fields:
                    val = result.get(f["path"])
                    if f["label"] == "Name" and not val:
                        val = canonical.full_name
                        
                    fmt = f.get("format")
                    formatted = self._format_val(val, fmt)
                    
                    if "Experience" in f["label"] and formatted != self._na():
                        formatted = Text(str(formatted), style="yellow")
                    if "Confidence" in f["label"] and val is not None:
                        formatted = Text(str(formatted), style=self._confidence_style(val))
                        
                    t.add_row(f["label"], formatted)
                    
                sections.append(t)
                sections.append(Text("──────────────────────────────", style="dim"))
                
            elif sec.list_path:
                val = result.get(sec.list_path)
                if val and isinstance(val, list):
                    sections.append(Text(sec.title, style="bold magenta"))
                    
                    if sec.list_path == "provenance":
                        prov_map: dict[str, set[str]] = {}
                        for p in val:
                            if isinstance(p, dict):
                                field = p.get("field", "unknown")
                                source = p.get("source", "unknown")
                                if field not in prov_map:
                                    prov_map[field] = set()
                                prov_map[field].add(source)
                                
                        ptable = Table(show_header=False, box=None)
                        ptable.add_column("Field", style="bold blue", width=25)
                        ptable.add_column("Sources")
                        for k, v in sorted(prov_map.items()):
                            ptable.add_row(k.title().replace("_", " "), ", ".join(sorted(v)))
                        sections.append(ptable)
                    else:
                        for item in val:
                            sections.append(Text(str(item)))
                    
                    sections.append(Text("──────────────────────────────", style="dim"))

        return Group(*sections)

def display_projection_overview(results: list[dict[str, Any]], config: OutputConfig, candidates: list[Candidate]) -> None:
    renderer = ProjectionRenderer(config, candidates)
    console.print(renderer.render_overview(results))

def display_projection_detail(result: dict[str, Any], index: int, config: OutputConfig, candidates: list[Candidate]) -> None:
    renderer = ProjectionRenderer(config, candidates)
    console.print(renderer.render_detail(result, index))
