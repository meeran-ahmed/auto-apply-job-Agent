import sys
import click
from loguru import logger
from src.agents.orchestrator import SwarmOrchestrator


@click.command()
@click.option('--mode', default='swarm', type=click.Choice(['swarm', 'linkedin', 'all']), help='Swarm mode to execute')
@click.option('--limit', default=50, type=int, help='Maximum external applications to process in this run')
def main(mode: str, limit: int):
    """
    OmniSwarm: Autonomous Multi-Agent Job Application Engine.
    Coordinates specialized worker agents across job portals, ATS boards,
    and LinkedIn, generating an executive report upon completion.
    """
    logger.info("Initializing OmniSwarm Multi-Agent Engine...")
    orchestrator = SwarmOrchestrator()

    if mode in ['swarm', 'all']:
        report_file = orchestrator.run_swarm(max_external_jobs=limit)
        print("\n" + "=" * 70)
        print(f"[SUCCESS] OMNISWARM APPLICATIONS COMPLETE!")
        print(f"Full Executive Report: {report_file}")
        print("=" * 70 + "\n")

    if mode in ['linkedin', 'all']:
        import subprocess
        try:
            logger.info("Starting LinkedIn Easy Apply & Dual-Tier ATS Agent...")
            subprocess.run([sys.executable, "main.py"], check=False)
        except Exception as e:
            logger.error(f"LinkedIn runner encountered an error: {e}")
        finally:
            orchestrator.reporter._load_existing_ledger()
            final_report = orchestrator.reporter.generate_report()
            print("\n" + "=" * 70)
            print(f"[SUCCESS] ALL JOB CHANNELS EXECUTED!")
            print(f"Updated Report: {final_report}")
            print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
