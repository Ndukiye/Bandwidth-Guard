# handles user interaction
import argparse
from rich.console import Console

from src.cli import show_status,show_history,set_limit,remove_limit,clear_all_limits,list_limits,configure_plan

console = Console()


def interactive_menu():
    """Interactive menu"""
    while True:
        console.print("\n[bold cyan]Bandwidth Guardian[/bold cyan]")
        console.print("1. View Status")
        console.print("2. View History")
        console.print("3. Set Limit")
        console.print("4. Remove Limit")
        console.print("5. List Limits")
        console.print("6. Clear All Limits")
        console.print("7. Configure Plan")
        console.print("8. Exit")
        
        choice = input("\nSelect: ").strip()
        
        if choice == "1":
            show_status()
        elif choice == "2":
            days = input("Days (default 7): ").strip()
            show_history(int(days) if days else 7)
        elif choice == "3":
            process = input("Process name: ").strip()
            limit = int(input("Limit (MB): ").strip())
            action = input("Action (kill/warn): ").strip() or "warn"
            set_limit(process, limit, action)
        elif choice == "4":
            process = input("Process name: ").strip()
            remove_limit(process)
        elif choice == "5":
            list_limits()
        elif choice == "6":
            clear_all_limits()
        elif choice == "7":
            configure_plan()
        elif choice == "8":
            break

def main():
    parser = argparse.ArgumentParser(description="Bandwidth Guard")
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--action', default='warn')
    
    args = parser.parse_args()
    
    if not args.command:
        interactive_menu()
        return
    
    if args.command == 'status':
        show_status()
    elif args.command == 'history':
        show_history(args.days)
    elif args.command == 'set-limit':
        if len(args.args) < 2:
            console.print("[red]Usage: set-limit <process> <limit_mb>[/red]")
        else:
            set_limit(args.args[0], int(args.args[1]), args.action)
    elif args.command == 'remove-limit':
        if len(args.args) < 1:
            console.print("[red]Usage: remove-limit <process>[/red]")
        else:
            remove_limit(args.args[0])
    elif args.command == 'clear-limits':
        clear_all_limits()
    elif args.command == 'limits':
        list_limits()
    elif args.command == 'configure-plan':
        configure_plan()
if __name__ == "__main__":
    main()