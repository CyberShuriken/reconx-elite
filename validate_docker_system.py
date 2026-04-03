"""System validation script for Docker Compose deployment."""

import asyncio
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DockerSystemValidator:
    """Comprehensive Docker Compose system validation."""
    
    def __init__(self):
        self.validation_results = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall_status": "pending",
            "errors": [],
            "warnings": []
        }
    
    async def run_full_validation(self) -> dict:
        """Run complete Docker Compose system validation."""
        
        logger.info("Starting Docker Compose system validation...")
        
        checks = [
            ("docker_compose", self._validate_docker_compose),
            ("services_health", self._validate_services_health),
            ("database", self._validate_database),
            ("api_connectivity", self._validate_api_connectivity),
            ("ai_service", self._validate_ai_service),
            ("new_features", self._validate_new_features),
        ]
        
        for check_name, check_func in checks:
            try:
                logger.info(f"Running {check_name} validation...")
                result = await check_func()
                self.validation_results["checks"][check_name] = result
                
                if result["status"] == "error":
                    self.validation_results["overall_status"] = "failed"
                    self.validation_results["errors"].append(f"{check_name}: {result.get('message', 'Unknown error')}")
                elif result["status"] == "warning":
                    if self.validation_results["overall_status"] == "pending":
                        self.validation_results["overall_status"] = "degraded"
                    self.validation_results["warnings"].append(f"{check_name}: {result.get('message', 'Warning')}")
                    
            except Exception as e:
                logger.error(f"Check {check_name} failed: {e}")
                self.validation_results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e)
                }
                self.validation_results["overall_status"] = "failed"
                self.validation_results["errors"].append(f"{check_name}: {str(e)}")
        
        self.validation_results["end_time"] = datetime.now(timezone.utc).isoformat()
        
        # Print summary
        self._print_summary()
        
        return self.validation_results
    
    async def _validate_docker_compose(self) -> dict:
        """Validate Docker Compose configuration."""
        
        try:
            # Check if docker-compose.yml exists
            compose_file = Path("docker-compose.yml")
            if not compose_file.exists():
                return {
                    "status": "error",
                    "message": "docker-compose.yml not found"
                }
            
            # Validate compose file syntax
            result = subprocess.run(
                ["docker-compose", "config"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Docker Compose config validation failed: {result.stderr}"
                }
            
            # Check if services are defined
            compose_output = result.stdout
            required_services = ["backend", "worker", "postgres", "redis"]
            missing_services = []
            
            for service in required_services:
                if service not in compose_output:
                    missing_services.append(service)
            
            if missing_services:
                return {
                    "status": "error",
                    "message": f"Missing required services: {', '.join(missing_services)}"
                }
            
            return {
                "status": "healthy",
                "message": "Docker Compose configuration valid",
                "services_found": required_services
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Docker Compose validation timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Docker Compose validation failed: {str(e)}"
            }
    
    async def _validate_services_health(self) -> dict:
        """Validate Docker services health."""
        
        try:
            # Check if containers are running
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Failed to check container status: {result.stderr}"
                }
            
            # Parse container status
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            running_containers = []
            stopped_containers = []
            
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    container_name = parts[0]
                    status = parts[2]
                    if "Up" in status:
                        running_containers.append(container_name)
                    else:
                        stopped_containers.append(container_name)
            
            if stopped_containers:
                return {
                    "status": "warning",
                    "message": f"Some containers not running: {', '.join(stopped_containers)}",
                    "running": running_containers,
                    "stopped": stopped_containers
                }
            
            return {
                "status": "healthy",
                "message": "All containers running",
                "containers": running_containers
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Service health check failed: {str(e)}"
            }
    
    async def _validate_database(self) -> dict:
        """Validate database connectivity and schema."""
        
        try:
            # Test database connectivity via backend container
            result = subprocess.run(
                ["docker-compose", "exec", "backend", "python", "-c", """
import sys
sys.path.append('/app')
from app.core.database import get_sessionmaker
from sqlalchemy import text

try:
    db = get_sessionmaker()()
    result = db.execute(text('SELECT 1')).scalar()
    if result == 1:
        print('Database connection successful')
    else:
        print('Database query failed')
    db.close()
except Exception as e:
    print(f'Database error: {e}')
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Database test failed: {result.stderr}"
                }
            
            if "Database connection successful" in result.stdout:
                return {
                    "status": "healthy",
                    "message": "Database connectivity verified"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Database test failed: {result.stdout}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database validation failed: {str(e)}"
            }
    
    async def _validate_api_connectivity(self) -> dict:
        """Validate API connectivity and basic endpoints."""
        
        try:
            import httpx
            
            # Test basic API endpoints
            test_endpoints = [
                ("health", "GET"),
                ("/api/system/health", "GET"),
            ]
            
            results = {}
            
            async with httpx.AsyncClient(timeout=10) as client:
                for endpoint, method in test_endpoints:
                    try:
                        if method == "GET":
                            response = await client.get(f"http://localhost:8000{endpoint}")
                        
                        results[endpoint] = {
                            "status_code": response.status_code,
                            "success": response.status_code < 400
                        }
                    except Exception as e:
                        results[endpoint] = {
                            "status_code": None,
                            "success": False,
                            "error": str(e)
                        }
            
            failed_endpoints = [ep for ep, res in results.items() if not res.get("success", False)]
            
            if failed_endpoints:
                return {
                    "status": "warning",
                    "message": f"Some endpoints failed: {', '.join(failed_endpoints)}",
                    "results": results
                }
            
            return {
                "status": "healthy",
                "message": "API connectivity verified",
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"API connectivity test failed: {str(e)}"
            }
    
    async def _validate_ai_service(self) -> dict:
        """Validate AI service configuration."""
        
        try:
            # Test AI service via backend container
            result = subprocess.run(
                ["docker-compose", "exec", "backend", "python", "-c", """
import sys
sys.path.append('/app')
from app.core.config import settings

if settings.gemini_api_key:
    print('AI service configured')
else:
    print('AI service not configured')
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"AI service test failed: {result.stderr}"
                }
            
            if "AI service configured" in result.stdout:
                return {
                    "status": "healthy",
                    "message": "AI service properly configured"
                }
            else:
                return {
                    "status": "warning",
                    "message": "AI service not configured (optional feature)"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI service validation failed: {str(e)}"
            }
    
    async def _validate_new_features(self) -> dict:
        """Validate new advanced features."""
        
        try:
            # Test new feature imports via backend container
            result = subprocess.run(
                ["docker-compose", "exec", "backend", "python", "-c", """
import sys
sys.path.append('/app')

try:
    # Test new feature imports
    from app.services.exploit_validator import ExploitValidator
    from app.services.out_of_band_service import OutOfBandService
    from app.services.manual_tester import ManualTester
    from app.services.intelligence_learning import IntelligenceLearningService
    from app.services.custom_template_engine import CustomTemplateEngine
    from app.models.exploit_validation import ExploitValidation
    from app.models.out_of_band_interaction import OutOfBandInteraction
    from app.models.learning_models import LearningPattern, SuccessfulPayload, HighValueEndpoint
    from app.models.custom_templates import CustomNucleiTemplate
    
    print('All new features imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
except Exception as e:
    print(f'Error: {e}')
"""],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"New features test failed: {result.stderr}"
                }
            
            if "All new features imported successfully" in result.stdout:
                return {
                    "status": "healthy",
                    "message": "All new features available"
                }
            else:
                return {
                    "status": "error",
                    "message": f"New features import failed: {result.stdout}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"New features validation failed: {str(e)}"
            }
    
    def _print_summary(self):
        """Print validation summary."""
        
        print("\n" + "="*60)
        print("RECONX ELITE - DOCKER COMPOSE VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Overall Status: {self.validation_results['overall_status'].upper()}")
        print(f"Start Time: {self.validation_results['start_time']}")
        print(f"End Time: {self.validation_results['end_time']}")
        
        print("\nCheck Results:")
        for check_name, result in self.validation_results["checks"].items():
            status = result["status"]
            message = result.get("message", "")
            print(f"  {check_name}: {status.upper()} - {message}")
        
        if self.validation_results["errors"]:
            print("\nErrors:")
            for error in self.validation_results["errors"]:
                print(f"  ❌ {error}")
        
        if self.validation_results["warnings"]:
            print("\nWarnings:")
            for warning in self.validation_results["warnings"]:
                print(f"  ⚠️  {warning}")
        
        print("\n" + "="*60)
        
        if self.validation_results["overall_status"] == "healthy":
            print("🎉 All systems operational! ReconX Elite is ready.")
        elif self.validation_results["overall_status"] == "degraded":
            print("⚠️  System operational with some warnings.")
        else:
            print("❌ System validation failed. Please check errors above.")
        
        print("="*60)


async def main():
    """Main validation function."""
    
    validator = DockerSystemValidator()
    results = await validator.run_full_validation()
    
    # Exit with appropriate code
    if results["overall_status"] == "healthy":
        sys.exit(0)
    elif results["overall_status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
