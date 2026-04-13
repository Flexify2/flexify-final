import typer
from app.database import get_cli_session, create_db_and_tables
import app.models  # noqa - registers all models

app_cli = typer.Typer()

@app_cli.command()
def init_db():
    """Create all tables."""
    create_db_and_tables()
    typer.echo("Database initialised.")

@app_cli.command()
def seed():
    """Seed the database with an admin user only."""
    from app.models.user import User
    from app.utilities.security import encrypt_password
    from sqlmodel import select

    create_db_and_tables()

    with get_cli_session() as session:
        # Create bob admin
        existing = session.exec(select(User).where(User.username == "bob")).one_or_none()
        if not existing:
            bob = User(username="bob", email="bob@flexify.com", password=encrypt_password("bobpass"), role="admin")
            session.add(bob)
            session.commit()
            typer.echo("Created admin user: bob / bobpass")
        else:
            typer.echo("User 'bob' already exists")

        typer.echo("Seed complete (admin user only)")

if __name__ == "__main__":
    app_cli()
