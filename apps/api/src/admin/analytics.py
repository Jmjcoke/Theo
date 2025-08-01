"""
Admin Analytics Module for Theo
Provides metrics collection and calculation for admin dashboard.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from databases import Database
from src.core.config import settings

logger = logging.getLogger(__name__)


class DashboardAnalytics:
    """
    Analytics class for collecting and calculating dashboard metrics.
    Provides methods to query database for user, document, and system statistics.
    """
    
    def __init__(self, database: Optional[Database] = None):
        """Initialize analytics with database connection."""
        self.database = database or Database(settings.database_url)
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Collect all dashboard metrics from database.
        
        Returns:
            Dict containing user, document, and system metrics
        """
        try:
            logger.info("Starting dashboard metrics collection")
            
            # Get all metrics in parallel for better performance
            user_metrics = await self._get_user_metrics()
            document_metrics = await self._get_document_metrics()
            system_metrics = await self._get_system_metrics()
            
            result = {
                "users": user_metrics,
                "documents": document_metrics,
                "system": system_metrics,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Dashboard metrics collected successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to collect dashboard metrics: {str(e)}")
            raise Exception(f"Analytics collection failed: {str(e)}")
    
    async def _get_user_metrics(self) -> Dict[str, int]:
        """
        Get user statistics from the database.
        
        Returns:
            Dict with total, pending, and approved user counts
        """
        try:
            # Total users count
            total_query = "SELECT COUNT(*) as count FROM users"
            total_result = await self.database.fetch_one(total_query)
            total_users = total_result["count"] if total_result else 0
            
            # Pending users count
            pending_query = "SELECT COUNT(*) as count FROM users WHERE status = 'pending'"
            pending_result = await self.database.fetch_one(pending_query)
            pending_users = pending_result["count"] if pending_result else 0
            
            # Approved users count
            approved_query = "SELECT COUNT(*) as count FROM users WHERE status = 'approved'"
            approved_result = await self.database.fetch_one(approved_query)
            approved_users = approved_result["count"] if approved_result else 0
            
            return {
                "total": total_users,
                "pending": pending_users,
                "approved": approved_users
            }
            
        except Exception as e:
            logger.error(f"Failed to get user metrics: {str(e)}")
            raise Exception(f"User metrics collection failed: {str(e)}")
    
    async def _get_document_metrics(self) -> Dict[str, int]:
        """
        Get document processing statistics from the database.
        
        Returns:
            Dict with total, processing, completed, and failed document counts
        """
        try:
            # Total documents count
            total_query = "SELECT COUNT(*) as count FROM documents"
            total_result = await self.database.fetch_one(total_query)
            total_documents = total_result["count"] if total_result else 0
            
            # Processing documents count
            processing_query = "SELECT COUNT(*) as count FROM documents WHERE processing_status = 'processing'"
            processing_result = await self.database.fetch_one(processing_query)
            processing_documents = processing_result["count"] if processing_result else 0
            
            # Completed documents count
            completed_query = "SELECT COUNT(*) as count FROM documents WHERE processing_status = 'completed'"
            completed_result = await self.database.fetch_one(completed_query)
            completed_documents = completed_result["count"] if completed_result else 0
            
            # Failed documents count
            failed_query = "SELECT COUNT(*) as count FROM documents WHERE processing_status = 'failed'"
            failed_result = await self.database.fetch_one(failed_query)
            failed_documents = failed_result["count"] if failed_result else 0
            
            return {
                "total": total_documents,
                "processing": processing_documents,
                "completed": completed_documents,
                "failed": failed_documents
            }
            
        except Exception as e:
            logger.error(f"Failed to get document metrics: {str(e)}")
            raise Exception(f"Document metrics collection failed: {str(e)}")
    
    async def _get_system_metrics(self) -> Dict[str, str]:
        """
        Get system status and configuration information.
        
        Returns:
            Dict with system uptime, version, and backup information
        """
        try:
            # For now, return static/calculated system information
            # In production, these could be retrieved from system monitoring tools
            
            # Calculate uptime (this is simplified - in production you'd track actual server start time)
            # For MVP, we'll use a placeholder value
            uptime = "operational"
            
            # Version from settings or environment
            version = getattr(settings, 'app_version', '1.0.0')
            
            # Last backup timestamp (placeholder - in production this would be from backup system)
            last_backup = datetime.now(timezone.utc).replace(hour=2, minute=0, second=0, microsecond=0)
            
            return {
                "uptime": uptime,
                "version": version,
                "lastBackup": last_backup.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {str(e)}")
            # Return safe defaults on error
            return {
                "uptime": "unknown",
                "version": "1.0.0",
                "lastBackup": datetime.now(timezone.utc).isoformat()
            }
    
    async def get_user_activity_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get user activity summary for the specified number of days.
        
        Args:
            days: Number of days to look back for activity
            
        Returns:
            Dict with user activity statistics
        """
        try:
            # Users registered in the last N days
            recent_users_query = """
                SELECT COUNT(*) as count 
                FROM users 
                WHERE created_at >= NOW() - INTERVAL '%s days'
            """ % days
            
            recent_result = await self.database.fetch_one(recent_users_query)
            recent_registrations = recent_result["count"] if recent_result else 0
            
            return {
                "recent_registrations": recent_registrations,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {str(e)}")
            return {
                "recent_registrations": 0,
                "period_days": days
            }
    
    async def get_document_processing_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get document processing summary for the specified number of days.
        
        Args:
            days: Number of days to look back for processing activity
            
        Returns:
            Dict with document processing statistics
        """
        try:
            # Documents uploaded in the last N days
            recent_uploads_query = """
                SELECT COUNT(*) as count 
                FROM documents 
                WHERE created_at >= NOW() - INTERVAL '%s days'
            """ % days
            
            recent_result = await self.database.fetch_one(recent_uploads_query)
            recent_uploads = recent_result["count"] if recent_result else 0
            
            # Documents completed in the last N days
            recent_completed_query = """
                SELECT COUNT(*) as count 
                FROM documents 
                WHERE processing_status = 'completed' 
                AND updated_at >= NOW() - INTERVAL '%s days'
            """ % days
            
            completed_result = await self.database.fetch_one(recent_completed_query)
            recent_completed = completed_result["count"] if completed_result else 0
            
            return {
                "recent_uploads": recent_uploads,
                "recent_completed": recent_completed,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get document processing summary: {str(e)}")
            return {
                "recent_uploads": 0,
                "recent_completed": 0,
                "period_days": days
            }


async def create_analytics_instance(database: Optional[Database] = None) -> DashboardAnalytics:
    """
    Factory function to create DashboardAnalytics instance.
    
    Args:
        database: Optional Database connection
        
    Returns:
        Configured DashboardAnalytics instance
    """
    return DashboardAnalytics(database=database)