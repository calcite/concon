# -*- coding: utf-8 -*-

"""Console script for concon."""

import click


@click.command()
def main(args=None):
    """Tool for configuration of Devices implementing "Uniprot" communication 
    layer over USB (HID profile).
    """
    click.echo("Replace this message by putting your code into "
               "concon.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")


if __name__ == "__main__":
    main()
