"""APISentry command-line scanner for CI/CD pipelines.

Runs a scan directly against a target (no backend needed) and can fail the build
when findings at or above a chosen severity are present.

Examples:
  python apisentry.py scan --spec targets/demopay_openapi.json --fail-on high
  python apisentry.py scan --spec spec.json --auth auth.json --report out.html
"""
import asyncio
import json
from pathlib import Path

import typer

from .services.owasp import SEVERITY_ORDER, severity_counts
from .services.reports import render_html
from .services.scanner import scan_target
from .services.spec_parser import parse_spec
from .services.validation import validate

app = typer.Typer(add_completion=False, help="APISentry API security scanner.")

_SEV = {"critical": "\033[91m", "high": "\033[93m", "medium": "\033[33m",
        "low": "\033[94m", "info": "\033[90m"}
_RESET = "\033[0m"


@app.callback()
def _main():
    """APISentry - automated OWASP API Top 10 security scanner."""


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


@app.command()
def scan(
    spec: Path = typer.Option(..., help="OpenAPI/Swagger or Postman collection file."),
    base_url: str = typer.Option(None, help="Override the base URL from the spec."),
    auth: Path = typer.Option(None, help="JSON file with an auth profile."),
    known: Path = typer.Option(None, help="JSON file with a known-vulnerability list."),
    fail_on: str = typer.Option(
        None, "--fail-on",
        help="Exit non-zero if a finding at or above this severity exists "
             "(critical|high|medium|low)."),
    report: Path = typer.Option(None, help="Write an HTML report to this path."),
    json_out: Path = typer.Option(None, "--json", help="Write findings JSON here."),
):
    """Scan an API described by SPEC and report OWASP API Top 10 findings."""
    spec_text = spec.read_text(encoding="utf-8")
    parsed_base, endpoints, kind = parse_spec(spec_text)
    target_base = (base_url or parsed_base or "").rstrip("/")
    if not target_base:
        typer.secho("Could not determine base URL; pass --base-url.", fg="red")
        raise typer.Exit(2)

    auth_profile = json.loads(auth.read_text(encoding="utf-8")) if auth else {}
    if "auth" in auth_profile:  # allow passing a *_vulns.json directly
        auth_profile = auth_profile["auth"]
    known_list = json.loads(known.read_text(encoding="utf-8")) if known else []
    if isinstance(known_list, dict):
        known_list = known_list.get("known_vulns", [])

    typer.echo(f"Scanning {target_base}  ({len(endpoints)} endpoints, spec: {kind})")
    result = asyncio.run(scan_target(target_base, endpoints, auth_profile))
    findings = [f for f in result["findings"] if f["severity"] != "info"]

    typer.secho(f"\nSecurity score: {result['score']}/100  (grade {result['grade']})",
                bold=True)
    counts = severity_counts(findings)
    typer.echo("  " + "  ".join(
        f"{_SEV.get(k,'')}{k}: {v}{_RESET}" for k, v in counts.items() if v) or "  clean")

    typer.echo("\nFindings:")
    for f in sorted(findings, key=lambda x: SEVERITY_ORDER.get(x["severity"], 9)):
        col = _SEV.get(f["severity"], "")
        typer.echo(f"  {col}[{f['severity'].upper():8}]{_RESET} "
                   f"{f['owasp_id']:5} {f['title']}")

    if known_list:
        v = validate(known_list, findings)
        typer.echo(f"\nValidation: detected {v['detected_count']}/{v['total_known']} "
                   f"known ({v['detection_rate']}%), "
                   f"{v['false_positive_count']} false positive(s).")

    if report:
        target = _Obj(name=spec.stem, base_url=target_base)
        scan_obj = _Obj(id=0, score=result["score"], grade=result["grade"])
        report.write_text(
            render_html(target, scan_obj, findings, [], "", "CLI run"),
            encoding="utf-8")
        typer.echo(f"HTML report written to {report}")
    if json_out:
        json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        typer.echo(f"Findings JSON written to {json_out}")

    if fail_on:
        threshold = SEVERITY_ORDER.get(fail_on.lower(), 0)
        worst = min((SEVERITY_ORDER.get(f["severity"], 9) for f in findings), default=9)
        if worst <= threshold:
            typer.secho(
                f"\nFAIL: findings at or above '{fail_on}' present -> exit 1", fg="red")
            raise typer.Exit(1)
        typer.secho(f"\nPASS: no findings at or above '{fail_on}'.", fg="green")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
