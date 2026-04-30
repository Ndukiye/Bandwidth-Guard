
from config import user_presets
from storage import get_bandwith_data,get_presets
from datetime import date
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

console = Console()
#Display data usage details
def display_usage(data,presets):
    if not data:
        print("[bold red]No bandwidth data yet. Monitor must be running.[/bold red]")
        return
    if not presets:
        console.print("[bold red]No preset configured. Use option 2 to set up.[/bold red]")
        return
    item_data = data[-1]
    item_presets = presets[0]
    percentage = (item_data["total_mb"] / item_presets["usage_limits"]) * 100
    if percentage >= 100:
       status = "[bold red]⚠ CAP REACHED[/bold red]"
    elif percentage >=80:
        status = "[bold yellow]⚠ Warning: 80%+[/bold yellow]"
    else:
        status = "[bold green]✓ Within limit[/bold green]"
    
    content = f'''[bold green]Plan:[/bold green] [bold blue]{item_presets["data_plan"]}[/bold blue]
[bold green]Cap:[/bold green] [bold blue]{item_presets["usage_limits"]}mb[/bold blue]
[bold green]Used:[/bold green] [bold blue]{item_data["total_mb"]}mb[/bold blue] ({percentage:.1f}%)
[bold green]Speed:[/bold green] [bold blue]{item_data["speed_mbps"]}mbps[/bold blue]
{status}'''

    console.print(Panel(content, title="Bandwidth Guardian", border_style="blue"))
    
# console.print("[bold green]Data used:[/bold green] 450 MB")

while True:
    user_input = input("\nBandwith Guardian - 1\nEdit Config - 2\nClose - 3\n")
    match user_input:
        case "1": 
            display_usage(get_bandwith_data(),get_presets())
        case "2":
            user_presets()
        case "3":
            break

