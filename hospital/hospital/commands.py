import click
import frappe
from hospital.setup import sync_workspaces as _sync_workspaces


@click.command("sync-hospital-workspaces")
def sync_hospital_workspaces():
	"""Sync Hospital Management workspaces into database."""
	_sync_workspaces()
	click.echo("Hospital workspaces synced successfully!")

@click.command("hospital_hello")
def hospital_hello():
    click.echo("Hello from Hospital Management System!")

@click.command("hospital-greet")
@click.argument("name")
def hospital_greet(name):
	click.echo("Hello, " + name + " from Hospital Management System!")


commands = [sync_hospital_workspaces, hospital_hello, hospital_greet]