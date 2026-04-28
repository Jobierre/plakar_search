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
from rich.table import Table

from plakar_search import __version__
from plakar_search.config import DEFAULT_LIMIT
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


@app.command()
def query(
    repo: str = typer.Argument(
        ...,
        help="Repository Plakar (@destination ou /chemin)",
    ),
    query_text: str = typer.Argument(
        ...,
        help="Requete en langage naturel",
    ),
    snapshot: str = typer.Option(
        None,
        "--snapshot",
        "-s",
        help="Filtrer par snapshot (id tronque accepte)",
    ),
    type_filter: str = typer.Option(
        None,
        "--type",
        "-t",
        help="Limiter la recherche : text ou images",
    ),
    limit: int = typer.Option(
        DEFAULT_LIMIT,
        "--limit",
        "-n",
        help="Nombre maximum de resultats",
    ),
) -> None:
    """Recherche des fichiers par contexte semantique.

    Exemples :
        plakar-search query @gdrive "photos de vacances"
        plakar-search query @s3 --type images "chien"
        plakar-search query @gdrive --snapshot abc1234 "rapport"
        plakar-search query @gdrive -n 10 "configuration"
    """
    from plakar_search.searcher import Searcher

    searcher = Searcher(repo)
    results = searcher.search(
        query=query_text,
        limit=limit,
        type_filter=type_filter,
        snapshot_filter=snapshot,
    )

    if not results:
        console.print("[yellow]Aucun resultat trouve.[/yellow]")
        return

    table = Table(title=f"Resultats pour : [bold]{query_text}[/bold]")
    table.add_column("Score", justify="right", style="cyan", width=8)
    table.add_column("Snapshot", style="dim", width=10)
    table.add_column("Path", style="white")
    table.add_column("Type", style="magenta", width=8)

    for r in results:
        table.add_row(
            f"{r['score']:.2f}",
            r["snapshot_id"][:8],
            r["path"],
            r["type"],
        )

    console.print(table)


@app.command()
def status(
    repo: str = typer.Argument(
        None,
        help="Repository Plakar (@destination ou /chemin). Si omis, liste tous les stores indexes.",
    ),
) -> None:
    """Affiche l'etat d'indexation d'un ou plusieurs stores.

    Exemples :
        plakar-search status @gdrive
        plakar-search status
    """
    if repo:
        _show_store_status(repo)
    else:
        _show_all_stores()


def _show_store_status(repo: str) -> None:
    from plakar_search.config import store_state_path
    from plakar_search.state import IndexState
    from plakar_search.store import VectorStore

    state = IndexState.load(repo, store_state_path(repo))

    try:
        store = VectorStore(repo)
        text_count = store.count_text()
        image_count = store.count_images()
    except Exception:
        text_count = 0
        image_count = 0

    if not state.snapshots:
        console.print(f"[yellow]Store '{repo}' non encore indexe.[/yellow]")
        return

    table = Table(title=f"Statut : [bold]{repo}[/bold]")
    table.add_column("Propriete", style="cyan")
    table.add_column("Valeur", style="white")

    table.add_row("Snapshots indexes", f"{state.done_count} / {state.total_count}")
    table.add_row(
        "Derniere mise a jour",
        state.last_updated[:19] if state.last_updated else "jamais",
    )
    table.add_row("Entrees texte", str(text_count))
    table.add_row("Entrees image", str(image_count))
    table.add_row(
        "Progression",
        f"{state.done_count}/{state.total_count} snapshots",
    )

    console.print(table)


def _show_all_stores() -> None:
    from plakar_search.config import STORES_DIR
    from plakar_search.state import IndexState

    if not STORES_DIR.exists():
        console.print(
            "[yellow]Aucun store indexe. Lancez 'plakar-search index <store>' d'abord.[/yellow]"
        )
        return

    store_dirs = sorted(
        [d for d in STORES_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    if not store_dirs:
        console.print("[yellow]Aucun store indexe.[/yellow]")
        return

    table = Table(title="Stores indexes")
    table.add_column("Store", style="cyan")
    table.add_column("Snapshots", justify="right")
    table.add_column("Progression")
    table.add_column("Derniere MAJ")

    for store_dir in store_dirs:
        state_path = store_dir / "state.json"
        if state_path.exists():
            state = IndexState.load(store_dir.name, state_path)
            done = state.done_count
            total = state.total_count
            prog = f"{done}/{total}" if total else "0/0"
            last = state.last_updated[:10] if state.last_updated else "-"
            table.add_row(store_dir.name, str(done), prog, last)
        else:
            table.add_row(store_dir.name, "0", "non indexe", "-")

    console.print(table)
