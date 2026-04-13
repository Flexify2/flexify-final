import typer
from app.database import get_cli_session, create_db_and_tables
import app.models  # noqa - registers all models

app_cli = typer.Typer()

@app_cli.command()
def init_db():
    """Create all tables."""
    create_db_and_tables()
    typer.echo("✅ Database initialised.")

@app_cli.command()
def seed():
    """Seed the database with a bob admin user and sample workouts."""
    from app.models.user import User
    from app.models.workout import Workout
    from app.utilities.security import encrypt_password
    from sqlmodel import select

    create_db_and_tables()

    WORKOUTS = [
        dict(name="Barbell Bench Press", description="Classic chest compound movement using a barbell on a flat bench.", muscle_group="Chest", difficulty="Intermediate", duration_minutes=45, equipment="Barbell, Bench"),
        dict(name="Push-Up", description="Bodyweight exercise that targets the chest, shoulders, and triceps.", muscle_group="Chest", difficulty="Beginner", duration_minutes=20, equipment="None"),
        dict(name="Incline Dumbbell Press", description="Targets the upper chest with dumbbells on an inclined bench.", muscle_group="Chest", difficulty="Intermediate", duration_minutes=40, equipment="Dumbbells, Incline Bench"),
        dict(name="Pull-Up", description="Upper body compound exercise hanging from a bar.", muscle_group="Back", difficulty="Intermediate", duration_minutes=25, equipment="Pull-up Bar"),
        dict(name="Barbell Deadlift", description="Full-body compound lift focusing on the posterior chain.", muscle_group="Back", difficulty="Advanced", duration_minutes=50, equipment="Barbell"),
        dict(name="Seated Cable Row", description="Horizontal pulling movement targeting the mid-back.", muscle_group="Back", difficulty="Beginner", duration_minutes=30, equipment="Cable Machine"),
        dict(name="Barbell Squat", description="King of all leg exercises — full lower body compound lift.", muscle_group="Legs", difficulty="Advanced", duration_minutes=50, equipment="Barbell, Rack"),
        dict(name="Leg Press", description="Machine-based quad-dominant leg exercise.", muscle_group="Legs", difficulty="Beginner", duration_minutes=35, equipment="Leg Press Machine"),
        dict(name="Romanian Deadlift", description="Hip-hinge movement targeting the hamstrings and glutes.", muscle_group="Legs", difficulty="Intermediate", duration_minutes=40, equipment="Barbell"),
        dict(name="Overhead Press", description="Strict pressing movement for shoulder strength and size.", muscle_group="Shoulders", difficulty="Intermediate", duration_minutes=40, equipment="Barbell"),
        dict(name="Lateral Raise", description="Isolation movement for the lateral deltoid.", muscle_group="Shoulders", difficulty="Beginner", duration_minutes=20, equipment="Dumbbells"),
        dict(name="Dumbbell Curl", description="Classic bicep isolation exercise.", muscle_group="Arms", difficulty="Beginner", duration_minutes=20, equipment="Dumbbells"),
        dict(name="Tricep Rope Pushdown", description="Cable isolation exercise for the triceps.", muscle_group="Arms", difficulty="Beginner", duration_minutes=20, equipment="Cable Machine"),
        dict(name="Plank", description="Isometric core stability exercise.", muscle_group="Core", difficulty="Beginner", duration_minutes=15, equipment="None"),
        dict(name="Hanging Leg Raise", description="Advanced core exercise hanging from a bar.", muscle_group="Core", difficulty="Advanced", duration_minutes=20, equipment="Pull-up Bar"),
        dict(name="Running", description="Cardiovascular endurance training — steady state or intervals.", muscle_group="Cardio", difficulty="Beginner", duration_minutes=30, equipment="None"),
        dict(name="Jump Rope", description="High-intensity cardio using a jump rope.", muscle_group="Cardio", difficulty="Intermediate", duration_minutes=20, equipment="Jump Rope"),
        dict(name="Burpee", description="Full body explosive movement combining squat, push-up, and jump.", muscle_group="Full Body", difficulty="Advanced", duration_minutes=25, equipment="None"),
    ]

    with get_cli_session() as session:
        # Create bob admin
        existing = session.exec(select(User).where(User.username == "bob")).one_or_none()
        if not existing:
            bob = User(username="bob", email="bob@flexify.com", password=encrypt_password("bobpass"), role="admin")
            session.add(bob)
            session.commit()
            typer.echo("✅ Created admin user: bob / bobpass")
        else:
            typer.echo("ℹ️  User 'bob' already exists")

        # Seed workouts
        for w_data in WORKOUTS:
            exists = session.exec(select(Workout).where(Workout.name == w_data["name"])).one_or_none()
            if not exists:
                session.add(Workout(**w_data))
        session.commit()
        typer.echo(f"✅ Seeded {len(WORKOUTS)} workouts")

if __name__ == "__main__":
    app_cli()
