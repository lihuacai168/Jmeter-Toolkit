"""Monitoring and health check utilities."""
import psutil
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from sqlalchemy import text
from loguru import logger

from config import settings
from database import SessionLocal


# Prometheus metrics
REQUEST_COUNT = Counter('jmeter_toolkit_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('jmeter_toolkit_request_duration_seconds', 'Request duration')
ACTIVE_TASKS = Gauge('jmeter_toolkit_active_tasks', 'Number of active tasks')
SYSTEM_CPU_PERCENT = Gauge('jmeter_toolkit_system_cpu_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_PERCENT = Gauge('jmeter_toolkit_system_memory_percent', 'System memory usage percentage')
DISK_USAGE_PERCENT = Gauge('jmeter_toolkit_disk_usage_percent', 'Disk usage percentage', ['path'])


class HealthChecker:
    """Health check utilities."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database connection failed: {str(e)}"}
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            r = redis.from_url(settings.redis_url)
            r.ping()
            return {"status": "healthy", "message": "Redis connection successful"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Redis connection failed: {str(e)}"}
    
    @staticmethod
    def check_disk_space() -> Dict[str, Any]:
        """Check disk space."""
        try:
            # Check main directory
            usage = psutil.disk_usage(str(Path.cwd()))
            free_percent = (usage.free / usage.total) * 100
            
            if free_percent < 10:
                return {"status": "unhealthy", "message": f"Low disk space: {free_percent:.1f}% free"}
            elif free_percent < 20:
                return {"status": "warning", "message": f"Disk space getting low: {free_percent:.1f}% free"}
            else:
                return {"status": "healthy", "message": f"Disk space OK: {free_percent:.1f}% free"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Disk space check failed: {str(e)}"}
    
    @staticmethod
    def check_jmeter() -> Dict[str, Any]:
        """Check JMeter installation."""
        try:
            jmeter_bin = Path(settings.jmeter_home) / "bin" / "jmeter"
            if jmeter_bin.exists():
                return {"status": "healthy", "message": "JMeter installation found"}
            else:
                return {"status": "unhealthy", "message": "JMeter installation not found"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"JMeter check failed: {str(e)}"}
    
    @staticmethod
    def check_directories() -> Dict[str, Any]:
        """Check required directories."""
        try:
            directories = [
                settings.jmx_files_path,
                settings.jtl_files_path,
                settings.reports_path
            ]
            
            missing_dirs = []
            for directory in directories:
                if not directory.exists():
                    missing_dirs.append(str(directory))
            
            if missing_dirs:
                return {"status": "unhealthy", "message": f"Missing directories: {missing_dirs}"}
            else:
                return {"status": "healthy", "message": "All required directories exist"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Directory check failed: {str(e)}"}
    
    @classmethod
    def get_health_status(cls) -> Dict[str, Any]:
        """Get overall health status."""
        checks = {
            "database": cls.check_database(),
            "redis": cls.check_redis(),
            "disk_space": cls.check_disk_space(),
            "jmeter": cls.check_jmeter(),
            "directories": cls.check_directories()
        }
        
        # Determine overall status
        unhealthy_services = [name for name, check in checks.items() if check["status"] == "unhealthy"]
        warning_services = [name for name, check in checks.items() if check["status"] == "warning"]
        
        if unhealthy_services:
            overall_status = "unhealthy"
        elif warning_services:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "services": checks
        }


class MetricsCollector:
    """Metrics collection utilities."""
    
    @staticmethod
    def collect_system_metrics():
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_PERCENT.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_PERCENT.set(memory.percent)
            
            # Disk usage
            for path in [settings.jmx_files_path, settings.jtl_files_path, settings.reports_path]:
                usage = psutil.disk_usage(str(path))
                usage_percent = (usage.used / usage.total) * 100
                DISK_USAGE_PERCENT.labels(path=str(path)).set(usage_percent)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    @staticmethod
    def collect_task_metrics():
        """Collect task metrics."""
        try:
            from database import Task, TaskStatus
            
            db = SessionLocal()
            active_count = db.query(Task).filter(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            ).count()
            ACTIVE_TASKS.set(active_count)
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to collect task metrics: {e}")
    
    @classmethod
    def collect_all_metrics(cls):
        """Collect all metrics."""
        cls.collect_system_metrics()
        cls.collect_task_metrics()


def get_prometheus_metrics() -> str:
    """Get Prometheus metrics in text format."""
    MetricsCollector.collect_all_metrics()
    return generate_latest().decode('utf-8')