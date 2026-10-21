import sys
import click
from loguru import logger
from src.agents.orchestrator import SwarmOrchestrator


@click.command()
@click.option('--mode', default='universal', type=click.Choice(['universal', 'swarm', 'linkedin', 'excel', 'outreach', 'all']), help='Execution mode: universal (live Chrome multi-portal), swarm, linkedin, excel, outreach, or all')
@click.option('--portal', default='all', type=str, help='Target portal in universal mode: all, freehire, linkedin, naukri, indeed, cutshort, internshala, wellfound')
@click.option('--file', default=None, type=str, help='Path to custom Excel (.xlsx, .xls) or CSV spreadsheet with job links')
@click.option('--limit', default=10, type=int, help='Maximum applications or recruiter contacts to process in this run')
@click.option('--port', default=9222, type=int, help='Chrome remote debugging port (default: 9222)')
def main(mode: str, portal: str, file: str, limit: int, port: int):
    """
    Auto Job: Autonomous Multi-Agent Job Application & Referral Outreach Engine.
    Coordinates specialized worker agents across job portals, custom Excel sheets,
    ATS boards, recruiter discovery, and referral synthesis.
    """
    logger.info("Initializing Auto Job Multi-Agent Engine...")

    if mode == 'universal':
        from src.core.universal_swarm import UniversalSwarm
        swarm = UniversalSwarm(port=port)
        if portal == 'all':
            report_file = swarm.run_swarm(limit_per_portal=limit)
        else:
            swarm.run_portal(portal_name=portal, limit=limit)
            report_file = swarm.reporter.generate_report()

        print("\n" + "=" * 70)
        print(f"[SUCCESS] UNIVERSAL CHROME JOB SWARM COMPLETE!")
        print(f"Full Executive Report: {report_file}")
        print("=" * 70 + "\n")
        return

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
