#!/usr/bin/env python3

"""
CLI para el sistema epidemiológico - Gestión segura de seeds y ETL.

Este CLI permite ejecutar tareas de mantenimiento, seeds y ETL sin exponer
estos servicios via API web.
"""

import asyncio
import sys
from pathlib import Path

import click

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_async_session


@click.group()
@click.version_option(version="1.0.0", prog_name="epidemiologia-cli")
def cli():
    """CLI para el sistema epidemiológico de Chubut."""
    click.echo("🏥 Sistema Epidemiológico - CLI de Gestión")
    click.echo("   Backend de gestión epidemiológica para Chubut")


@cli.group()
def seeds():
    """Gestión de seeds (datos maestros del sistema)."""
    pass


@seeds.command("run")
@click.option(
    "--confirm", is_flag=True, help="Confirmar ejecución sin prompt interactivo."
)
def seeds_run(confirm: bool):
    """Ejecutar todos los seeds del sistema."""
    if not confirm:
        click.confirm(
            "⚠️  ¿Estás seguro de ejecutar todos los seeds? "
            "Esto puede modificar datos en la base de datos.",
            abort=True,
        )

    click.echo("🌱 Ejecutando seeds del sistema epidemiológico...")

    async def run_seeds_async():
        try:
            from scripts.seeds.run_seeds import run_all_seeds

            await run_all_seeds()
            click.echo("✅ Seeds ejecutados correctamente!")
        except Exception as e:
            click.echo(f"❌ Error ejecutando seeds: {str(e)}", err=True)
            raise click.ClickException(str(e))

    asyncio.run(run_seeds_async())


@seeds.command("geografia")
@click.option(
    "--confirm", is_flag=True, help="Confirmar ejecución sin prompt interactivo."
)
def seeds_geografia(confirm: bool):
    """Ejecutar solo el seed de geografía (localidades, provincias, departamentos)."""
    if not confirm:
        click.confirm("⚠️  ¿Estás seguro de ejecutar el seed de geografía?", abort=True)

    click.echo("🌍 Ejecutando seed de geografía...")

    async def run_geografia_seed():
        try:
            async for session in get_async_session():
                try:
                    from scripts.seeds.seed_geografia import seed_geografia

                    await seed_geografia(session)
                    click.echo("✅ Seed de geografía ejecutado correctamente!")
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except Exception as e:
            click.echo(f"❌ Error ejecutando seed de geografía: {str(e)}", err=True)
            raise click.ClickException(str(e))

    asyncio.run(run_geografia_seed())


@seeds.command("eventos")
@click.option(
    "--confirm", is_flag=True, help="Confirmar ejecución sin prompt interactivo."
)
def seeds_eventos(confirm: bool):
    """Ejecutar solo el seed de eventos epidemiológicos."""
    if not confirm:
        click.confirm("⚠️  ¿Estás seguro de ejecutar el seed de eventos?", abort=True)

    click.echo("🦠 Ejecutando seed de eventos...")

    async def run_eventos_seed():
        try:
            async for session in get_async_session():
                try:
                    from scripts.seeds.seed_eventos import seed_eventos

                    await seed_eventos(session)
                    click.echo("✅ Seed de eventos ejecutado correctamente!")
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except Exception as e:
            click.echo(f"❌ Error ejecutando seed de eventos: {str(e)}", err=True)
            raise click.ClickException(str(e))

    asyncio.run(run_eventos_seed())


@seeds.command("establecimientos")
@click.option(
    "--confirm", is_flag=True, help="Confirmar ejecución sin prompt interactivo."
)
def seeds_establecimientos(confirm: bool):
    """Ejecutar solo el seed de establecimientos de salud."""
    if not confirm:
        click.confirm(
            "⚠️  ¿Estás seguro de ejecutar el seed de establecimientos?", abort=True
        )

    click.echo("🏥 Ejecutando seed de establecimientos...")

    async def run_establecimientos_seed():
        try:
            async for session in get_async_session():
                try:
                    from scripts.seeds.seed_establecimientos import (
                        seed_establecimientos,
                    )

                    await seed_establecimientos(session)
                    click.echo("✅ Seed de establecimientos ejecutado correctamente!")
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        except Exception as e:
            click.echo(
                f"❌ Error ejecutando seed de establecimientos: {str(e)}", err=True
            )
            raise click.ClickException(str(e))

    asyncio.run(run_establecimientos_seed())


if __name__ == "__main__":
    cli()
