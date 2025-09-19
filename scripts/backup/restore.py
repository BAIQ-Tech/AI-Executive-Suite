#!/usr/bin/env python3
"""
Disaster recovery and restore script for AI Executive Suite
"""

import os
import sys
import logging
import subprocess
import boto3
from datetime import datetime
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RestoreService:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.s3_bucket = os.getenv('BACKUP_S3_BUCKET')
        self.restore_dir = Path('/app/restore')
        self.uploads_dir = Path('/app/uploads')
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3')
        
        # Ensure restore directory exists
        self.restore_dir.mkdir(exist_ok=True)
    
    def list_available_backups(self, backup_type='database'):
        """List available backups from S3"""
        try:
            prefix = f"{backup_type}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            backups = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified']
                    })
            
            # Sort by modification date (newest first)
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def download_backup(self, s3_key):
        """Download backup file from S3"""
        try:
            local_file = self.restore_dir / Path(s3_key).name
            
            logger.info(f"Downloading backup from S3: {s3_key}")
            
            self.s3_client.download_file(
                self.s3_bucket,
                s3_key,
                str(local_file)
            )
            
            logger.info(f"Downloaded backup to: {local_file}")
            return str(local_file)
            
        except Exception as e:
            logger.error(f"Error downloading backup: {e}")
            return None
    
    def restore_database(self, backup_file=None, backup_date=None):
        """Restore database from backup"""
        try:
            if not backup_file:
                # Find latest backup if no specific file provided
                backups = self.list_available_backups('database')
                if not backups:
                    logger.error("No database backups found")
                    return False
                
                # Filter by date if provided
                if backup_date:
                    backups = [b for b in backups if backup_date in b['key']]
                    if not backups:
                        logger.error(f"No backups found for date: {backup_date}")
                        return False
                
                # Download latest backup
                backup_file = self.download_backup(backups[0]['key'])
                if not backup_file:
                    return False
            
            logger.info(f"Restoring database from: {backup_file}")
            
            # Decompress if needed
            if backup_file.endswith('.gz'):
                subprocess.run(['gunzip', backup_file], check=True)
                backup_file = backup_file[:-3]  # Remove .gz extension
            
            # Restore database
            cmd = [
                'psql',
                self.db_url,
                '--no-password',
                '--verbose',
                '-f', backup_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def restore_files(self, backup_file=None, backup_date=None):
        """Restore uploaded files from backup"""
        try:
            if not backup_file:
                # Find latest backup if no specific file provided
                backups = self.list_available_backups('files')
                if not backups:
                    logger.error("No file backups found")
                    return False
                
                # Filter by date if provided
                if backup_date:
                    backups = [b for b in backups if backup_date in b['key']]
                    if not backups:
                        logger.error(f"No file backups found for date: {backup_date}")
                        return False
                
                # Download latest backup
                backup_file = self.download_backup(backups[0]['key'])
                if not backup_file:
                    return False
            
            logger.info(f"Restoring files from: {backup_file}")
            
            # Extract files
            cmd = [
                'tar',
                '-xzf', backup_file,
                '-C', str(self.uploads_dir.parent)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Files restored successfully")
                return True
            else:
                logger.error(f"Files restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring files: {e}")
            return False
    
    def full_restore(self, backup_date=None):
        """Perform full system restore"""
        logger.info("Starting full system restore")
        
        # Restore database
        db_success = self.restore_database(backup_date=backup_date)
        
        # Restore files
        files_success = self.restore_files(backup_date=backup_date)
        
        if db_success and files_success:
            logger.info("Full system restore completed successfully")
            return True
        else:
            logger.error("Full system restore completed with errors")
            return False

def main():
    parser = argparse.ArgumentParser(description='AI Executive Suite Restore Service')
    parser.add_argument('action', choices=['list', 'restore-db', 'restore-files', 'full-restore'],
                       help='Action to perform')
    parser.add_argument('--date', help='Backup date (YYYYMMDD format)')
    parser.add_argument('--file', help='Specific backup file to restore')
    parser.add_argument('--type', choices=['database', 'files'], default='database',
                       help='Backup type to list')
    
    args = parser.parse_args()
    
    service = RestoreService()
    
    if args.action == 'list':
        backups = service.list_available_backups(args.type)
        print(f"\nAvailable {args.type} backups:")
        print("-" * 80)
        for backup in backups:
            print(f"{backup['key']:<50} {backup['size']:>10} bytes {backup['modified']}")
    
    elif args.action == 'restore-db':
        success = service.restore_database(args.file, args.date)
        sys.exit(0 if success else 1)
    
    elif args.action == 'restore-files':
        success = service.restore_files(args.file, args.date)
        sys.exit(0 if success else 1)
    
    elif args.action == 'full-restore':
        success = service.full_restore(args.date)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()