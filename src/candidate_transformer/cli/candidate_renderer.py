import json
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from candidate_transformer.domain.models import Candidate

console = Console()

class CandidateRenderer:
    def __init__(self, candidate: Candidate, verbose: bool = False):
        self.c = candidate
        self.verbose = verbose

    def _na(self) -> Text:
        return Text("N/A", style="dim")

    def _confidence_style(self, conf: float) -> str:
        if conf >= 0.9:
            return "green"
        if conf >= 0.7:
            return "yellow"
        return "red"

    def render(self) -> Group:
        sections = []

        # Header
        header = Text(f"\nCandidate #{self.c.candidate_id}\n{self.c.full_name}\n", style="bold cyan", justify="center")
        sections.append(header)

        # Section 1 - Basic Information
        sections.append(Text("Basic Information", style="bold green"))
        basic_table = Table(show_header=False, box=None)
        basic_table.add_column("Property", style="bold blue", width=22)
        basic_table.add_column("Value")
        
        basic_table.add_row("Candidate ID", str(self.c.candidate_id))
        basic_table.add_row("Name", str(self.c.full_name))
        basic_table.add_row("Headline", str(self.c.headline) if self.c.headline else self._na())
        basic_table.add_row("Experience", f"{self.c.years_experience} years" if self.c.years_experience else self._na())
        conf_str = f"{self.c.overall_confidence:.2f}"
        basic_table.add_row("Overall Confidence", Text(conf_str, style=self._confidence_style(self.c.overall_confidence)))
        sections.append(basic_table)
        sections.append(Text())

        # Section 2 - Contact
        if self.c.contact:
            sections.append(Text("Contact", style="bold green"))
            contact_table = Table(show_header=False, box=None)
            contact_table.add_column("Type", style="bold blue", width=14)
            contact_table.add_column("Value")
            
            emails = self.c.contact.emails
            if not emails:
                contact_table.add_row("Emails", self._na())
            else:
                contact_table.add_row("Emails", emails[0])
                for e in emails[1:]:
                    contact_table.add_row("", e)

            phones = self.c.contact.phones
            if not phones:
                contact_table.add_row("Phones", self._na())
            else:
                contact_table.add_row("Phones", phones[0])
                for p in phones[1:]:
                    contact_table.add_row("", p)
            
            loc_str = "N/A"
            if self.c.contact.location:
                l = self.c.contact.location
                parts = [p for p in [l.get("city"), l.get("region"), l.get("country")] if p]
                loc_str = ", ".join(parts) if parts else "N/A"
            contact_table.add_row("Location", loc_str if loc_str != "N/A" else self._na())
            
            sections.append(contact_table)
            sections.append(Text())

        # Section 3 - Links
        if self.c.links:
            sections.append(Text("Links", style="bold green"))
            links_table = Table(show_header=False, box=None)
            links_table.add_column("Platform", style="bold blue", width=12)
            links_table.add_column("URL")
            
            has_link = False
            for platform in ["linkedin", "github", "portfolio"]:
                url = getattr(self.c.links, platform, None)
                if url:
                    links_table.add_row(platform.title(), Text(url, style="blue underline"))
                    has_link = True
            
            for other_link in (self.c.links.other or []):
                links_table.add_row("Other", Text(other_link, style="blue underline"))
                has_link = True
                
            if not has_link:
                links_table.add_row("Links", self._na())
                
            sections.append(links_table)
            sections.append(Text())

        # Section 4 - Skills
        if self.c.skills:
            sections.append(Text("Skills", style="bold green"))
            skills_table = Table(box=None)
            skills_table.add_column("Skill", style="bold blue")
            skills_table.add_column("Confidence")
            skills_table.add_column("Sources")
            
            for skill in self.c.skills:
                conf = f"{skill.confidence:.2f}"
                conf_text = Text(conf, style=self._confidence_style(skill.confidence))
                sources = ",".join(skill.sources) if skill.sources else "unknown"
                skills_table.add_row(skill.name, conf_text, sources)
            sections.append(skills_table)
            sections.append(Text())

        # Section 5 - Experience
        if self.c.experience:
            sections.append(Text("Experience", style="bold green"))
            exp_table = Table(box=None)
            exp_table.add_column("Company", style="bold blue")
            exp_table.add_column("Title", style="bold blue")
            exp_table.add_column("From", style="bold blue")
            exp_table.add_column("To", style="bold blue")
            
            for exp in self.c.experience:
                start = str(exp.start) if exp.start else "N/A"
                end = str(exp.end) if exp.end else "N/A"
                comp = str(exp.company) if exp.company else "N/A"
                title = str(exp.title) if exp.title else "N/A"
                exp_table.add_row(comp, title, start, end)
                if exp.summary:
                    # Print summary indented and dim
                    exp_table.add_row("", Text(str(exp.summary), style="dim"), "", "")
            sections.append(exp_table)
            sections.append(Text())

        # Section 6 - Education
        if self.c.education:
            sections.append(Text("Education", style="bold green"))
            edu_table = Table(box=None)
            edu_table.add_column("Institution", style="bold blue")
            edu_table.add_column("Degree", style="bold blue")
            edu_table.add_column("Year", style="bold blue")
            
            for edu in self.c.education:
                inst = str(edu.institution) if edu.institution else "N/A"
                deg = str(edu.degree) if edu.degree else "N/A"
                if edu.field:
                    deg = f"{deg} {edu.field}".strip()
                year = str(edu.end_year) if edu.end_year else "N/A"
                edu_table.add_row(inst, deg, year)
            sections.append(edu_table)
            sections.append(Text())

        # Section 7 - Certifications
        if self.c.certifications:
            sections.append(Text("Certifications", style="bold green"))
            for cert in self.c.certifications:
                sections.append(Text(cert))
            sections.append(Text())

        # Section 8 - Projects
        if self.c.projects:
            sections.append(Text("Projects", style="bold green"))
            for p in self.c.projects:
                p_table = Table(show_header=False, box=None)
                p_table.add_column("Key", width=20)
                p_table.add_column("Value")
                
                name = p.name or "N/A"
                desc = p.description or ""
                techs = ", ".join(p.technologies) if p.technologies else ""
                
                # Top row uses name as key if we want, or "Name"
                if desc:
                    p_table.add_row(name, desc)
                else:
                    p_table.add_row(name, "")
                    
                if techs:
                    p_table.add_row("Technologies", techs)
                
                sections.append(Panel(p_table, border_style="dim"))
            sections.append(Text())

        # Section 9 - Languages
        if self.c.languages:
            sections.append(Text("Languages", style="bold green"))
            for lang in self.c.languages:
                sections.append(Text(lang))
            sections.append(Text())

        # Section 10 - Provenance
        if self.c.provenance:
            sections.append(Text("Provenance", style="bold green"))
            prov_table = Table(box=None)
            prov_table.add_column("Field", style="bold blue")
            prov_table.add_column("Source", style="bold blue")
            prov_table.add_column("Method", style="bold blue")
            prov_table.add_column("Conf", style="bold blue")
            if self.verbose:
                prov_table.add_column("Timestamp", style="bold blue")
                
            for prov in self.c.provenance:
                conf_str = f"{prov.confidence:.2f}"
                conf_text = Text(conf_str, style=self._confidence_style(prov.confidence))
                row = [prov.field, prov.source, prov.method, conf_text]
                if self.verbose:
                    row.append(prov.timestamp or "N/A")
                prov_table.add_row(*row)
            sections.append(prov_table)
            sections.append(Text())
            
        return Group(*sections)

def display_candidate(candidate: Candidate, as_json: bool = False, verbose: bool = False) -> None:
    if as_json:
        console.print(Panel(json.dumps(candidate.model_dump(), indent=2), title=candidate.full_name, border_style="blue"))
        return
        
    renderer = CandidateRenderer(candidate, verbose)
    console.print(Panel(renderer.render(), border_style="cyan"))
