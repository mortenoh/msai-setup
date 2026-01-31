"""MS-S1 MAX CLI."""

import typer

app = typer.Typer(
    name="msai",
    help="MS-S1 MAX Home Server Setup CLI",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show version information."""
    from msai_setup import __version__

    typer.echo(f"msai-setup {__version__}")


@app.command()
def docs() -> None:
    """Serve documentation locally."""
    import subprocess

    subprocess.run(["mkdocs", "serve"], check=True)


if __name__ == "__main__":
    app()
