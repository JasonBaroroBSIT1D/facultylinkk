"""Flask CLI commands."""

from __future__ import annotations

import getpass
import sys

import click
from flask.cli import with_appcontext

from auth.services import validate_password_strength
from extensions import db
from models import User


@click.command("create-administrator")
@click.option("--email", prompt=True, help="Administrator email address")
@click.option("--full-name", prompt="Full name", help="Display name")
@with_appcontext
def create_administrator(email: str, full_name: str) -> None:
    """
    Create the first (or additional) administrator account interactively.
    Password is read from the terminal and never stored in source control.
    """
    normalized = email.strip().lower()
    if User.query.filter_by(role="administrator").first():
        click.echo(
            "An administrator account already exists. "
            "Use that account after staff-management APIs are available.",
            err=True,
        )
        sys.exit(1)

    duplicate = User.query.filter(db.func.lower(User.email) == normalized).first()
    if duplicate:
        click.echo("A user with that email already exists.", err=True)
        sys.exit(1)

    while True:
        password = getpass.getpass("Administrator password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            click.echo("Passwords do not match. Try again.", err=True)
            continue
        strength = validate_password_strength(password)
        if strength:
            click.echo(strength, err=True)
            continue
        break

    user = User(
        email=normalized,
        role="administrator",
        full_name=full_name.strip(),
        is_active=True,
        must_change_password=False,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Administrator created: {user.public_id} ({user.email})")
