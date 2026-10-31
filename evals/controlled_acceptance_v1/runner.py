"""Exactly one authored 12-case final run; no tunable variants or selective cases."""

from evals.inference_lab_v1.runner import run


def main():
    return run(track="acceptance", trial="final-001")


if __name__ == "__main__":
    main()
