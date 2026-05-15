from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from storage import (
    get_today_usage,
    get_date_range_usage,
    get_bandwith_data,
)
from config_loader import save_limit_config,load_enforcement_config,set_data_plan


console = Console()

def show_status():
    """Show system-wide + per-process bandwidth usage"""
    
    # === SYSTEM-WIDE DATA ===
    system_data = get_bandwith_data()
    today_str = str(date.today())
    today_system = None
    
    if system_data:
        for entry in reversed(system_data):
            if entry.get('date') == today_str:
                today_system = entry
                break
    
    # Get config for limits
    config = load_enforcement_config()
    data_plan = config.get('global', {}).get('data_plan', 'Not configured')
    daily_limit = config.get('global', {}).get('daily_limit_mb', 'Not set')
    
    # Display system panel
    if today_system:
        total_mb = today_system.get('total_mb', 0)
        speed_mbps = today_system.get('speed_mbps', 0)
        
        if daily_limit != 'Not set':
            percentage = (total_mb / daily_limit) * 100
            if percentage >= 100:
                status = "[bold red]⚠ CAP REACHED[/bold red]"
            elif percentage >= 80:
                status = "[bold yellow]⚠ Warning: 80%+[/bold yellow]"
            else:
                status = "[bold green]✓ Within limit[/bold green]"
        else:
            status = "[dim]No limit set[/dim]"
            percentage = 0
        
        system_content = f"""[bold green]Plan:[/bold green] [bold blue]{data_plan}[/bold blue]
[bold green]Daily Limit:[/bold green] [bold blue]{daily_limit} MB[/bold blue]
[bold green]Used Today:[/bold green] [bold blue]{total_mb:.1f} MB[/bold blue] ({percentage:.1f}%)
[bold green]Current Speed:[/bold green] [bold blue]{speed_mbps:.2f} Mbps[/bold blue]
{status}"""
        
        console.print(Panel(system_content, title="📊 System Overview", border_style="blue"))
    else:
        console.print("[yellow]No system-wide data tracked today.[/yellow]")
    
    console.print()  # Blank line
    
    # === PER-PROCESS DATA ===
    usage = get_today_usage()
    
    if not usage:
        console.print("[yellow]No per-process data tracked today.[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Per-Process Usage - {date.today()}")
    table.add_column("Process", style="cyan")
    table.add_column("Download", justify="right", style="green")
    table.add_column("Upload", justify="right", style="yellow")
    table.add_column("Total", justify="right", style="magenta")
    table.add_column("Limit", justify="right", style="red")
    table.add_column("Status", justify="center")
    
    # Get process limits
    process_limits = config.get('processes', {})
    
    # Sort by total usage
    sorted_procs = sorted(
        usage.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    for process_name, stats in sorted_procs:
        limit_config = process_limits.get(process_name, {})
        limit_mb = limit_config.get('limit_mb', '-')
        
        if limit_mb != '-':
            percentage = (stats['total'] / limit_mb) * 100
            if percentage >= 100:
                status = "🔴"
            elif percentage >= 80:
                status = "🟡"
            else:
                status = "✅"
            limit_str = f"{limit_mb} MB"
        else:
            status = "-"
            limit_str = "No limit"
        
        table.add_row(
            process_name,
            f"{stats['recv']:.1f} MB",
            f"{stats['send']:.1f} MB",
            f"{stats['total']:.1f} MB",
            limit_str,
            status
        )
    
    console.print(table)

def show_history(days=7):
    """Show usage over last N days"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    usage = get_date_range_usage(start_date, end_date)
    
    if not usage:
        console.print(f"[yellow]No data for last {days} days.[/yellow]")
        return
    
    table = Table(title=f"Last {days} Days ({start_date} to {end_date})")
    table.add_column("Process", style="cyan")
    table.add_column("Download", justify="right", style="green")
    table.add_column("Upload", justify="right", style="yellow")
    table.add_column("Total", justify="right", style="magenta")
    
    sorted_procs = sorted(
        usage.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )
    
    for process_name, stats in sorted_procs:
        table.add_row(
            process_name,
            f"{stats['recv']:.1f} MB",
            f"{stats['send']:.1f} MB",
            f"{stats['total']:.1f} MB"
        )
    
    console.print(table)

def set_limit(process_name, limit_mb, action="kill"):
    """Set bandwidth limit for a process"""
    config = load_enforcement_config()
    
    if 'processes' not in config:
        config['processes'] = {}
    
    config['processes'][process_name] = {
        'limit_mb': limit_mb,
        'action': action
    }
    
    save_limit_config(config)
    console.print(f"[green]✓[/green] Set {process_name} limit to {limit_mb}MB (action: {action})")

def list_limits():
    """Show configured limits"""
    config = load_enforcement_config()
    processes = config.get('processes', {})
    
    if not processes:
        console.print("[yellow]No limits configured.[/yellow]")
        return
    
    table = Table(title="Configured Limits")
    table.add_column("Process", style="cyan")
    table.add_column("Limit", justify="right", style="magenta")
    table.add_column("Action", style="yellow")
    
    for process_name, settings in processes.items():
        table.add_row(
            process_name,
            f"{settings['limit_mb']} MB",
            settings['action']
        )
    
    console.print(table)

def remove_limit(process_name):
    """Remove limit for a specific process"""
    config = load_enforcement_config()
    
    if process_name in config.get('processes', {}):
        del config['processes'][process_name]
        save_limit_config(config)
        console.print(f"[green]✓[/green] Removed limit for {process_name}")
    else:
        console.print(f"[yellow]No limit set for {process_name}[/yellow]")

def clear_all_limits():
    """Remove all process limits"""
    config = load_enforcement_config()
    config['processes'] = {}
    save_limit_config(config)
    console.print(f"[green]✓[/green] Cleared all process limits")

def configure_plan():
    """Configure data plan interactively"""
    plan = input("Plan name (e.g., MTN 5GB Daily, 700mb): ").strip()
    limit = int(input("Daily limit (MB): ").strip())
    set_data_plan(plan, limit)
    console.print(f"[green]✓[/green] Set plan: {plan} ({limit}MB)")