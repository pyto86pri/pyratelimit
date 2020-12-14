from subprocess import check_call


def test() -> None:
    check_call(["pytest", "-v", "tests"])


def cov() -> None:
    check_call(["coverage", "run", "--source", "pyratelimit", "-m", "pytest", "tests"])
    check_call(["coveralls"])


def lint() -> None:
    check_call(["flake8", "--config=setup.cfg", "pyratelimit", "tests"])


def format() -> None:
    check_call(["isort", "pyratelimit", "tests"])
    check_call(["black", "pyratelimit", "tests"])


def typecheck() -> None:
    check_call(["mypy", "--config-file=setup.cfg", "pyratelimit", "tests"])
