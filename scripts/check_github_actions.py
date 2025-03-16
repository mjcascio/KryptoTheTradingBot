#!/usr/bin/env python3
"""
GitHub Actions Status Checker

This script checks the status of GitHub Actions workflows and reports on their health.
It requires a GitHub Personal Access Token with appropriate permissions.
"""

import os
import sys
import argparse
import requests
import datetime
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/github_actions.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class GitHubActionsChecker:
    """Checks the status of GitHub Actions workflows."""
    
    def __init__(self, token: str, owner: str, repo: str):
        """
        Initialize the GitHub Actions checker.
        
        Args:
            token: GitHub Personal Access Token
            owner: Repository owner (username or organization)
            repo: Repository name
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Get all workflows in the repository.
        
        Returns:
            List of workflow dictionaries
        """
        url = f"{self.base_url}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["workflows"]
    
    def get_workflow_runs(self, workflow_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent runs for a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            limit: Maximum number of runs to retrieve
            
        Returns:
            List of workflow run dictionaries
        """
        url = f"{self.base_url}/actions/workflows/{workflow_id}/runs?per_page={limit}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["workflow_runs"]
    
    def check_workflow_health(self, workflow_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Check the health of a workflow over the specified time period.
        
        Args:
            workflow_id: ID of the workflow
            days: Number of days to check
            
        Returns:
            Dictionary with health metrics
        """
        runs = self.get_workflow_runs(workflow_id, limit=100)
        
        # Filter runs within the specified time period
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        recent_runs = [
            run for run in runs 
            if (datetime.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) 
                > cutoff_date)
        ]
        
        if not recent_runs:
            return {
                "total_runs": 0,
                "success_rate": 0,
                "failure_rate": 0,
                "last_run_status": "unknown",
                "last_run_date": None,
                "average_duration": 0
            }
        
        # Calculate metrics
        total_runs = len(recent_runs)
        successful_runs = sum(1 for run in recent_runs if run["conclusion"] == "success")
        failed_runs = sum(1 for run in recent_runs if run["conclusion"] == "failure")
        
        # Calculate durations for completed runs
        durations = []
        for run in recent_runs:
            if run["status"] == "completed" and run["updated_at"] and run["created_at"]:
                start = datetime.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                end = datetime.datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (end - start).total_seconds()
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_runs": total_runs,
            "success_rate": (successful_runs / total_runs) * 100 if total_runs > 0 else 0,
            "failure_rate": (failed_runs / total_runs) * 100 if total_runs > 0 else 0,
            "last_run_status": recent_runs[0]["conclusion"],
            "last_run_date": recent_runs[0]["created_at"],
            "average_duration": avg_duration
        }
    
    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a comprehensive report on all workflows.
        
        Args:
            days: Number of days to include in the report
            
        Returns:
            Dictionary with report data
        """
        workflows = self.get_workflows()
        report = {
            "repository": f"{self.owner}/{self.repo}",
            "report_date": datetime.datetime.now().isoformat(),
            "period_days": days,
            "workflows": {}
        }
        
        for workflow in workflows:
            workflow_id = workflow["id"]
            workflow_name = workflow["name"]
            
            try:
                health = self.check_workflow_health(workflow_id, days)
                report["workflows"][workflow_name] = {
                    "id": workflow_id,
                    "state": workflow["state"],
                    "path": workflow["path"],
                    "health": health
                }
            except Exception as e:
                logger.error(f"Error checking workflow {workflow_name}: {str(e)}")
                report["workflows"][workflow_name] = {
                    "id": workflow_id,
                    "state": workflow["state"],
                    "path": workflow["path"],
                    "health": {"error": str(e)}
                }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save the report to a file.
        
        Args:
            report: Report data
            output_file: Path to output file (optional)
            
        Returns:
            Path to the saved report file
        """
        if not output_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/github_actions_report_{timestamp}.txt"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write(f"GitHub Actions Report for {report['repository']}\n")
            f.write(f"Generated: {report['report_date']}\n")
            f.write(f"Period: Last {report['period_days']} days\n\n")
            
            for name, workflow in report["workflows"].items():
                f.write(f"Workflow: {name}\n")
                f.write(f"  Path: {workflow['path']}\n")
                f.write(f"  State: {workflow['state']}\n")
                
                if "error" in workflow["health"]:
                    f.write(f"  Error: {workflow['health']['error']}\n")
                else:
                    health = workflow["health"]
                    f.write(f"  Total Runs: {health['total_runs']}\n")
                    f.write(f"  Success Rate: {health['success_rate']:.2f}%\n")
                    f.write(f"  Failure Rate: {health['failure_rate']:.2f}%\n")
                    f.write(f"  Last Run: {health['last_run_status']} "
                            f"on {health['last_run_date']}\n")
                    f.write(f"  Average Duration: {health['average_duration']:.2f} seconds\n")
                
                f.write("\n")
        
        logger.info(f"Report saved to {output_file}")
        return output_file


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check GitHub Actions workflow status")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--owner", help="Repository owner (username or organization)")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--days", type=int, default=7, help="Number of days to include in report")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Get token from environment if not provided
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not provided. Use --token or set GITHUB_TOKEN "
                     "environment variable.")
        sys.exit(1)
    
    # Get owner and repo from environment if not provided
    owner = args.owner or os.environ.get("GITHUB_OWNER")
    repo = args.repo or os.environ.get("GITHUB_REPO")
    
    if not owner or not repo:
        logger.error("Repository owner and name are required.")
        sys.exit(1)
    
    try:
        checker = GitHubActionsChecker(token, owner, repo)
        report = checker.generate_report(days=args.days)
        output_file = checker.save_report(report, args.output)
        
        print(f"Report generated successfully: {output_file}")
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 