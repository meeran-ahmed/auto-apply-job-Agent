import sys
import click
from loguru import logger
from src.agents.orchestrator import SwarmOrchestrator


@click.command()
@click.option('--mode', default='swarm', type=click.Choice(['swarm', 'linkedin', 'excel', 'outreach', 'all']), help='Execution mode: swarm, linkedin, excel, outreach, or all')
@click.option('--file', default=None, type=str, help='Path to custom Excel (.xlsx, .xls) or CSV spreadsheet with job links')
@click.option('--limit', default=50, type=int, help='Maximum applications or recruiter contacts to process in this run')
def main(mode: str, file: str, limit: int):
    """
    Auto Job: Autonomous Multi-Agent Job Application & Referral Outreach Engine.
    Coordinates specialized worker agents across job portals, custom Excel sheets,
    ATS boards, recruiter discovery, and referral synthesis.
    """
    logger.info("Initializing Auto Job Multi-Agent Engine...")
    orchestrator = SwarmOrchestrator()

    if mode == 'outreach':
        report_file = orchestrator.generate_outreach(max_companies=limit)
        print("\n" + "=" * 70)
        print(f"[SUCCESS] RECRUITER SCOUT & REFERRAL OUTREACH COMPLETE!")
        print(f"Full Referral Matrix Report: {report_file}")
        print("=" * 70 + "\n")
        return

    if mode == 'excel':
        report_file = orchestrator.run_excel_batch(file_path=file, max_jobs=limit)
        print("\n" + "=" * 70)
        print(f"[SUCCESS] SPREADSHEET BATCH APPLICATIONS COMPLETE!")
        print(f"Full Executive Report: {report_file}")
        print("=" * 70 + "\n")
        return

    if mode in ['swarm', 'all']:
        report_file = orchestrator.run_swarm(max_external_jobs=limit)
        print("\n" + "=" * 70)
        print(f"[SUCCESS] AUTO JOB APPLICATIONS COMPLETE!")
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
