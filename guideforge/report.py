from dataclasses import dataclass, field


@dataclass
class Issue:
    stage: str
    message: str
    level: str = "error"


@dataclass
class Report:
    stage: str
    issues: list = field(default_factory=list)
    stats: str = ""

    @property
    def errors(self):
        return [i for i in self.issues if i.level == "error"]

    @property
    def ok(self):
        return not self.errors


def render(reports):
    lines = []
    for r in reports:
        status = "PASS" if r.ok else "FAIL"
        lines.append(f"{status}  {r.stage:<13}{r.stats}")
        for i in r.issues:
            lines.append(f"      - {i.message}")
    return "\n".join(lines)
