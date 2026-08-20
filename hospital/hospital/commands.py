import click
import frappe
from hospital.setup import sync_workspaces as _sync_workspaces


@click.command("sync-hospital-workspaces")
def sync_hospital_workspaces():
	"""Sync Hospital Management workspaces into database."""
	_sync_workspaces()
	click.echo("Hospital workspaces synced successfully!")


commands = [sync_hospital_workspaces]