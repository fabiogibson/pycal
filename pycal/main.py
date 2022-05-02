#!/usr/bin/env python
import click
import arrow

from pycal import views
from pycal.config import Config
from pycal.api import EventStorage
from pycal.api.providers.google_calendar import GoogleCalendar

from pycal.app import PyCalendar


@click.group()
@click.pass_context
def cli(ctx):
    config = Config()
    config.FACTORIES["GoogleCalendar"] = GoogleCalendar.from_settings
    storage = EventStorage(config)
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
@click.option(
    "--join", default=False, is_flag=True, help="Remotely join the closest event."
)
def next(ctx, join):
    storage = ctx.obj["storage"]
    closest_event = storage.get_closest_event()

    if not closest_event or abs((arrow.now() - closest_event.start_time).days) > 1:
        click.echo("No upcoming events")
        return

    granularity = [
        "minute",
    ]

    if abs(closest_event.start_time - arrow.now()).total_seconds() / 60 >= 60:
        granularity.append("hour")

    click.echo(
        f"{closest_event.start_time.humanize(granularity=granularity)} - {closest_event.title}"
    )

    if join:
        storage.join_event(closest_event)


cli.add_command(agenda)
cli.add_command(next)


if __name__ == "__main__":
    cli()
