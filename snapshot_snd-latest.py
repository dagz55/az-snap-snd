import asyncio
import json
import logging
import sys  # Added sys module
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.prompt import Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.console import Group
import getpass
import time
import csv
from collections import defaultdict

console = Console()

# Create overall progress bar
overall_progress = Progress(
    SpinnerColumn(),
    "[progress.description]{task.description}",
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.0f}%",
    "•",
    TextColumn("[bold blue]{task.fields[subscription]}"),
    TimeRemainingColumn(),
    console=console,
    transient=True,  # Progress bar disappears when done
)
overall_task = overall_progress.add_task(
    description="[cyan]Initializing...", total=100, subscription=""
)

COLOR_SCALE = ["green", "yellow", "red"]

# Configure logging
current_date = datetime.now().strftime("%Y%m%d")
current_user = getpass.getuser()
log_file = f"azure_snapshot_manager_{current_date}_{current_user}.log"
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to file: {log_file}")

async def run_az_command(command):
    logger.info(f"Running Azure command: {command}")
    try:
        if isinstance(command, list):
            if 'az' in command and 'login' in command:
                # For az login, allow interaction with the terminal
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=None,
                    stdout=None,
                    stderr=None,
                )
                await process.communicate()
                if process.returncode == 0:
                    logger.info("az login executed successfully")
                    return "Logged in", None
                else:
                    error_message = "Login failed"
                    logger.error(f"Error running command: {command}")
                    logger.error(f"Error message: {error_message}")
                    return None, error_message
            else:
                # For other commands, capture stdout and stderr
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
        else:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        stdout, stderr = await process.communicate()
        stdout = stdout.decode().strip()
        stderr = stderr.decode().strip()
        if process.returncode == 0:
            logger.info("Command executed successfully")
            return stdout, None
        else:
            error_message = stderr
            logger.error(f"Error running command: {command}")
            logger.error(f"Error message: {error_message}")
            return None, error_message
    except Exception as e:
        logger.exception(f"An error occurred while running command: {command}")
        return None, str(e)

async def check_az_login():
    logger.info("Checking Azure login status")
    result, error = await run_az_command(["az", "account", "show"])
    if result:
        logger.info("User is already logged in")
        return True
    else:
        console.print("[yellow]You are not logged in to Azure. Please log in.[/yellow]")
        logger.info("User not logged in, attempting to run 'az login'")
        result, error = await run_az_command(["az", "login"])
        if result:
            logger.info("Login successful")
            return True
        else:
            logger.error(f"Login failed. Error: {error}")
            console.print("[red]Failed to log in to Azure. Exiting.[/red]")
            return False

async def get_subscriptions():
    logger.info("Fetching Azure subscriptions")
    result, error = await run_az_command(
        ["az", "account", "list", "--query", "[].{name:name, id:id}", "-o", "json"]
    )
    if result:
        subscriptions = json.loads(result)
        logger.info(f"Found {len(subscriptions)} subscriptions")
        return subscriptions
    logger.warning(f"No subscriptions found. Error: {error}")
    return []

async def get_snapshots(subscription_id, start_date, end_date, keyword=None):
    logger.info(
        f"Fetching snapshots for subscription {subscription_id} between {start_date} and {end_date}"
    )
    query = (
        f"[?timeCreated >= '{start_date}' && timeCreated <= '{end_date}']"
        f".{{name:name, resourceGroup:resourceGroup, timeCreated:timeCreated, "
        f"diskState:diskState, id:id, tags:tags}}"
    )
    command = [
        'az', 'snapshot', 'list',
        '--subscription', subscription_id,
        '--query', query,
        '-o', 'json'
    ]
    result, error = await run_az_command(command)
    if result:
        snapshots = json.loads(result)
        if keyword:
            snapshots = [s for s in snapshots if keyword.lower() in s["name"].lower()]
        logger.info(f"Found {len(snapshots)} snapshots in subscription {subscription_id}")
        return snapshots
    logger.warning(f"No snapshots found in subscription {subscription_id}. Error: {error}")
    return []

def get_age_color(created_date):
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(created_date)).days
    if age < 30:
        return COLOR_SCALE[0]
    elif age < 90:
        return COLOR_SCALE[1]
    else:
        return COLOR_SCALE[2]

def create_snapshot_table(snapshots, subscription_name):
    table = Table(title=f"Snapshots in {subscription_name}")
    table.add_column("Name", style="cyan")
    table.add_column("Resource Group", style="magenta")
    table.add_column("Time Created", style="green")
    table.add_column("Age (days)", style="yellow")
    table.add_column("Created By", style="blue")
    table.add_column("Status", style="red")

    for snapshot in snapshots:
        created_date = datetime.fromisoformat(snapshot["timeCreated"])
        age = (datetime.now(timezone.utc) - created_date).days
        age_color = get_age_color(snapshot["timeCreated"])
        tags = snapshot.get("tags", {})
        created_by = tags.get("CreatedByUserId", "N/A")
        status = snapshot.get("diskState", "N/A")

        table.add_row(
            snapshot["name"],
            snapshot["resourceGroup"],
            snapshot["timeCreated"],
            f"[{age_color}]{age}[/{age_color}]",
            created_by,
            status,
        )

    return table

def display_snapshots(snapshots, subscription_name):
    if not snapshots:
        console.print(
            f"[yellow]No snapshots found in subscription: {subscription_name}[/yellow]"
        )
    else:
        table = create_snapshot_table(snapshots, subscription_name)
        console.print(table)

def get_default_date_range():
    today = datetime.now(timezone.utc)
    start_of_month = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end_of_month = (
        start_of_month + timedelta(days=32)
    ).replace(day=1) - timedelta(seconds=1)
    return start_of_month.isoformat(), end_of_month.isoformat()

def is_non_prod(subscription_name):
    return "nonprod" in subscription_name.lower()

def is_prod(subscription_name):
    return "prod" in subscription_name.lower()

async def switch_subscription(subscription_id, current_subscription_id):
    if subscription_id != current_subscription_id:
        result, error = await run_az_command(
            ["az", "account", "set", "--subscription", subscription_id]
        )
        if result is not None:
            logger.info(f"Switched to subscription: {subscription_id}")
            return subscription_id
        else:
            logger.error(f"Failed to switch to subscription: {subscription_id}. Error: {error}")
            return None
    else:
        return current_subscription_id

async def delete_snapshots(snapshot_list):
    results = {"deleted": [], "failed": []}
    current_subscription = None

    total_snapshots = len(snapshot_list)

    # Organize snapshots by subscription for efficient processing
    snapshots_by_subscription = defaultdict(list)
    for snapshot in snapshot_list:
        snapshots_by_subscription[snapshot["subscription_id"]].append(snapshot)

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        delete_task = progress.add_task(
            "[cyan]Deleting snapshots...", total=total_snapshots
        )

        # Process each subscription separately
        for subscription_id, snapshots in snapshots_by_subscription.items():
            subscription_name = snapshots[0]["subscription_name"]

            # Switch to the correct subscription
            current_subscription = await switch_subscription(
                subscription_id, current_subscription
            )
            if current_subscription != subscription_id:
                for snapshot in snapshots:
                    snapshot_name = snapshot["name"]
                    results["failed"].append(snapshot_name)
                    progress.console.print(
                        f"[red]Failed to switch to subscription {subscription_name}. Skipping snapshot {snapshot_name}[/red]"
                    )
                    progress.update(delete_task, advance=1)
                continue

            # Collect snapshot IDs and handle locks
            snapshot_ids = [snapshot["id"] for snapshot in snapshots]
            resource_groups = set(snapshot["resourceGroup"] for snapshot in snapshots)

            removed_locks = []
            # Remove locks from all involved resource groups
            for resource_group in resource_groups:
                lock_query = "[?level=='CanNotDelete'].{name:name, id:id}"
                lock_list_result, error = await run_az_command(
                    ['az', 'lock', 'list', '--resource-group', resource_group,
                     '--query', lock_query, '-o', 'json']
                )
                locks = json.loads(lock_list_result) if lock_list_result else []
                for lock in locks:
                    # Remove the lock
                    remove_lock_result, error = await run_az_command(
                        ['az', 'lock', 'delete', '--ids', lock['id']]
                    )
                    if remove_lock_result is not None:
                        removed_locks.append((resource_group, lock))
                        progress.console.print(
                            f"[yellow]Removed lock '{lock['name']}' on resource group '{resource_group}'[/yellow]"
                        )
                    else:
                        logger.error(
                            f"Failed to remove lock {lock['name']} on resource group {resource_group}. Error: {error}"
                        )
                        progress.console.print(
                            f"[red]Failed to remove lock '{lock['name']}' on resource group '{resource_group}'. Skipping associated snapshots.[/red]"
                        )
                        # Mark snapshots in this resource group as failed
                        for snapshot in snapshots:
                            if snapshot["resourceGroup"] == resource_group:
                                snapshot_name = snapshot["name"]
                                results["failed"].append(snapshot_name)
                                progress.update(delete_task, advance=1)
                        # Remove snapshots from deletion list
                        snapshots = [s for s in snapshots if s["resourceGroup"] != resource_group]
                        snapshot_ids = [s["id"] for s in snapshots]
                        if not snapshots:
                            break

            if not snapshots:
                continue

            # Delete snapshots asynchronously
            delete_coroutines = []
            for snapshot in snapshots:
                snapshot_id = snapshot["id"]
                snapshot_name = snapshot["name"]
                delete_coroutines.append(delete_snapshot(snapshot_id, snapshot_name, progress))

            deletion_results = await asyncio.gather(*delete_coroutines)

            for snapshot_name, success in deletion_results:
                if success:
                    results["deleted"].append(snapshot_name)
                else:
                    results["failed"].append(snapshot_name)
                progress.update(delete_task, advance=1)

            # Restore locks
            for resource_group, lock in removed_locks:
                create_lock_result, error = await run_az_command(
                    ['az', 'lock', 'create', '--name', lock['name'], '--resource-group', resource_group, '--lock-type', 'CanNotDelete']
                )
                if create_lock_result is not None:
                    progress.console.print(
                        f"[yellow]Restored lock '{lock['name']}' on resource group '{resource_group}'[/yellow]"
                    )
                else:
                    logger.error(
                        f"Failed to restore lock '{lock['name']}' on resource group {resource_group}. Error: {error}"
                    )
                    progress.console.print(
                        f"[red]Failed to restore lock '{lock['name']}' on resource group '{resource_group}'[/red]"
                    )

    return results

async def delete_snapshot(snapshot_id, snapshot_name, progress):
    # Proceed to delete snapshot
    progress.console.print(
        f"[cyan]Deleting snapshot '{snapshot_name}'[/cyan]"
    )
    delete_result, error = await run_az_command(
        ['az', 'snapshot', 'delete', '--ids', snapshot_id]
    )
    if delete_result is not None:
        logger.info(f"Deleted snapshot '{snapshot_name}'")
        progress.console.print(
            f"[green]Deleted snapshot '{snapshot_name}'[/green]"
        )
        return snapshot_name, True
    else:
        logger.error(f"Failed to delete snapshot '{snapshot_name}'. Error: {error}")
        progress.console.print(
            f"[red]Failed to delete snapshot '{snapshot_name}'[/red]"
        )
        return snapshot_name, False

async def main():
    logger.info("Starting Azure Snapshot Manager")
    console.print("[bold cyan]Welcome to the Azure Snapshot Search & Destroy![/bold cyan]")

    # Check Azure login status
    is_logged_in = await check_az_login()
    if not is_logged_in:
        return

    # Get date range from user or use default
    default_start, default_end = get_default_date_range()
    start_date = Prompt.ask(
        "Enter start date (YYYY-MM-DD)", default=default_start[:10]
    )
    end_date = Prompt.ask(
        "Enter end date (YYYY-MM-DD)", default=default_end[:10]
    )

    # Validate and format dates
    try:
        start_datetime = datetime.strptime(
            start_date, "%Y-%m-%d"
        ).replace(tzinfo=timezone.utc)
        end_datetime = datetime.strptime(
            end_date, "%Y-%m-%d"
        ).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        start_date = start_datetime.isoformat()
        end_date = end_datetime.isoformat()
        logger.info(f"Date range set: {start_date} to {end_date}")
    except ValueError:
        logger.warning(
            "Invalid date format. Using default date range for the current month."
        )
        console.print(
            "[bold red]Invalid date format. Using default date range for the current month.[/bold red]"
        )
        start_date, end_date = default_start, default_end

    # Ask for keyword filter
    keyword = Prompt.ask("Enter a keyword to filter snapshots (optional)", default="")

    subscriptions = await get_subscriptions()
    if not subscriptions:
        logger.error("No subscriptions found. User may not be logged in.")
        console.print(
            "[bold red]No subscriptions found. Please make sure you're logged in with 'az login'.[/bold red]"
        )
        return

    all_snapshots = []
    start_time = time.time()

    # Create a growing table
    growing_table = Table(
        title="[bold cyan]Snapshot Search Results[/bold cyan]", border_style="blue"
    )
    growing_table.add_column("Subscription", style="cyan", header_style="bold cyan")
    growing_table.add_column(
        "Snapshots Found", style="magenta", header_style="bold magenta"
    )
    growing_table.add_column("Status", style="green", header_style="bold green")

    with Live(Panel(Group(overall_progress, growing_table)), refresh_per_second=4) as live:
        for i, subscription in enumerate(subscriptions):
            logger.info(f"Searching in subscription: {subscription['name']}")
            overall_progress.update(
                overall_task,
                completed=(i + 1) / len(subscriptions) * 100,
                description="Searching subscriptions",
                subscription=f"{i + 1}/{len(subscriptions)}",
            )
            snapshots = await get_snapshots(
                subscription["id"], start_date, end_date, keyword
            )
            for snapshot in snapshots:
                snapshot["subscription_id"] = subscription["id"]
                snapshot["subscription_name"] = subscription["name"]
            all_snapshots.extend(snapshots)

            # Update the growing table
            status = (
                "[bold green]Complete[/bold green]"
                if snapshots
                else "[bold red]No snapshots found[/bold red]"
            )
            growing_table.add_row(
                subscription["name"], f"[bold magenta]{len(snapshots)}[/bold magenta]", status
            )
            live.update(Panel(Group(overall_progress, growing_table)))

    end_time = time.time()
    runtime = end_time - start_time

    # Display detailed results
    console.print("\n[bold cyan]Detailed Results:[/bold cyan]")
    for subscription in subscriptions:
        subscription_snapshots = [
            s for s in all_snapshots if s["subscription_id"] == subscription["id"]
        ]
        display_snapshots(subscription_snapshots, subscription["name"])

    # Log sorted snapshots
    log_sorted_snapshots(all_snapshots)

    total_snapshots = len(all_snapshots)
    summary = Panel(
        f"[bold green]Total snapshots found: {total_snapshots}[/bold green]\n"
        f"[bold yellow]Runtime: {runtime:.2f} seconds[/bold yellow]",
        title="Summary",
        expand=False,
    )
    console.print(summary)

    # Export to CSV
    if Prompt.ask(
        "Do you want to export results to CSV?", choices=["y", "n"], default="n"
    ) == "y":
        filename = f"snapshot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", newline="") as csvfile:
            fieldnames = [
                "name",
                "resourceGroup",
                "timeCreated",
                "createdBy",
                "subscription_name",
                "diskState",
                "id",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for snapshot in all_snapshots:
                tags = snapshot.get("tags", {})
                snapshot["createdBy"] = tags.get("CreatedByUserId", "N/A")
                writer.writerow({k: snapshot.get(k, "N/A") for k in fieldnames})
        console.print(f"[green]Results exported to {filename}[/green]")

    # Now, process snapshots for potential deletion
    non_prod_snapshots_to_delete = []
    prod_snapshots_to_delete = []

    current_time = datetime.now(timezone.utc)

    for snapshot in all_snapshots:
        subscription_name = snapshot["subscription_name"]

        # Determine if it's prod or non-prod
        if is_non_prod(subscription_name):
            env = "non-prod"
            age_limit = 3
        elif is_prod(subscription_name):
            env = "prod"
            age_limit = 7
        else:
            continue  # Skip snapshots not in prod or non-prod subscriptions

        # Calculate age
        created_date = datetime.fromisoformat(snapshot["timeCreated"])
        age_days = (current_time - created_date).days

        if age_days >= age_limit:
            # Add to deletion list
            snapshot["age_days"] = age_days
            if env == "non-prod":
                non_prod_snapshots_to_delete.append(snapshot)
            elif env == "prod":
                prod_snapshots_to_delete.append(snapshot)

    # Notify user about non-prod snapshots to delete
    if non_prod_snapshots_to_delete:
        console.print(
            f"\n[bold yellow]There are {len(non_prod_snapshots_to_delete)} non-prod snapshots that are 3 days or older.[/bold yellow]"
        )

        # Display snapshots to be deleted
        table = Table(
            title="[bold red]Non-prod Snapshots to be Deleted[/bold red]"
        )
        table.add_column("Name", style="cyan")
        table.add_column("Subscription", style="magenta")
        table.add_column("Resource Group", style="green")
        table.add_column("Age (days)", style="yellow")
        for snapshot in non_prod_snapshots_to_delete:
            table.add_row(
                snapshot["name"],
                snapshot["subscription_name"],
                snapshot["resourceGroup"],
                str(snapshot["age_days"]),
            )
        console.print(table)

        if Prompt.ask(
            "Do you want to delete these snapshots?", choices=["y", "n"], default="n"
        ) == "y":
            # Proceed to delete non-prod snapshots
            deletion_results = await delete_snapshots(non_prod_snapshots_to_delete)
            # Display summary
            console.print("\n[bold cyan]Non-prod Snapshot Deletion Results:[/bold cyan]")
            console.print(f"[bold green]Deleted snapshots: {len(deletion_results['deleted'])}[/bold green]")
            console.print(f"[bold red]Failed to delete: {len(deletion_results['failed'])}[/bold red]")
        else:
            console.print("[yellow]Skipping deletion of non-prod snapshots.[/yellow]")
    else:
        console.print("\n[bold green]No non-prod snapshots to delete.[/bold green]")

    # Notify user about prod snapshots to delete
    if prod_snapshots_to_delete:
        console.print(
            f"\n[bold yellow]There are {len(prod_snapshots_to_delete)} prod snapshots that are 7 days or older.[/bold yellow]"
        )

        # Display snapshots to be deleted
        table = Table(title="[bold red]Prod Snapshots to be Deleted[/bold red]")
        table.add_column("Name", style="cyan")
        table.add_column("Subscription", style="magenta")
        table.add_column("Resource Group", style="green")
        table.add_column("Age (days)", style="yellow")
        for snapshot in prod_snapshots_to_delete:
            table.add_row(
                snapshot["name"],
                snapshot["subscription_name"],
                snapshot["resourceGroup"],
                str(snapshot["age_days"]),
            )
        console.print(table)

        if Prompt.ask(
            "Do you want to delete these snapshots?", choices=["y", "n"], default="n"
        ) == "y":
            # Proceed to delete prod snapshots
            deletion_results = await delete_snapshots(prod_snapshots_to_delete)
            # Display summary
            console.print("\n[bold cyan]Prod Snapshot Deletion Results:[/bold cyan]")
            console.print(f"[bold green]Deleted snapshots: {len(deletion_results['deleted'])}[/bold green]")
            console.print(f"[bold red]Failed to delete: {len(deletion_results['failed'])}[/bold red]")
        else:
            console.print("[yellow]Skipping deletion of prod snapshots.[/yellow]")
    else:
        console.print("\n[bold green]No prod snapshots to delete.[/bold green]")

    console.print("\n[bold green]Snapshot search and destroy complete![/bold green]")
    logger.info("Azure Snapshot Manager completed successfully")

    # Log additional information
    logger.info(f"Total snapshots found: {total_snapshots}")
    logger.info(f"Runtime: {runtime:.2f} seconds")
    logger.info("Snapshot search and destroy complete")

def log_sorted_snapshots(all_snapshots):
    sorted_snapshots = defaultdict(lambda: defaultdict(list))
    for snapshot in all_snapshots:
        subscription_name = snapshot["subscription_name"]
        resource_group = snapshot["resourceGroup"]
        snapshot_id = snapshot["id"]
        sorted_snapshots[subscription_name][resource_group].append(snapshot_id)

    logger.info("Sorted Snapshot Resource IDs:")
    for subscription_name, resource_groups in sorted_snapshots.items():
        logger.info(f"Subscription: {subscription_name}")
        for resource_group, snapshot_ids in resource_groups.items():
            logger.info(f"  Resource Group: {resource_group}")
            for snapshot_id in snapshot_ids:
                logger.info(f"    {snapshot_id}")

if __name__ == "__main__":
    asyncio.run(main())
