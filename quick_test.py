#!/usr/bin/env python
"""Quick test of Snakemake with correct syntax."""

import subprocess
import sys
from datetime import datetime

def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

def main():
    log('Testing Snakemake syntax fixes...')
    
    # Test 1: Check if dry run works with correct syntax
    log('Testing dry run...')
    
    try:
        result = subprocess.run([
            'snakemake', '--dry-run', '--quiet', 'all'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            log('✓ Dry run syntax is correct!')
            jobs_count = result.stdout.count(' job ')
            log(f'Jobs found: {jobs_count}')
        else:
            log('✗ Dry run failed')
            print('STDERR:', result.stderr[:200])
            
    except Exception as e:
        log(f'✗ Error: {e}')
    
    # Test 2: Check simple command with local-storage-prefix
    log('Testing with local storage optimization...')
    
    try:
        # Use local temp directory to avoid network filesystem issues
        import tempfile
        local_temp = tempfile.gettempdir()
        
        result = subprocess.run([
            'snakemake', '--dry-run', '--quiet', 'all',
            '--local-storage-prefix', local_temp,
            '--shared-fs-usage', 'none'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            log('✓ Local storage optimization syntax is correct!')
        else:
            log('✗ Local storage optimization failed')
            print('STDERR:', result.stderr[:200])
            
    except Exception as e:
        log(f'✗ Error: {e}')
    
    log('✓ Quick test completed!')

if __name__ == '__main__':
    main()
