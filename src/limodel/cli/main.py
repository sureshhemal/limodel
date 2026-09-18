"""Terminal commands."""

import typer

app = typer.Typer(help="Find the best electrodialysis setup for Li selectivity over Mg.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
