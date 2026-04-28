import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from plakar_search import __version__
from plakar_search.plakar_client import PlakarError

app = typer.Typer(
    name="plakar-search",
    help="Recherche semantique par contexte dans un store Plakar.",
)

console = Console()


@app.command()
def index(
    repo: str = typer.Argument(
        ...,
        help="Repository Plakar (@destination ou /chemin)",
    ),
    passphrase: str = typer.Option(
        None,
        "--passphrase",
        "-p",
        help="Passphrase pour les stores par chemin (optionnel pour @destinations)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Afficher les logs detailles (fichiers ignores, erreurs)",
    ),
) -> None:
    """Indexe tous les snapshots d'un store Plakar dans ChromaDB.

    Exemples :
        plakar-search index @gdrive
        plakar-search index /var/backups --passphrase "secret"
        plakar-search index @s3 --verbose
    """
    from plakar_search.indexer import Indexer

    try:
        indexer = Indexer(repo, passphrase=passphrase, verbose=verbose)
    except PlakarError as e:
        console.print(f"[bold red]Erreur :[/bold red] {e}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        try:
            indexer.index(progress=progress)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrompu.[/yellow]")
            raise typer.Exit(0)

    if indexer.interrupted:
        console.print("[yellow]Indexation interrompue. Relancez pour reprendre.[/yellow]")
    else:
        console.print("[bold green]Indexation terminee.[/bold green]")
