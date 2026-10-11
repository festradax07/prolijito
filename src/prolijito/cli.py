"""Punto de entrada de la línea de comandos.

Solo interpreta argumentos, arma las dependencias y traduce resultados a exit codes.
La lógica vive en `application/`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from enum import IntEnum
from pathlib import Path

from prolijito import __version__
from prolijito.adapters.yaml_profiles import (
    YamlProfileRepository,
    builtin_profiles_dir,
    profile_template,
)
from prolijito.application.errors import ProlijitoError
from prolijito.domain.profile import PROFILE_ID_PATTERN

PROG = "prolijito"
REPORT_FORMATS = ("md", "json", "github")
CUSTOM_PROFILE_HINT = """\
Perfil propio:
  prolijito profiles --template mi-perfil > mi-perfil.yaml
  prolijito check informe.pdf --profile mi-perfil.yaml"""


class ExitCode(IntEnum):
    """Contrato de salida de la CLI."""

    OK = 0
    VIOLATIONS = 1
    EXECUTION_ERROR = 2


Handler = Callable[[argparse.Namespace], ExitCode]


def main(argv: Sequence[str] | None = None) -> ExitCode:
    """Ejecuta la CLI con `argv` (o `sys.argv[1:]`) y devuelve el exit code."""
    args = _build_parser().parse_args(argv)
    handler: Handler = args.handler
    try:
        return handler(args)
    except ProlijitoError as error:
        return _fail(str(error))


def run() -> None:
    """Entrypoint del script `prolijito`."""
    sys.exit(main())


# ---------- comandos ----------


def _check(args: argparse.Namespace) -> ExitCode:
    document: Path = args.file
    if not document.is_file():
        return _fail(f"no existe el archivo '{document}'.")
    return _fail("'check' todavía no está implementado.")


def _profiles(args: argparse.Namespace) -> ExitCode:
    if args.template is not None:
        return _print_template(args.template)
    repository = _profile_repository(args.profiles_dir)
    summaries = repository.available()
    builtin = builtin_profiles_dir().resolve()
    width = max((len(s.id) for s in summaries), default=0)
    lines = ["Perfiles disponibles:"]
    for s in summaries:
        origin = "" if s.path.parent.resolve() == builtin else f"  [{s.path}]"
        lines.append(f"  {s.id.ljust(width)}  {s.version.ljust(7)}  {s.description}{origin}")
    sys.stdout.write("\n".join([*lines, "", CUSTOM_PROFILE_HINT, ""]))
    return ExitCode.OK


def _print_template(profile_id: str) -> ExitCode:
    if not PROFILE_ID_PATTERN.match(profile_id):
        return _fail(f"'{profile_id}' no sirve como id: usar kebab-case (ej. mi-catedra).")
    sys.stdout.write(profile_template(profile_id))
    return ExitCode.OK


def _profile_repository(profiles_dir: Path | None) -> YamlProfileRepository:
    if profiles_dir is not None and not profiles_dir.is_dir():
        raise ProlijitoError(f"no existe la carpeta de perfiles '{profiles_dir}'.")
    extra = [profiles_dir] if profiles_dir is not None else []
    return YamlProfileRepository([*extra, builtin_profiles_dir()])


def _not_implemented(command: str) -> Handler:
    def handler(_: argparse.Namespace) -> ExitCode:
        return _fail(f"'{command}' todavía no está implementado.")

    return handler


def _fail(message: str) -> ExitCode:
    sys.stderr.write(f"{PROG}: error: {message}\n")
    return ExitCode.EXECUTION_ERROR


# ---------- parser ----------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Valida el formato de informes contra una norma, sin tocar el contenido.",
        epilog=CUSTOM_PROFILE_HINT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    _add_help(parser)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión y termina.",
    )
    commands = parser.add_subparsers(title="comandos", metavar="<comando>", required=True)

    check = _add_command(commands, "check", "Valida un documento y genera el reporte.", _check)
    _add_document_args(check)
    check.add_argument(
        "--format",
        choices=REPORT_FORMATS,
        default="md",
        help="Formato del reporte (por defecto: md).",
    )
    check.add_argument("--output", type=Path, help="Archivo donde escribir el reporte.")

    fix = _add_command(commands, "fix", "Corrige el formato (Fase 3).", _not_implemented("fix"))
    _add_document_args(fix)
    fix.add_argument("--max-iter", type=int, default=3, help="Máximo de vueltas del loop.")

    review = _add_command(
        commands, "review", "Sugiere mejoras de redacción (Fase 4).", _not_implemented("review")
    )
    _add_document_args(review)
    review.add_argument("--llm", help="Proveedor de LLM.")

    new = _add_command(
        commands,
        "new",
        "Crea un documento desde la plantilla de un perfil (Fase 3).",
        _not_implemented("new"),
    )
    new.add_argument("profile", help="ID del perfil.")
    new.add_argument("destination", type=Path, help="Archivo a crear.")

    profiles = _add_command(commands, "profiles", "Lista los perfiles disponibles.", _profiles)
    _add_profiles_dir(profiles)
    profiles.add_argument(
        "--template",
        nargs="?",
        const="mi-perfil",
        metavar="ID",
        help="Imprime una plantilla comentada para crear un perfil propio con ese id.",
    )
    return parser


def _add_command(
    commands: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    summary: str,
    handler: Handler,
) -> argparse.ArgumentParser:
    command = commands.add_parser(
        name,
        help=summary,
        description=summary,
        epilog=CUSTOM_PROFILE_HINT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    _add_help(command)
    command.set_defaults(handler=handler)
    return command


def _add_document_args(command: argparse.ArgumentParser) -> None:
    command.add_argument("file", type=Path, help="Documento a procesar.")
    command.add_argument(
        "--profile",
        required=True,
        help="ID de un perfil (ver `prolijito profiles`) o ruta a un .yaml.",
    )
    _add_profiles_dir(command)


def _add_profiles_dir(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--profiles-dir",
        type=Path,
        help="Carpeta adicional con perfiles propios; tiene prioridad sobre los incluidos.",
    )


def _add_help(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-h", "--help", action="help", help="Muestra esta ayuda y termina.")
