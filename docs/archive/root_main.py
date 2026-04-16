#!/usr/bin/env python3
"""
ReconX-Elite - Agentic Multi-Model Vulnerability Research Engine
Main entry point with antigravity autonomous flow
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv

# Import all phase modules
from backend.recon_pipeline import ReconPipeline
from backend.context_tree import ContextTree
from backend.ai_router import AIRouter
from backend.predictive_sandbox import PredictiveSandbox
from backend.reporting.professional_reporter import ProfessionalReporter
from backend.tool_runner import ToolRunner
from backend.websocket_manager import WebSocketManager

# Import vulnerability modules
from backend.vulnerability_modules.bac_idor import BACIDORModule
from backend.vulnerability_modules.injection import InjectionModule
from backend.vulnerability_modules.ssrf_misconfig import SSRFMisconfigModule
from backend.vulnerability_modules.xss_bypass import XSSBypassModule
from backend.vulnerability_modules.auth_session import AuthSessionModule
from backend.vulnerability_modules.business_logic import BusinessLogicModule

# Import session management
from backend.session_manifest import SessionManifest

# Import Phase 7 and Phase 8 modules
from backend.exploit_chainer import ExploitChainer
from backend.semantic_fuzzer import SemanticFuzzer
from backend.waf_analyzer import WAFAnalyzer
from backend.agent_browser import AgenticBrowser

# Import monitoring and refinement modules
from backend.watchdog import Watchdog, MonitoringConfig
from backend.refinement import Refinement

# Import Master Edition modules
from backend.mass_scan import MassScanner
from backend.notifications import NotificationHub

# Load and validate environment variables
load_dotenv(override=False)

# Required environment variables
REQUIRED_ENV_VARS = [
    'POSTGRES_DB',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
]

def validate_environment() -> None:
    """Validate that required environment variables are set"""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please set them in .env file or as environment variables."
        )

# Configure logging
def setup_logging() -> logging.Logger:
    """Configure logging with environment-based log level"""
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        log_level = logging.INFO
        print(f"Invalid LOG_LEVEL '{log_level_str}', using INFO", file=sys.stderr)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('reconx_elite.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

class ReconXEliteEngine:
    """Main autonomous vulnerability research engine"""
    
    def __init__(self, target: str, session_tokens: Dict[str, str] = None):
        self.target = target
        self.session_tokens = session_tokens or {}
        self.session_id = str(uuid.uuid4())
        
        # Initialize core components
        self.ai_router = AIRouter()
        self.tool_runner = ToolRunner()
        self.ws_manager = WebSocketManager()
        self.session_manifest = SessionManifest(self.session_id)
        
        # Initialize phase modules
        self.recon_pipeline = ReconPipeline(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.context_tree = ContextTree(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.predictive_sandbox = PredictiveSandbox(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.professional_reporter = ProfessionalReporter(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        
        # Initialize Phase 7 and Phase 8 modules
        self.exploit_chainer = ExploitChainer(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.semantic_fuzzer = SemanticFuzzer(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.waf_analyzer = WAFAnalyzer(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.agent_browser = AgenticBrowser(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        
        # Initialize vulnerability modules
        self.vulnerability_modules = {
            'bac_idor': BACIDORModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager, self.session_tokens
            ),
            'injection': InjectionModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
            ),
            'ssrf_misconfig': SSRFMisconfigModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
            ),
            'xss_bypass': XSSBypassModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
            ),
            'auth_session': AuthSessionModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager, self.session_tokens
            ),
            'business_logic': BusinessLogicModule(
                self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager, self.session_tokens
            )
        }
        
        # Results storage
        self.scan_results = {}
        self.final_report = None
        
        # Initialize monitoring and refinement modules
        self.watchdog = Watchdog(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        self.refinement = Refinement(
            self.session_id, target, self.ai_router, self.tool_runner, self.ws_manager
        )
        
        # Initialize Master Edition modules
        self.notification_hub = NotificationHub(self.session_id)
        self.mass_scanner = MassScanner(
            self.session_id, self.ai_router, self.tool_runner, self.ws_manager
        )
        
    async def execute_autonomous_flow(self) -> Dict[str, Any]:
        """Execute the complete autonomous vulnerability research flow"""
        logger.info(f"Starting ReconX-Elite autonomous flow for {self.target}")
        logger.info(f"Session ID: {self.session_id}")
        
        try:
            # Initialize session manifest
            await self.session_manifest.initialize_session(self.target, self.session_tokens)
            
            # Phase 8: Pre-Scan Stealth Check & Browser Authentication
            logger.info("=== PHASE 8: PRE-SCAN STEALTH CHECK & BROWSER AUTHENTICATION ===")
            
            # WAF warm-up and stealth configuration
            waf_results = await self.waf_analyzer.execute()
            self.scan_results['waf_analysis'] = waf_results
            
            # Agentic browser for authentication and SPA analysis
            browser_results = await self.agent_browser.execute(self.session_tokens)
            self.scan_results['agent_browser'] = browser_results
            
            # Update session tokens from browser if authenticated
            if browser_results.get('browser_session', {}).get('is_authenticated', False):
                await self._update_session_tokens_from_browser(browser_results)
            
            # Semantic fuzzing for contextual wordlists
            semantic_results = await self.semantic_fuzzer.execute(context_tree_results={})  # Will be updated after Phase 2
            self.scan_results['semantic_fuzzer'] = semantic_results
            
            # Phase 1: Enhanced Reconnaissance Engine
            logger.info("=== PHASE 1: ENHANCED RECONNAISSANCE ENGINE ===")
            recon_results = await self.recon_pipeline.execute()
            self.scan_results['reconnaissance'] = recon_results
            
            # Phase 2: Technology Profiler & Context Tree
            logger.info("=== PHASE 2: TECHNOLOGY PROFILER & CONTEXT TREE ===")
            context_tree_results = await self.context_tree.build_context_tree(recon_results)
            self.scan_results['context_tree'] = context_tree_results
            
            # Phase 3: AI Tactical Commander (Model Router)
            logger.info("=== PHASE 3: AI TACTICAL COMMANDER ===")
            # AI routing is integrated into all modules, no separate execution needed
            
            # Phase 4: The Big 7 Vulnerability Modules
            logger.info("=== PHASE 4: THE BIG 7 VULNERABILITY MODULES ===")
            vulnerability_results = await self._execute_vulnerability_modules(context_tree_results)
            self.scan_results['vulnerability_modules'] = vulnerability_results
            
            # Phase 5: Predictive Sandbox & Execution
            logger.info("=== PHASE 5: PREDICTIVE SANDBOX & EXECUTION ===")
            sandbox_results = await self.predictive_sandbox.execute(vulnerability_results)
            self.scan_results['predictive_sandbox'] = sandbox_results
            
            # Phase 7: Tactical Chain Analysis
            logger.info("=== PHASE 7: TACTICAL CHAIN ANALYSIS ===")
            chain_results = await self.exploit_chainer.execute(self.scan_results)
            self.scan_results['exploit_chainer'] = chain_results
            
            # Re-run semantic fuzzing with enhanced context tree
            logger.info("=== PHASE 8: ENHANCED SEMANTIC FUZZING ===")
            enhanced_semantic_results = await self.semantic_fuzzer.execute(context_tree_results)
            self.scan_results['enhanced_semantic_fuzzer'] = enhanced_semantic_results
            
            # Phase 6: Professional Reporting & PoC
            logger.info("=== PHASE 6: PROFESSIONAL REPORTING & POC ===")
            reporting_results = await self.professional_reporter.execute(self.scan_results)
            self.final_report = reporting_results
            self.scan_results['reporting'] = reporting_results
            
            # Phase 9: Learning Feedback & Refinement
            logger.info("=== PHASE 9: LEARNING FEEDBACK & REFINEMENT ===")
            refinement_results = await self.refinement.execute()
            self.scan_results['refinement'] = refinement_results
            
            # Finalize session
            await self.session_manifest.finalize_session(self.scan_results)
            
            logger.info("=== RECONX-ELITE AUTONOMOUS FLOW COMPLETED ===")
            
            return self.scan_results
            
        except Exception as e:
            logger.error(f"Autonomous flow execution failed: {e}")
            await self.ws_manager.send_log(
                self.session_id, 'error', f'Autonomous flow failed: {str(e)}', phase='error'
            )
            raise
    
    async def _execute_vulnerability_modules(self, context_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all Big 7 vulnerability modules"""
        vulnerability_results = {}
        
        # Execute modules in parallel where possible
        module_tasks = []
        module_names = []
        
        for module_name, module in self.vulnerability_modules.items():
            module_tasks.append(module.execute(context_tree))
            module_names.append(module_name)
        
        # Run modules concurrently
        try:
            results = await asyncio.gather(*module_tasks, return_exceptions=True)
            
            failed_count = 0
            for i, result in enumerate(results):
                module_name = module_names[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Module {module_name} failed: {result}")
                    vulnerability_results[module_name] = {'error': str(result)}
                    failed_count += 1
                else:
                    vulnerability_results[module_name] = result
                    logger.info(f"Module {module_name} completed successfully")
                    
                    # Check for critical findings and send notifications
                    await self._check_and_notify_critical_findings(module_name, result)
            
            # If all modules failed, raise an error
            if failed_count == len(module_names):
                raise RuntimeError("All vulnerability modules failed to execute")
        
        except Exception as e:
            logger.error(f"Failed to execute vulnerability modules: {e}")
            raise
        
        return vulnerability_results
    
    async def _update_session_tokens_from_browser(self, browser_results: Dict[str, Any]) -> None:
        """Update session tokens from browser authentication results"""
        try:
            browser_session = browser_results.get('browser_session', {})
            
            if not isinstance(browser_session, dict):
                logger.warning("Invalid browser_session format, skipping token update")
                return
            
            # Extract cookies as session tokens
            cookies = browser_session.get('cookies', [])
            if not isinstance(cookies, list):
                logger.warning(f"Invalid cookies format (expected list, got {type(cookies).__name__})")
                cookies = []
            
            for cookie in cookies:
                if isinstance(cookie, dict):
                    cookie_name = cookie.get('name', '')
                    if cookie_name in ['sessionid', 'session', 'auth', 'token']:
                        self.session_tokens[f"cookie_{cookie_name}"] = cookie.get('value', '')
            
            # Extract access tokens
            access_tokens = browser_session.get('access_tokens', {})
            if isinstance(access_tokens, dict):
                for token_type, token_value in access_tokens.items():
                    if token_value and isinstance(token_value, str):
                        self.session_tokens[f"{token_type}_token"] = token_value
            
            # Extract authorization headers
            headers = browser_session.get('headers', {})
            if isinstance(headers, dict):
                auth_header = headers.get('Authorization', '')
                if auth_header and isinstance(auth_header, str):
                    self.session_tokens['auth_header'] = auth_header
            
            logger.info(f"Updated session tokens from browser authentication: {len(self.session_tokens)} tokens")
            
        except Exception as e:
            logger.error(f"Failed to update session tokens from browser: {e}")
    
    async def _check_and_notify_critical_findings(self, module_name: str, result: Dict[str, Any]) -> None:
        """Check for critical findings and send notifications"""
        try:
            findings = result.get('findings', []) or result.get('results', [])
            
            if not isinstance(findings, list):
                logger.warning(f"Invalid findings format for module {module_name}")
                return
            
            for finding in findings:
                if isinstance(finding, dict):
                    severity = finding.get('severity', '').lower()
                    
                    # Notify for critical vulnerabilities
                    if severity in ['critical', 'p1']:
                        await self.notification_hub.notify_critical_vulnerability(
                            vulnerability_id=finding.get('id', 'unknown'),
                            severity=severity.upper(),
                            endpoint=finding.get('endpoint', 'unknown'),
                            description=finding.get('description', 'No description available')
                        )
                    
                    # Notify for valid PoC generation
                    if finding.get('poc_generated', False):
                        await self.notification_hub.notify_valid_poc(
                            vulnerability_id=finding.get('id', 'unknown'),
                            severity=severity.upper(),
                            endpoint=finding.get('endpoint', 'unknown'),
                            payload=finding.get('payload', 'No payload available')
                        )
        
        except Exception as e:
            logger.error(f"Failed to check and notify critical findings: {e}")
    
    async def execute_mass_scan(self, template_paths: List[str], domain_filter: Optional[str] = None) -> Dict[str, Any]:
        """Execute mass scan with notifications"""
        logger.info(f"Starting mass scan with {len(template_paths)} templates")
        
        try:
            # Execute mass scan
            scan_results = await self.mass_scanner.execute(template_paths, domain_filter)
            
            # Send completion notification
            scan_info = scan_results.get('scan_info', {})
            await self.notification_hub.notify_mass_scan_completed(
                targets_count=scan_info.get('targets_count', 0),
                templates_count=scan_info.get('valid_templates_count', 0),
                total_findings=scan_info.get('total_findings', 0),
                duration="Unknown"  # TODO: Calculate actual duration
            )
            
            return scan_results
        
        except Exception as e:
            logger.error(f"Mass scan failed: {e}")
            # Send error notification
            await self.notification_hub.notify_monitoring_error(
                error_message=str(e),
                target=self.target,
                error_type="mass_scan_failure"
            )
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        if not self.scan_results:
            return {'status': 'not_executed'}
        
        # Count total vulnerabilities
        total_vulnerabilities = 0
        critical_count = 0
        high_count = 0
        
        # Count from vulnerability modules
        vuln_modules = self.scan_results.get('vulnerability_modules', {})
        for module_name, module_results in vuln_modules.items():
            if isinstance(module_results, dict):
                findings = module_results.get('findings', []) or module_results.get('results', [])
                if isinstance(findings, list):
                    total_vulnerabilities += len(findings)
                    
                    # Count critical and high severity
                    for finding in findings:
                        if isinstance(finding, dict):
                            severity = finding.get('severity', '').lower()
                            if severity == 'critical':
                                critical_count += 1
                            elif severity == 'high':
                                high_count += 1
        
        # Add sandbox results
        sandbox_results = self.scan_results.get('predictive_sandbox', {})
        sandbox_tests = sandbox_results.get('sandbox_tests', {}).get('results', [])
        if isinstance(sandbox_tests, list):
            successful_tests = [t for t in sandbox_tests if isinstance(t, dict) and t.get('test_result', '').startswith('success')]
            total_vulnerabilities += len(successful_tests)
        
        # Add exploit chain results
        chain_results = self.scan_results.get('exploit_chainer', {})
        attack_chains = chain_results.get('attack_chains', {}).get('results', [])
        if isinstance(attack_chains, list):
            total_vulnerabilities += len(attack_chains)
        
        return {
            'status': 'completed',
            'session_id': self.session_id,
            'target': self.target,
            'total_vulnerabilities': total_vulnerabilities,
            'critical_count': critical_count,
            'high_count': high_count,
            'scan_duration': self._calculate_scan_duration(),
            'report_generated': bool(self.final_report)
        }
    
    def _calculate_scan_duration(self) -> str:
        """Calculate scan duration"""
        if not self.session_manifest.session_data:
            return "unknown"
        
        start_time = self.session_manifest.session_data.get('start_time')
        end_time = self.session_manifest.session_data.get('end_time')
        
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(start_time)
                end = datetime.fromisoformat(end_time)
                duration = end - start
                
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                if hours > 0:
                    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
                elif minutes > 0:
                    return f"{int(minutes)}m {int(seconds)}s"
                else:
                    return f"{int(seconds)}s"
            except Exception as e:
                logger.error(f"Failed to calculate scan duration: {e}")
        
        return "unknown"

def parse_session_tokens(args: List[str]) -> Dict[str, str]:
    """Parse session tokens from command line arguments
    
    Args:
        args: Command line arguments (options already parsed)
    
    Returns:
        Dictionary of session tokens
    """
    session_tokens = {}
    for i, token in enumerate(args):
        session_tokens[f'session_{i}'] = token
    return session_tokens

async def main():
    """Main entry point"""
    # Validate environment
    try:
        validate_environment()
    except EnvironmentError as e:
        print(f"Environment validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python main.py <target> [options] [session_tokens...]")
        print("Options:")
        print("  --monitor              Enable continuous monitoring mode")
        print("  --interval <minutes>   Set monitoring interval (default: 60)")
        print("  --delta-only           Only scan changed assets in monitor mode")
        print("  --mass-scan <templates> Run mass scan with Nuclei templates")
        print("  --domain-filter <domain> Filter domains for mass scan")
        print("Example: python main.py example.com")
        print("Example: python main.py example.com --monitor --interval 30")
        print("Example: python main.py example.com --mass-scan templates/*.yaml")
        print("Example: python main.py example.com token1 token2 token3")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # Parse command line options
    monitor_mode = False
    monitor_interval = 60
    delta_only = False
    mass_scan_mode = False
    template_paths = []
    domain_filter = None
    session_token_args = []
    
    # Parse options
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--monitor':
            monitor_mode = True
            i += 1
        elif arg == '--interval':
            if i + 1 < len(sys.argv):
                try:
                    monitor_interval = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print("Error: Invalid interval value", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: --interval requires a value", file=sys.stderr)
                sys.exit(1)
        elif arg == '--delta-only':
            delta_only = True
            i += 1
        elif arg == '--mass-scan':
            mass_scan_mode = True
            i += 1
            # Collect template paths until next option
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                template_paths.append(sys.argv[i])
                i += 1
        elif arg == '--domain-filter':
            if i + 1 < len(sys.argv):
                domain_filter = sys.argv[i + 1]
                i += 2
            else:
                print("Error: --domain-filter requires a value", file=sys.stderr)
                sys.exit(1)
        else:
            # Session token - collect all remaining non-option args
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                session_token_args.append(sys.argv[i])
                i += 1
    
    # Parse session tokens flexibly
    session_tokens = parse_session_tokens(session_token_args)
    
    # Validate target
    if not target or '.' not in target:
        print("Error: Invalid target specified", file=sys.stderr)
        sys.exit(1)
    
    print(f"ReconX-Elite - Agentic Multi-Model Vulnerability Research Engine")
    print(f"Target: {target}")
    print(f"Session Tokens: {len(session_tokens)} provided")
    
    # Determine mode
    if mass_scan_mode:
        mode = "Mass Scan"
    elif monitor_mode:
        mode = "Monitoring"
    else:
        mode = "Autonomous Scan"
    
    print(f"Mode: {mode}")
    
    if monitor_mode:
        print(f"Monitor Interval: {monitor_interval} minutes")
        print(f"Delta Only: {delta_only}")
    
    if mass_scan_mode:
        print(f"Template Paths: {len(template_paths)} templates")
        if domain_filter:
            print(f"Domain Filter: {domain_filter}")
    
    print()
    
    # Initialize and execute engine
    engine = ReconXEliteEngine(target, session_tokens)
    
    try:
        if mass_scan_mode:
            # Validate template paths
            if not template_paths:
                print("Error: --mass-scan requires at least one template path", file=sys.stderr)
                sys.exit(1)
            
            print("Starting mass scan...")
            print("Press Ctrl+C to stop scanning")
            print()
            
            # Execute mass scan
            results = await engine.execute_mass_scan(template_paths, domain_filter)
            
        elif monitor_mode:
            # Configure monitoring
            monitoring_config = MonitoringConfig(
                target=target,
                interval_minutes=monitor_interval,
                enable_subdomain_monitoring=True,
                enable_js_monitoring=True,
                enable_ssl_monitoring=True,
                enable_header_monitoring=True,
                enable_tech_monitoring=True,
                auto_execute_delta=not delta_only,
                baseline_retention_days=30
            )
            
            print("Starting continuous monitoring...")
            print("Press Ctrl+C to stop monitoring")
            print()
            
            # Create baseline first if it doesn't exist
            if not engine.watchdog.baseline_file.exists():
                print("Creating initial baseline...")
                baseline_results = await engine.execute_autonomous_flow()
                await engine.watchdog.execute(baseline_results)
                print("Baseline created successfully")
                print()
            
            # Start monitoring
            await engine.watchdog.execute()
        else:
            # Execute autonomous flow
            results = await engine.execute_autonomous_flow()
        
        # Display summary
        summary = engine.get_summary()
        
        print()
        print("=" * 60)
        print("RECONX-ELITE EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Target: {summary['target']}")
        print(f"Session ID: {summary['session_id']}")
        print(f"Status: {summary['status']}")
        print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"Critical: {summary['critical_count']}")
        print(f"High: {summary['high_count']}")
        print(f"Duration: {summary['scan_duration']}")
        print(f"Report Generated: {summary['report_generated']}")
        print()
        
        # Show report location if generated
        if engine.final_report and engine.final_report.get('markdown_report'):
            print("Vulnerability report has been generated and saved.")
            print("Check the 'reports/' directory for detailed findings.")
        
        # Save session manifest
        await engine.session_manifest.save_session()
        
        print()
        print("ReconX-Elite autonomous flow completed successfully!")
        
    except KeyboardInterrupt:
        print("\nExecution interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nExecution failed: {e}", file=sys.stderr)
        logger.error(f"Main execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the autonomous flow
    asyncio.run(main())
