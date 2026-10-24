import argparse
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def run_app():
    app_path = str(Path(__file__).parent / "app.py")
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())


def verify(args):
    from dafs_teach.core.verification import verify_code, using_default_secret

    if using_default_secret():
        print(
            "Warning: DAFS_TEACH_SECRET is not set, using the built-in default "
            "secret. Since this repo is public, codes checked this way give no "
            "real protection against fabricated codes. Set DAFS_TEACH_SECRET to "
            "a private value known only to you and your students.",
            file=sys.stderr,
        )

    ok = verify_code(args.student_name, args.lesson_id, args.code)
    if ok:
        print(f"VALID — {args.student_name} completed '{args.lesson_id}'")
    else:
        print(f"INVALID — code does not match {args.student_name} / {args.lesson_id}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="dafs-teach")
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser(
        "verify", help="Check a student's module completion code"
    )
    verify_parser.add_argument("student_name", help="Student name, exactly as they entered it")
    verify_parser.add_argument("lesson_id", help="Lesson id, e.g. 03_packages_and_variables")
    verify_parser.add_argument("code", help="The code the student sent you")
    verify_parser.set_defaults(func=verify)

    # Only parse known args as a subcommand; bare `dafs-teach` launches the app.
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        args = parser.parse_args()
        args.func(args)
    else:
        run_app()


if __name__ == "__main__":
    main()
