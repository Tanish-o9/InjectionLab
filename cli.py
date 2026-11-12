"""InjectionLab Unified CLI."""
import argparse
import os
import subprocess
import sys

import config
from defenses.detector import InjectionDetector
from evaluation.report_generator import generate_html_report


def cmd_scan(args):
    """Scan a text query for prompt injection cues."""
    detector = InjectionDetector().fit()
    score = detector.score(args.text)
    is_inj = score >= config.DETECTOR_THRESHOLD
    print(f"\nScanning query: \"{args.text}\"")
    print(f"Injection Score: {score:.4f} (Threshold: {config.DETECTOR_THRESHOLD})")
    if is_inj:
        print("[!] VERDICT: DETECTED PROMPT INJECTION (FLAGGED)")
        sys.exit(1)
    else:
        print("[+] VERDICT: CLEAN / SAFE")
        sys.exit(0)


def cmd_benchmark(args):
    """Run benchmark experiments."""
    cmd = [sys.executable, "run_experiment.py", "--model", args.model, "--trials", str(args.trials)]
    if args.max_attacks > 0:
        cmd.extend(["--max-attacks", str(args.max_attacks)])
    subprocess.run(cmd, check=True)


def cmd_plot(args):
    """Generate benchmark visual plots."""
    subprocess.run([sys.executable, "plot_results.py", args.tag], check=True)


def cmd_report(args):
    """Generate self-contained interactive HTML report."""
    out = generate_html_report(args.tag)
    print(f"[+] Interactive HTML report generated at: {out}")


def cmd_demo(args):
    """Launch the interactive Streamlit security playground."""
    print("[*] Launching InjectionLab Playground on http://localhost:8501 ...")
    subprocess.run(["streamlit", "run", "demo.py"], check=True)


def cmd_test(args):
    """Run full test suite."""
    subprocess.run([sys.executable, "-m", "pytest", "-v", "tests"], check=True)


def main():
    parser = argparse.ArgumentParser(
        prog="injectionlab",
        description="InjectionLab: Automated LLM Red-Teaming & Prompt-Injection Defense Benchmark"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan a text string for prompt injection indicators")
    p_scan.add_argument("text", help="Prompt or text to analyze")
    p_scan.set_defaults(func=cmd_scan)

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Run benchmark against target LLM")
    p_bench.add_argument("--model", default="mock:weak", help="Model spec (mock:weak, ollama:..., openai:...)")
    p_bench.add_argument("--trials", type=int, default=3, help="Number of evaluation trials per attack")
    p_bench.add_argument("--max-attacks", type=int, default=0, help="Subset of attacks to evaluate (0 = all)")
    p_bench.set_defaults(func=cmd_benchmark)

    # plot
    p_plot = subparsers.add_parser("plot", help="Generate ASR vs Utility charts")
    p_plot.add_argument("tag", default="mock_weak", nargs="?", help="Results directory tag (e.g. mock_weak)")
    p_plot.set_defaults(func=cmd_plot)

    # report
    p_rep = subparsers.add_parser("report", help="Generate standalone interactive HTML report")
    p_rep.add_argument("tag", default="mock_weak", nargs="?", help="Results directory tag")
    p_rep.set_defaults(func=cmd_report)

    # demo
    p_demo = subparsers.add_parser("demo", help="Launch interactive Streamlit playground UI")
    p_demo.set_defaults(func=cmd_demo)

    # test
    p_test = subparsers.add_parser("test", help="Run pytest test suite")
    p_test.set_defaults(func=cmd_test)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
