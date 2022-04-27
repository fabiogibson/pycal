#!/usr/bin/env python
import click
import arrow

from pycal import views
from pycal.api import EventStorage
from pycal.app import PyCalendar
from pycal.config import Config


@click.group()
@click.pass_context
def cli(ctx):
    config = Config()
    storage = EventStorage(list(config.calendars))
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["storage"] = storage


@click.command()
@click.pass_context
def agenda(ctx):
    agenda = views.Agenda(ctx.obj["storage"])

    PyCalendar.run(
        calendar_view=agenda,
        title="PyCal",
        config=ctx.obj["config"],
    )


@click.command()
@click.pass_context
def next(ctx):
    storage = ctx.obj["storage"]

    next_event = min(
        storage.get_events(),
        key=lambda e: abs((arrow.now() - e.start_time).total_seconds()),
    )

    if not next_event or abs((arrow.now() - next_event.start_time).days) > 1:
        click.echo("No upcoming events")
        return

    granularity = [
        "minute",
    ]

    if abs(next_event.start_time - arrow.now()).total_seconds() / 60 >= 60:
        granularity.append("hour")

    click.echo(
        f"{next_event.start_time.humanize(granularity=granularity)} - {next_event.title}"
    )


cli.add_command(agenda)
cli.add_command(next)


if __name__ == "__main__":
    cli()
