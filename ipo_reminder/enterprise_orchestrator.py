"""Enterprise-grade IPO reminder orchestrator with all advanced features."""
import logging
import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import json

from .config import (
    SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL,
    DATABASE_URL, REDIS_URL, BSE_API_KEY, NSE_API_KEY
)
from .database import DatabaseManager, IPOData, IPORecommendation
from .cache import CacheManager
from .official_apis import BSEAPIClient, NSEAPIClient
from .monitoring import monitoring_system, record_metric, increment_counter
from .compliance import compliance_logger, log_system_startup, log_system_shutdown
from .emailer import Emailer
from .ipo_categorizer import IPOCategorizer
from .investment_advisor import InvestmentAdvisor
from .deep_analyzer import DeepAnalyzer
from .sources.zerodha import ZerodhaScraper
from .sources.moneycontrol import MoneycontrolScraper
from .sources.chittorgarh import ChittorgarhScraper
from .sources.fallback import FallbackScraper

logger = logging.getLogger(__name__)

class EnterpriseIPOOrchestrator:
    """Enterprise-grade IPO reminder orchestrator."""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.cache_manager = CacheManager()
        self.bse_client = BSEAPIClient(api_key=BSE_API_KEY)
        self.nse_client = NSEAPIClient(api_key=NSE_API_KEY)
        self.emailer = Emailer()
        self.categorizer = IPOCategorizer()
        self.advisor = InvestmentAdvisor()
        self.analyzer = DeepAnalyzer()

        # Scrapers for fallback
        self.scrapers = {
            'zerodha': ZerodhaScraper(),
            'moneycontrol': MoneycontrolScraper(),
            'chittorgarh': ChittorgarhScraper(),
            'fallback': FallbackScraper()
        }

        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_running = False
        self.last_run = None

    async def initialize(self):
        """Initialize all enterprise components."""
        try:
            logger.info("Initializing enterprise IPO orchestrator...")

            # Initialize database
            await self.db_manager.initialize()

            # Initialize cache
            await self.cache_manager.initialize()

            # Initialize official API clients
            await self.bse_client.initialize()
            await self.nse_client.initialize()

            # Start monitoring
            monitoring_system.start_monitoring()

            # Log system startup
            log_system_startup({
                'components': ['database', 'cache', 'bse_api', 'nse_api', 'monitoring'],
                'version': 'enterprise-v1.0'
            })

            record_metric('system_initialization', 1.0, {'status': 'success'})
            logger.info("Enterprise orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enterprise orchestrator: {e}")
            record_metric('system_initialization', 0.0, {'status': 'failure', 'error': str(e)})
            raise

    async def shutdown(self):
        """Shutdown all enterprise components gracefully."""
        try:
            logger.info("Shutting down enterprise IPO orchestrator...")

            # Stop monitoring
            monitoring_system.stop_monitoring()

            # Shutdown API clients
            await self.bse_client.shutdown()
            await self.nse_client.shutdown()

            # Shutdown cache
            await self.cache_manager.shutdown()

            # Shutdown database
            await self.db_manager.shutdown()

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            # Log system shutdown
            log_system_shutdown({
                'shutdown_reason': 'normal',
                'uptime_seconds': getattr(monitoring_system, '_start_time', 0)
            })

            logger.info("Enterprise orchestrator shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def fetch_ipo_data_enterprise(self) -> List[Dict[str, Any]]:
        """Fetch IPO data using enterprise-grade approach."""
        start_time = datetime.utcnow()
        record_metric('ipo_fetch_start', 1.0)

        try:
            # Try official APIs first
            ipo_data = []

            # Fetch from BSE
            try:
                bse_data = await self.bse_client.get_upcoming_ipos()
                ipo_data.extend(bse_data)
                record_metric('bse_api_calls', 1.0, {'status': 'success'})
                compliance_logger.log_api_call('bse', 'upcoming_ipos', 'SUCCESS',
                                             {'record_count': len(bse_data)})
            except Exception as e:
                logger.warning(f"BSE API failed: {e}")
                record_metric('bse_api_calls', 1.0, {'status': 'failure', 'error': str(e)})
                compliance_logger.log_api_call('bse', 'upcoming_ipos', 'FAILURE',
                                             {'error': str(e)})

            # Fetch from NSE
            try:
                nse_data = await self.nse_client.get_upcoming_ipos()
                ipo_data.extend(nse_data)
                record_metric('nse_api_calls', 1.0, {'status': 'success'})
                compliance_logger.log_api_call('nse', 'upcoming_ipos', 'SUCCESS',
                                             {'record_count': len(nse_data)})
            except Exception as e:
                logger.warning(f"NSE API failed: {e}")
                record_metric('nse_api_calls', 1.0, {'status': 'failure', 'error': str(e)})
                compliance_logger.log_api_call('nse', 'upcoming_ipos', 'FAILURE',
                                             {'error': str(e)})

            # If official APIs fail, use web scraping as fallback
            if not ipo_data:
                logger.info("Official APIs failed, falling back to web scraping...")
                ipo_data = await self._fetch_via_scraping()

            # Remove duplicates and validate data
            ipo_data = self._deduplicate_and_validate(ipo_data)

            # Cache the results
            await self.cache_manager.set('latest_ipo_data', ipo_data, ttl=3600)  # 1 hour

            # Store in database
            await self._store_ipo_data(ipo_data)

            duration = (datetime.utcnow() - start_time).total_seconds()
            record_metric('ipo_fetch_duration', duration)
            record_metric('ipo_fetch_success', 1.0, {'count': len(ipo_data)})

            compliance_logger.log_ipo_data_fetch('enterprise', len(ipo_data), 'SUCCESS',
                                               {'duration_seconds': duration, 'sources': ['bse', 'nse', 'scraping']})

            return ipo_data

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            record_metric('ipo_fetch_duration', duration)
            record_metric('ipo_fetch_failure', 1.0, {'error': str(e)})

            compliance_logger.log_ipo_data_fetch('enterprise', 0, 'FAILURE',
                                               {'error': str(e), 'duration_seconds': duration})

            logger.error(f"Enterprise IPO fetch failed: {e}")
            raise

    async def _fetch_via_scraping(self) -> List[Dict[str, Any]]:
        """Fallback to web scraping if official APIs fail."""
        ipo_data = []

        # Try scrapers in order of preference
        for name, scraper in self.scrapers.items():
            try:
                data = await asyncio.get_event_loop().run_in_executor(
                    self.executor, scraper.get_upcoming_ipos
                )
                ipo_data.extend(data)
                record_metric('scraper_calls', 1.0, {'scraper': name, 'status': 'success'})
            except Exception as e:
                logger.warning(f"Scraper {name} failed: {e}")
                record_metric('scraper_calls', 1.0, {'scraper': name, 'status': 'failure', 'error': str(e)})

        return ipo_data

    def _deduplicate_and_validate(self, ipo_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and validate IPO data."""
        seen = set()
        validated_data = []

        for ipo in ipo_data:
            # Create unique key
            key = f"{ipo.get('company_name', '').lower()}_{ipo.get('ipo_open_date', '')}"

            if key not in seen and self._validate_ipo_data(ipo):
                seen.add(key)
                validated_data.append(ipo)

        return validated_data

    def _validate_ipo_data(self, ipo: Dict[str, Any]) -> bool:
        """Validate IPO data structure."""
        required_fields = ['company_name', 'ipo_open_date', 'ipo_close_date']

        for field in required_fields:
            if not ipo.get(field):
                return False

        # Validate dates
        try:
            open_date = datetime.fromisoformat(ipo['ipo_open_date'].replace('Z', '+00:00'))
            close_date = datetime.fromisoformat(ipo['ipo_close_date'].replace('Z', '+00:00'))

            if close_date <= open_date:
                return False

        except (ValueError, AttributeError):
            return False

        return True

    async def _store_ipo_data(self, ipo_data: List[Dict[str, Any]]):
        """Store IPO data in database."""
        try:
            with self.db_manager.get_session() as session:
                for ipo in ipo_data:
                    # Check if already exists
                    existing = session.query(IPOData).filter_by(
                        company_name=ipo['company_name'],
                        ipo_open_date=datetime.fromisoformat(ipo['ipo_open_date'].replace('Z', '+00:00'))
                    ).first()

                    if not existing:
                        db_ipo = IPOData(
                            company_name=ipo['company_name'],
                            ipo_open_date=datetime.fromisoformat(ipo['ipo_open_date'].replace('Z', '+00:00')),
                            ipo_close_date=datetime.fromisoformat(ipo['ipo_close_date'].replace('Z', '+00:00')),
                            price_range=ipo.get('price_range'),
                            lot_size=ipo.get('lot_size'),
                            platform=ipo.get('platform', 'Unknown'),
                            sector=ipo.get('sector'),
                            raw_data=json.dumps(ipo)
                        )
                        session.add(db_ipo)

                session.commit()

        except Exception as e:
            logger.error(f"Failed to store IPO data: {e}")
            raise

    async def analyze_and_categorize_ipos(self, ipo_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze and categorize IPOs with enterprise features."""
        analyzed_ipos = []

        for ipo in ipo_data:
            try:
                # Get cached analysis if available
                cache_key = f"analysis_{ipo['company_name']}_{ipo['ipo_open_date']}"
                cached_analysis = await self.cache_manager.get(cache_key)

                if cached_analysis:
                    analyzed_ipos.append(cached_analysis)
                    continue

                # Perform comprehensive analysis
                analysis = await self._perform_comprehensive_analysis(ipo)

                # Cache the analysis
                await self.cache_manager.set(cache_key, analysis, ttl=1800)  # 30 minutes

                analyzed_ipos.append(analysis)

            except Exception as e:
                logger.error(f"Failed to analyze IPO {ipo.get('company_name')}: {e}")
                # Add basic analysis on failure
                analyzed_ipos.append({
                    **ipo,
                    'risk_score': 5.0,
                    'recommendation': 'HOLD',
                    'analysis': 'Analysis failed - please check manually'
                })

        return analyzed_ipos

    async def _perform_comprehensive_analysis(self, ipo: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive IPO analysis."""
        # Run analysis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        # Deep analysis
        deep_analysis = await loop.run_in_executor(
            self.executor, self.analyzer.analyze_ipo, ipo
        )

        # Investment recommendation
        recommendation = await loop.run_in_executor(
            self.executor, self.advisor.get_recommendation, ipo
        )

        # Categorization
        category = await loop.run_in_executor(
            self.executor, self.categorizer.categorize_ipo, ipo
        )

        return {
            **ipo,
            'deep_analysis': deep_analysis,
            'recommendation': recommendation,
            'category': category,
            'analyzed_at': datetime.utcnow().isoformat()
        }

    async def send_enterprise_notifications(self, analyzed_ipos: List[Dict[str, Any]]):
        """Send enterprise-grade notifications."""
        if not analyzed_ipos:
            logger.info("No IPOs to notify about")
            return

        try:
            # Generate comprehensive email content
            email_content = await self._generate_enterprise_email_content(analyzed_ipos)

            # Send email
            success = await self.emailer.send_email(
                subject=f"IPO Reminder • {datetime.now().strftime('%B %d, %Y')}",
                content=email_content,
                recipient=RECIPIENT_EMAIL
            )

            if success:
                record_metric('emails_sent', 1.0)
                increment_counter('email_notifications')
                compliance_logger.log_email_send(
                    RECIPIENT_EMAIL,
                    f"IPO Reminder • {datetime.now().strftime('%B %d, %Y')}",
                    'SUCCESS',
                    {'ipo_count': len(analyzed_ipos)}
                )
            else:
                record_metric('emails_failed', 1.0)
                compliance_logger.log_email_send(
                    RECIPIENT_EMAIL,
                    f"IPO Reminder • {datetime.now().strftime('%B %d, %Y')}",
                    'FAILURE',
                    {'ipo_count': len(analyzed_ipos)}
                )

        except Exception as e:
            logger.error(f"Failed to send enterprise notifications: {e}")
            record_metric('email_send_errors', 1.0, {'error': str(e)})
            compliance_logger.log_error('email_send', str(e), {'ipo_count': len(analyzed_ipos)})

    async def _generate_enterprise_email_content(self, analyzed_ipos: List[Dict[str, Any]]) -> str:
        """Generate comprehensive enterprise email content."""
        content_parts = []

        # Header
        content_parts.append(f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px;">
        IPO Reminder - {datetime.now().strftime('%B %d, %Y')}
    </h2>
""")

        # Summary statistics
        total_ipos = len(analyzed_ipos)
        mainboard_count = sum(1 for ipo in analyzed_ipos if ipo.get('platform') == 'Mainboard')
        sme_count = sum(1 for ipo in analyzed_ipos if ipo.get('platform') == 'SME')

        content_parts.append(f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #495057;">IPO Summary</h3>
        <p><strong>Total IPOs:</strong> {total_ipos}</p>
        <p><strong>Mainboard IPOs:</strong> {mainboard_count}</p>
        <p><strong>SME IPOs:</strong> {sme_count}</p>
    </div>
""")

        # IPO details
        for ipo in analyzed_ipos:
            platform = ipo.get('platform', 'Unknown')
            platform_color = '#28a745' if platform == 'Mainboard' else '#007bff'

            content_parts.append(f"""
    <div style="border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 15px 0;">
        <h3 style="margin-top: 0; color: #333;">{ipo['company_name']}</h3>
        <p style="background-color: {platform_color}; color: white; padding: 5px 10px; border-radius: 3px; display: inline-block; font-size: 12px; font-weight: bold;">
            {platform} IPO
        </p>

        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Open Date:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{ipo['ipo_open_date']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Close Date:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{ipo['ipo_close_date']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Price Range:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{ipo.get('price_range', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Lot Size:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{ipo.get('lot_size', 'N/A')}</td>
            </tr>
        </table>

        <div style="background-color: #fff3cd; padding: 10px; border-radius: 3px; margin: 10px 0;">
            <strong>Recommendation:</strong> {ipo.get('recommendation', 'N/A')}<br>
            <strong>Risk Score:</strong> {ipo.get('deep_analysis', {}).get('risk_score', 'N/A')}/10
        </div>

        <p style="font-size: 14px; color: #666;">
            {ipo.get('deep_analysis', {}).get('summary', 'Analysis not available')}
        </p>
    </div>
""")

        # Footer
        content_parts.append("""
    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #666; font-size: 12px;">
        <p>This is an automated notification from the Enterprise IPO Reminder System.</p>
        <p>For questions or concerns, please check the system logs.</p>
    </div>
</div>
""")

        return ''.join(content_parts)

    async def run_enterprise_cycle(self):
        """Run one complete enterprise IPO monitoring cycle."""
        try:
            logger.info("Starting enterprise IPO monitoring cycle...")

            # Fetch IPO data
            ipo_data = await self.fetch_ipo_data_enterprise()

            if not ipo_data:
                logger.info("No IPO data found")
                return

            # Analyze and categorize
            analyzed_ipos = await self.analyze_and_categorize_ipos(ipo_data)

            # Send notifications
            await self.send_enterprise_notifications(analyzed_ipos)

            self.last_run = datetime.utcnow()
            record_metric('cycle_completed', 1.0)

            logger.info(f"Enterprise cycle completed successfully. Processed {len(analyzed_ipos)} IPOs")

        except Exception as e:
            logger.error(f"Enterprise cycle failed: {e}")
            record_metric('cycle_failed', 1.0, {'error': str(e)})
            compliance_logger.log_error('enterprise_cycle', str(e))

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get health status from monitoring
            health = monitoring_system.get_health_status()

            # Get cache stats
            cache_stats = await self.cache_manager.get_stats()

            # Get database stats
            db_stats = await self.db_manager.get_stats()

            # Get API client status
            bse_status = await self.bse_client.get_status()
            nse_status = await self.nse_client.get_status()

            return {
                'timestamp': datetime.utcnow().isoformat(),
                'health': health,
                'cache': cache_stats,
                'database': db_stats,
                'api_clients': {
                    'bse': bse_status,
                    'nse': nse_status
                },
                'last_run': self.last_run.isoformat() if self.last_run else None,
                'is_running': self.is_running
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}

    def start_enterprise_service(self):
        """Start the enterprise service with proper signal handling."""
        async def main():
            await self.initialize()
            self.is_running = True

            # Set up signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.shutdown())
                self.is_running = False

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            logger.info("Enterprise IPO service started. Press Ctrl+C to stop.")

            # Run initial cycle
            await self.run_enterprise_cycle()

            # Keep running until stopped
            while self.is_running:
                # Wait for next cycle (daily)
                await asyncio.sleep(86400)  # 24 hours

                if self.is_running:  # Check if still running after sleep
                    await self.run_enterprise_cycle()

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Service failed: {e}")
        finally:
            if self.is_running:
                asyncio.run(self.shutdown())

# Global orchestrator instance
enterprise_orchestrator = EnterpriseIPOOrchestrator()

if __name__ == "__main__":
    enterprise_orchestrator.start_enterprise_service()
