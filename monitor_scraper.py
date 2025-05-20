import json
import os
import time
from datetime import datetime
import argparse
import sys

def check_scraper_status(output_dir):
    """Check the status of the scraper"""
    
    # Check if output directory exists
    if not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' not found!")
        return False
        
    status_file = os.path.join(output_dir, 'status.json')
    pid_file = os.path.join(output_dir, 'scraper.pid')
    logs_dir = os.path.join(output_dir, 'logs')
    
    print("\n" + "="*50)
    print(f"Scraper Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Check status file
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            print(f"\nStatus Information:")
            print(f"Current Status: {status['status']}")
            print(f"Last Updated: {status['last_updated']}")
        except Exception as e:
            print(f"\nError reading status file: {str(e)}")
    else:
        print("\nStatus file not found!")
    
    # Check PID file and process status
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if process is running
                print(f"\nProcess Status: RUNNING (PID: {pid})")
            except OSError:
                print(f"\nProcess Status: NOT RUNNING (Last PID: {pid})")
        except Exception as e:
            print(f"\nError checking process: {str(e)}")
    else:
        print("\nPID file not found - Process may not be running")
    
    # Check latest log file
    if os.path.exists(logs_dir):
        log_files = sorted([f for f in os.listdir(logs_dir) if f.endswith('.log')], reverse=True)
        if log_files:
            latest_log = os.path.join(logs_dir, log_files[0])
            print(f"\nLatest Log File: {log_files[0]}")
            print("\nLast 10 log entries:")
            print("-"*50)
            try:
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.strip())
            except Exception as e:
                print(f"Error reading log file: {str(e)}")
        else:
            print("\nNo log files found!")
    else:
        print("\nLogs directory not found!")
    
    # Check output files
    print("\nOutput Files Status:")
    print("-"*50)
    try:
        categories = [d for d in os.listdir(output_dir) 
                     if os.path.isdir(os.path.join(output_dir, d)) 
                     and not d == 'logs']
        for category in categories:
            category_dir = os.path.join(output_dir, category)
            files = [f for f in os.listdir(category_dir) if f.endswith('.csv')]
            print(f"\n{category}:")
            for file in files:
                file_path = os.path.join(category_dir, file)
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"- {file}")
                print(f"  Size: {size/1024:.2f} KB")
                print(f"  Last Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error checking output files: {str(e)}")

def monitor_continuously(output_dir, interval):
    """Monitor the scraper continuously with specified interval"""
    try:
        while True:
            check_scraper_status(output_dir)
            print(f"\nNext check in {interval} seconds...")
            print("\nPress Ctrl+C to stop monitoring")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Monitor Amazon Product Scraper Status')
    parser.add_argument('output_dir', help='Output directory to monitor')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring interval in seconds (default: 300)')
    parser.add_argument('--continuous', action='store_true',
                       help='Monitor continuously with specified interval')
    
    args = parser.parse_args()
    
    if args.continuous:
        monitor_continuously(args.output_dir, args.interval)
    else:
        check_scraper_status(args.output_dir)

if __name__ == "__main__":
    main() 