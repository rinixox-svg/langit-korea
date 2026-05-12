from pathlib import Path
from loguru import logger
import typer

from main import Orchestrator
from config.settings import settings

app = typer.Typer(
    name="epstopik",
    help="Forensic EPS-TOPIK workbook scraper with full audit trail",
)


@app.command()
def scrape(
    start_page: int = typer.Option(1, "--start-page", "-s", help="First page to scrape"),
    max_pages: int = typer.Option(0, "--max-pages", "-m", help="Max pages (0=unlimited)"),
    force_screenshot: bool = typer.Option(False, "--screenshot", "-ss", help="Force screenshot on every page"),
):
    """Run the full scrape pipeline: list → detail → download → audit."""
    logger.add(
        settings.ARTIFACTS_DIR / "scrape.log",
        rotation="100 MB",
        retention="30 days",
        level="INFO",
    )
    logger.info(f"Starting scrape: page {start_page}, max={max_pages or 'unlimited'}")

    orch = Orchestrator()
    if force_screenshot:
        logger.info("Screenshot mode enabled (every page will be captured)")

    try:
        orch.run(start_page=start_page, max_pages=max_pages)
        logger.info("Scrape completed successfully")
        typer.echo("[OK] Scrape complete. Run: epstopik verify")
    except Exception as e:
        logger.exception(f"Scrape failed: {e}")
        typer.echo(f"[FAIL] Scrape failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def verify():
    """Verify downloaded file integrity against SHA256 records."""
    logger.info("Running integrity verification")
    orch = Orchestrator()
    mismatches = orch.verify_integrity()
    if not mismatches:
        typer.echo("[OK] All files verified (SHA256 matches)")
    else:
        typer.echo(f"[WARN] Found {len(mismatches)} integrity issues:")
        for m in mismatches:
            typer.echo(f"  - [{m['status']}] {m['path']}")


@app.command()
def report():
    """Generate audit manifest JSON from provenance database."""
    logger.info("Generating audit report")
    orch = Orchestrator()
    report = orch.generate_report()
    path = settings.ARTIFACTS_DIR / "audit_manifest.json"
    typer.echo(f"[OK] Audit report saved: {path}")
    typer.echo(f"   Jobs: {len(report['jobs'])}")
    total_files = sum(len(j.get("files", [])) for j in report["jobs"])
    typer.echo(f"   Files: {total_files}")


if __name__ == "__main__":
    app()
