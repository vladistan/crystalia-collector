import click

from simple import collect_dataset_metrics


@click.command()
@click.argument("path", type=click.Path(exists=True))
def collect_metrics(path):
    metrics = collect_dataset_metrics(path)

    for tpl in metrics:
        click.echo(tpl)

