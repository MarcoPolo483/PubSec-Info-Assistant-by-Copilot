"""Automated DR backup and restore scripts for Qdrant, Redis, and Azure Blob."""
import asyncio
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DisasterRecoveryManager:
    """Manages backup and restore operations for all data stores."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        backup_root: Path = Path("./backups")
    ):
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    async def backup_qdrant(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Qdrant collection snapshot.
        
        Args:
            tenant_id: Specific tenant to backup, or None for all
        
        Returns:
            Backup metadata
        """
        logger.info(f"Starting Qdrant backup (tenant: {tenant_id or 'all'})")
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        try:
            import httpx
            
            # Get all collections if tenant not specified
            if tenant_id:
                collections = [f"{tenant_id}_documents"]
            else:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://{self.qdrant_host}:{self.qdrant_port}/collections")
                    resp.raise_for_status()
                    data = resp.json()
                    collections = [c["name"] for c in data.get("result", {}).get("collections", [])]
            
            logger.info(f"Backing up {len(collections)} collections")
            
            snapshots = []
            for collection in collections:
                try:
                    # Create snapshot via API
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            f"http://{self.qdrant_host}:{self.qdrant_port}/collections/{collection}/snapshots"
                        )
                        resp.raise_for_status()
                        snapshot_data = resp.json()
                    
                    snapshot_name = snapshot_data.get("result", {}).get("name")
                    
                    if snapshot_name:
                        # Download snapshot
                        backup_dir = self.backup_root / "qdrant" / timestamp
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        
                        snapshot_path = backup_dir / f"{collection}.snapshot"
                        
                        async with httpx.AsyncClient() as client:
                            resp = await client.get(
                                f"http://{self.qdrant_host}:{self.qdrant_port}/collections/{collection}/snapshots/{snapshot_name}"
                            )
                            resp.raise_for_status()
                            
                            with open(snapshot_path, "wb") as f:
                                f.write(resp.content)
                        
                        snapshots.append({
                            "collection": collection,
                            "snapshot_name": snapshot_name,
                            "path": str(snapshot_path),
                            "size_bytes": snapshot_path.stat().st_size
                        })
                        
                        logger.info(f"✓ Backed up collection: {collection}")
                
                except Exception as e:
                    logger.error(f"✗ Failed to backup {collection}: {e}")
            
            # Write metadata
            metadata = {
                "timestamp": timestamp,
                "type": "qdrant",
                "tenant_id": tenant_id,
                "collections": len(snapshots),
                "snapshots": snapshots,
                "status": "success" if snapshots else "failed"
            }
            
            metadata_path = self.backup_root / "qdrant" / timestamp / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Qdrant backup complete: {len(snapshots)} collections")
            return metadata
        
        except Exception as e:
            logger.error(f"✗ Qdrant backup failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    async def restore_qdrant(self, backup_timestamp: str, tenant_id: Optional[str] = None) -> bool:
        """
        Restore Qdrant collections from snapshot.
        
        Args:
            backup_timestamp: Timestamp of backup to restore (e.g., "20251201-143000")
            tenant_id: Specific tenant to restore, or None for all
        
        Returns:
            Success status
        """
        logger.info(f"Starting Qdrant restore from {backup_timestamp}")
        
        try:
            import httpx
            
            backup_dir = self.backup_root / "qdrant" / backup_timestamp
            
            if not backup_dir.exists():
                logger.error(f"Backup not found: {backup_dir}")
                return False
            
            # Load metadata
            metadata_path = backup_dir / "metadata.json"
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            snapshots = metadata.get("snapshots", [])
            
            if tenant_id:
                snapshots = [s for s in snapshots if s["collection"].startswith(tenant_id)]
            
            logger.info(f"Restoring {len(snapshots)} collections")
            
            for snapshot in snapshots:
                try:
                    collection = snapshot["collection"]
                    snapshot_path = Path(snapshot["path"])
                    
                    # Upload snapshot
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        with open(snapshot_path, "rb") as f:
                            files = {"snapshot": f}
                            resp = await client.post(
                                f"http://{self.qdrant_host}:{self.qdrant_port}/collections/{collection}/snapshots/upload",
                                files=files
                            )
                            resp.raise_for_status()
                    
                    logger.info(f"✓ Restored collection: {collection}")
                
                except Exception as e:
                    logger.error(f"✗ Failed to restore {collection}: {e}")
                    return False
            
            logger.info(f"✓ Qdrant restore complete")
            return True
        
        except Exception as e:
            logger.error(f"✗ Qdrant restore failed: {e}", exc_info=True)
            return False
    
    async def backup_redis(self) -> Dict[str, Any]:
        """
        Create Redis RDB snapshot.
        
        Returns:
            Backup metadata
        """
        logger.info("Starting Redis backup")
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        try:
            # Trigger BGSAVE
            result = subprocess.run(
                ["redis-cli", "-h", self.redis_host, "-p", str(self.redis_port), "BGSAVE"],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Redis BGSAVE triggered")
            
            # Wait for save to complete
            await asyncio.sleep(2)
            
            # Check LASTSAVE
            result = subprocess.run(
                ["redis-cli", "-h", self.redis_host, "-p", str(self.redis_port), "LASTSAVE"],
                capture_output=True,
                text=True,
                check=True
            )
            
            lastsave_ts = int(result.stdout.strip())
            
            # Copy RDB file
            backup_dir = self.backup_root / "redis" / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Assume standard Redis data directory (adjust if needed)
            import shutil
            rdb_source = Path("/var/lib/redis/dump.rdb")  # Adjust path if needed
            
            if rdb_source.exists():
                rdb_backup = backup_dir / "dump.rdb"
                shutil.copy2(rdb_source, rdb_backup)
                
                metadata = {
                    "timestamp": timestamp,
                    "type": "redis",
                    "lastsave": lastsave_ts,
                    "path": str(rdb_backup),
                    "size_bytes": rdb_backup.stat().st_size,
                    "status": "success"
                }
            else:
                logger.warning(f"RDB file not found at {rdb_source}")
                metadata = {
                    "timestamp": timestamp,
                    "type": "redis",
                    "status": "partial",
                    "note": "BGSAVE triggered but RDB file not accessible"
                }
            
            # Write metadata
            metadata_path = backup_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Redis backup complete")
            return metadata
        
        except Exception as e:
            logger.error(f"✗ Redis backup failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
    
    async def validate_backup(self, backup_type: str, backup_timestamp: str) -> bool:
        """
        Validate backup integrity.
        
        Args:
            backup_type: "qdrant" or "redis"
            backup_timestamp: Timestamp of backup
        
        Returns:
            Validation status
        """
        logger.info(f"Validating {backup_type} backup: {backup_timestamp}")
        
        try:
            backup_dir = self.backup_root / backup_type / backup_timestamp
            
            if not backup_dir.exists():
                logger.error(f"Backup directory not found: {backup_dir}")
                return False
            
            # Check metadata
            metadata_path = backup_dir / "metadata.json"
            if not metadata_path.exists():
                logger.error("Metadata file missing")
                return False
            
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            if metadata.get("status") != "success":
                logger.error(f"Backup status: {metadata.get('status')}")
                return False
            
            # Validate files
            if backup_type == "qdrant":
                snapshots = metadata.get("snapshots", [])
                for snapshot in snapshots:
                    path = Path(snapshot["path"])
                    if not path.exists():
                        logger.error(f"Snapshot file missing: {path}")
                        return False
                    
                    if path.stat().st_size != snapshot["size_bytes"]:
                        logger.error(f"Snapshot size mismatch: {path}")
                        return False
            
            elif backup_type == "redis":
                rdb_path = Path(metadata.get("path", ""))
                if rdb_path.exists():
                    if rdb_path.stat().st_size != metadata["size_bytes"]:
                        logger.error(f"RDB size mismatch")
                        return False
            
            logger.info(f"✓ Backup validation passed")
            return True
        
        except Exception as e:
            logger.error(f"✗ Validation failed: {e}", exc_info=True)
            return False
    
    async def cleanup_old_backups(self, retention_days: int = 30):
        """Remove backups older than retention period."""
        logger.info(f"Cleaning up backups older than {retention_days} days")
        
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        deleted = 0
        
        for backup_type in ["qdrant", "redis"]:
            type_dir = self.backup_root / backup_type
            
            if not type_dir.exists():
                continue
            
            for backup_dir in type_dir.iterdir():
                if not backup_dir.is_dir():
                    continue
                
                try:
                    # Parse timestamp from dir name
                    ts_str = backup_dir.name
                    backup_date = datetime.strptime(ts_str, "%Y%m%d-%H%M%S")
                    
                    if backup_date < cutoff:
                        import shutil
                        shutil.rmtree(backup_dir)
                        deleted += 1
                        logger.info(f"Deleted old backup: {backup_dir}")
                
                except Exception as e:
                    logger.warning(f"Failed to process {backup_dir}: {e}")
        
        logger.info(f"✓ Cleanup complete: {deleted} old backups removed")


async def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DR backup/restore manager")
    parser.add_argument("command", choices=["backup", "restore", "validate", "cleanup"])
    parser.add_argument("--type", choices=["qdrant", "redis", "all"], default="all")
    parser.add_argument("--tenant", help="Tenant ID (Qdrant only)")
    parser.add_argument("--timestamp", help="Backup timestamp for restore/validate")
    parser.add_argument("--retention-days", type=int, default=30, help="Retention for cleanup")
    
    args = parser.parse_args()
    
    manager = DisasterRecoveryManager()
    
    if args.command == "backup":
        if args.type in ["qdrant", "all"]:
            result = await manager.backup_qdrant(args.tenant)
            print(f"Qdrant backup: {result['status']}")
        
        if args.type in ["redis", "all"]:
            result = await manager.backup_redis()
            print(f"Redis backup: {result['status']}")
    
    elif args.command == "restore":
        if not args.timestamp:
            print("Error: --timestamp required for restore")
            sys.exit(1)
        
        if args.type == "qdrant":
            success = await manager.restore_qdrant(args.timestamp, args.tenant)
            sys.exit(0 if success else 1)
        else:
            print("Error: Only Qdrant restore implemented")
            sys.exit(1)
    
    elif args.command == "validate":
        if not args.timestamp:
            print("Error: --timestamp required for validate")
            sys.exit(1)
        
        if args.type == "all":
            qdrant_ok = await manager.validate_backup("qdrant", args.timestamp)
            redis_ok = await manager.validate_backup("redis", args.timestamp)
            sys.exit(0 if (qdrant_ok and redis_ok) else 1)
        else:
            success = await manager.validate_backup(args.type, args.timestamp)
            sys.exit(0 if success else 1)
    
    elif args.command == "cleanup":
        await manager.cleanup_old_backups(args.retention_days)


if __name__ == "__main__":
    asyncio.run(main())
