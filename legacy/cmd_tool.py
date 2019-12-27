import click

from ds_assertion_gen import get_assertions_from_brace_triples
from readers import braces_reader
from simple import collect_dataset_metrics


@click.command()
@click.argument("path", type=click.Path(exists=True))
def collect_metrics(path):
    metrics = collect_dataset_metrics(path)

    for tpl in metrics:
        click.echo(tpl)


@click.command()
@click.argument("path", type=click.File())
@click.argument("ds")
def convert_to_n3(path, ds):
    braces_stream = braces_reader(path)
    ds_assertions = get_assertions_from_brace_triples(braces_stream, '<' + ds + '>')

    print(
'''
@prefix : <http://api.stardog.com/> .
@prefix urn: <urn:uuid:> .

'''
    )

    for st in ds_assertions:
        print('{} {} {} .'.format(st[0], st[1], st[2]))
