#!/usr/bin/env python
"""Test week slice run."""

import shutil
import subprocess
import time
from datetime import datetime

def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

def main():
    log('Starting week slice test...')
    
    # Backup existing config
    try:
        shutil.copy2('config/config.yaml', 'config/config.yaml.backup')
        log('Backed up existing config')
    except FileNotFoundError:
        pass
    
    # Apply week configuration
    log('Applying week configuration...')
    shutil.copy2('config/config.test-week.yaml', 'config/config.yaml')
    
    # Test dry run first
    log('Testing dry run...')
    result = subprocess.run([
        'snakemake', '-j1', '--dry-run', 
        'results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc'
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        log('✓ Dry run successful!')
        jobs_count = result.stdout.count('job ')
        log(f'Jobs planned: {jobs_count}')
        
        # Run actual benchmark (short version)
        log('Running actual week slice (limited time)...')
        start_time = time.time()
        
        # Run for max 10 minutes as a test
        result = subprocess.run([
            'snakemake', '-j2', '--forceall',
            'results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc'
        ], capture_output=True, text=True, timeout=600)  # 10 minutes
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            log(f'✓ Week slice completed in {elapsed/60:.1f} minutes!')
        else:
            log(f'Week slice running... (stopped after {elapsed/60:.1f} minutes for testing)')
            log(f'Return code: {result.returncode}')
            if result.stderr:
                print('Recent stderr:', result.stderr[-300:])
        
    else:
        log('✗ Dry run failed')
        print('STDERR:', result.stderr[:500])
    
    # Restore original config
    try:
        shutil.move('config/config.yaml.backup', 'config/config.yaml')
        log('Restored original configuration')
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    main()
