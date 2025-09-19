#!/usr/bin/env python3
"""
Automated backup service for AI Executive Suite
Handles database backups, file backups, and disaster recovery
"""

import os
import sys
import time
import logging
import schedule
import subprocess
import boto3
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.s3_bucket = os.getenv('BACKUP_S3_BUCKET')
        self.backup_dir = Path('/app/backups')
        self.uploads_dir = Path('/app/uploads')
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3')
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_database_backup(self):
        """Create PostgreSQL database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'db_backup_{timestamp}.sql'
            
            logger.info(f"Creating database backup: {backup_file}")
            
            # Create database dump
            cmd = [
                'pg_dump',
                self.db_url,
                '--no-password',
                '--verbose',
                '--clean',
                '--no-acl',
                '--no-owner',
                '-f', str(backup_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {backup_file}")
                
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                subprocess.run(['gzip', str(backup_file)], check=True)
                
                # Upload to S3
                self.upload_to_s3(compressed_file, f"database/{timestamp}/db_backup.sql.gz")
                
                # Clean up old local backups (keep last 7 days)
                self.cleanup_old_backups('db_backup_*.sql.gz', days=7)
                
                return compressed_file
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return None
    
    def create_files_backup(self):
        """Create backup of uploaded files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'files_backup_{timestamp}.tar.gz'
            
            logger.info(f"Creating files backup: {backup_file}")
            
            # Create tar archive of uploads directory
            cmd = [
                'tar',
                '-czf', str(backup_file),
                '-C', str(self.uploads_dir.parent),
                self.uploads_dir.name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Files backup created successfully: {backup_file}")
                
                # Upload to S3
                self.upload_to_s3(str(backup_file), f"files/{timestamp}/files_backup.tar.gz")
                
                # Clean up old local backups
                self.cleanup_old_backups('files_backup_*.tar.gz', days=7)
                
                return str(backup_file)
            else:
                logger.error(f"Files backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating files backup: {e}")
            return None
    
    def upload_to_s3(self, local_file, s3_key):
        """Upload backup file to S3"""
        try:
            logger.info(f"Uploading {local_file} to S3: {s3_key}")
            
            self.s3_client.upload_file(
                local_file,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            logger.info(f"Successfully uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
    
    def cleanup_old_backups(self, pattern, days=7):
        """Remove local backup files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for backup_file in self.backup_dir.glob(pattern):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def cleanup_old_s3_backups(self, prefix, days=30):
        """Remove S3 backup files older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3_client.delete_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        logger.info(f"Removed old S3 backup: {obj['Key']}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old S3 backups: {e}")
    
    def full_backup(self):
        """Perform full system backup"""
        logger.info("Starting full system backup")
        
        # Create database backup
        db_backup = self.create_database_backup()
        
        # Create files backup
        files_backup = self.create_files_backup()
        
        # Clean up old S3 backups
        self.cleanup_old_s3_backups('database/', days=30)
        self.cleanup_old_s3_backups('files/', days=30)
        
        if db_backup and files_backup:
            logger.info("Full system backup completed successfully")
        else:
            logger.error("Full system backup completed with errors")
    
    def incremental_backup(self):
        """Perform incremental backup (database only)"""
        logger.info("Starting incremental backup")
        self.create_database_backup()
    
    def health_check(self):
        """Check backup system health"""
        try:
            # Check database connectivity
            result = subprocess.run(
                ['pg_isready', '-d', self.db_url],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Database health check failed")
                return False
            
            # Check S3 connectivity
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            
            # Check disk space
            backup_disk_usage = subprocess.run(
                ['df', '-h', str(self.backup_dir)],
                capture_output=True,
                text=True
            )
            
            logger.info(f"Backup system health check passed")
            logger.info(f"Disk usage: {backup_disk_usage.stdout}")
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def run(self):
        """Run backup service with scheduled tasks"""
        logger.info("Starting backup service")
        
        # Schedule backups
        schedule.every().day.at("02:00").do(self.full_backup)
        schedule.every(6).hours.do(self.incremental_backup)
        schedule.every().hour.do(self.health_check)
        
        # Run initial health check
        self.health_check()
        
        # Keep service running
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    service = BackupService()
    service.run()