#!/usr/bin/env python3
"""
SOC Analysis Dashboard - Security Operations Center Analysis System
Analyzes session manifests and notification logs for actionable security insights
"""
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ExploitabilityLevel(Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    THEORETICAL = "theoretical"

@dataclass
class VulnerabilityFinding:
    id: str
    type: str
    severity: str
    confidence: float
    endpoint: str
    method: str
    payload: str
    evidence: str
    exploitability: ExploitabilityLevel
    verification_command: str
    business_impact: str
    remediation_priority: int

@dataclass
class ConsensusAnalysis:
    vulnerability_id: str
    severity: str
    primary_model: str
    secondary_model: str
    primary_confidence: float
    secondary_confidence: float
    consensus_score: float
    agreement: bool
    flaws_detected: List[str]
    final_determination: str
    reasoning: str
    recommendation: str

@dataclass
class TemplateStatus:
    template_id: str
    template_name: str
    template_path: str
    generated_at: str
    validation_status: str
    validation_errors: List[str]
    template_info: Dict[str, Any]

@dataclass
class DeltaAnalysis:
    new_subdomains: List[Dict[str, Any]]
    js_changes: List[Dict[str, Any]]
    ssl_changes: List[Dict[str, Any]]
    header_changes: List[Dict[str, Any]]
    technology_changes: List[Dict[str, Any]]
    total_changes: int
    risk_assessment: str

class SOCAnalyzer:
    """Security Operations Center Analysis System"""
    
    def __init__(self, session_manifest_path: str, notifications_log_path: str):
        self.session_manifest_path = Path(session_manifest_path)
        self.notifications_log_path = Path(notifications_log_path)
        
        # Analysis results
        self.session_data: Dict[str, Any] = {}
        self.notifications: List[Dict[str, Any]] = []
        self.vulnerabilities: List[VulnerabilityFinding] = []
        self.consensus_analyses: List[ConsensusAnalysis] = []
        self.template_statuses: List[TemplateStatus] = []
        self.delta_analysis: Optional[DeltaAnalysis] = None
        
        # Exploitability scoring matrix
        self.exploitability_matrix = {
            'sql_injection': {'base_score': 0.9, 'immediate': True},
            'xss_reflected': {'base_score': 0.7, 'immediate': False},
            'xss_stored': {'base_score': 0.8, 'immediate': False},
            'idor': {'base_score': 0.8, 'immediate': True},
            'ssrf': {'base_score': 0.6, 'immediate': False},
            'rce': {'base_score': 0.95, 'immediate': True},
            'lfi': {'base_score': 0.7, 'immediate': False},
            'business_logic': {'base_score': 0.5, 'immediate': False}
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive SOC analysis"""
        logger.info("Starting SOC analysis...")
        
        # Load data
        self._load_session_manifest()
        self._load_notifications()
        
        # Perform analysis
        self._analyze_vulnerabilities()
        self._analyze_consensus_results()
        self._analyze_template_status()
        self._analyze_deltas()
        self._calculate_exploitability()
        self._generate_action_items()
        
        # Generate report
        report = self._generate_soc_report()
        
        logger.info("SOC analysis completed")
        return report
    
    def _load_session_manifest(self) -> None:
        """Load and parse session manifest"""
        try:
            with open(self.session_manifest_path, 'r') as f:
                self.session_data = json.load(f)
            logger.info(f"Loaded session manifest: {self.session_data.get('session_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to load session manifest: {e}")
            raise
    
    def _load_notifications(self) -> None:
        """Load and parse notifications log"""
        try:
            with open(self.notifications_log_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        notification = self._parse_notification_line(line)
                        if notification:
                            self.notifications.append(notification)
            logger.info(f"Loaded {len(self.notifications)} notifications")
        except Exception as e:
            logger.error(f"Failed to load notifications log: {e}")
            raise
    
    def _parse_notification_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single notification line"""
        try:
            # Extract timestamp
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', line)
            if not timestamp_match:
                return None
            
            timestamp = timestamp_match.group(1)
            
            # Extract log level
            level_match = re.search(r'\[(\w+)\]', line)
            level = level_match.group(1) if level_match else 'INFO'
            
            # Extract message
            message_match = re.search(r'\] (.+)$', line)
            message = message_match.group(1) if message_match else line
            
            # Extract notification type
            notification_type = 'general'
            if 'NEW_SUBDOMAIN' in message:
                notification_type = 'new_subdomain'
            elif 'VALID_POC' in message:
                notification_type = 'valid_poc'
            elif 'CONSENSUS_ALERT' in message:
                notification_type = 'consensus_alert'
            elif 'NUCLEI_TEMPLATE' in message:
                notification_type = 'nuclei_template'
            elif 'JS_CHANGE' in message:
                notification_type = 'js_change'
            elif 'ATTACK_CHAIN' in message:
                notification_type = 'attack_chain'
            
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'type': notification_type,
                'raw_line': line
            }
        
        except Exception as e:
            logger.debug(f"Failed to parse notification line: {e}")
            return None
    
    def _analyze_vulnerabilities(self) -> None:
        """Analyze vulnerability findings"""
        logger.info("Analyzing vulnerabilities...")
        
        # Extract vulnerabilities from phase 4
        phase_4 = self.session_data.get('phases', {}).get('phase_4', {})
        findings = phase_4.get('findings', [])
        
        for finding in findings:
            if finding.get('type') in ['sql_injection', 'xss_reflected', 'xss_stored', 'idor', 'ssrf', 'rce', 'lfi', 'business_logic']:
                vuln_finding = VulnerabilityFinding(
                    id=finding.get('id', 'unknown'),
                    type=finding.get('type', 'unknown'),
                    severity=finding.get('severity', 'unknown'),
                    confidence=finding.get('confidence', 0.0),
                    endpoint=finding.get('data', {}).get('endpoint', ''),
                    method=finding.get('data', {}).get('method', ''),
                    payload=finding.get('data', {}).get('payload', ''),
                    evidence=finding.get('data', {}).get('evidence', ''),
                    exploitability=ExploitabilityLevel.THEORETICAL,  # Will be calculated later
                    verification_command='',  # Will be generated later
                    business_impact='',  # Will be calculated later
                    remediation_priority=0  # Will be calculated later
                )
                self.vulnerabilities.append(vuln_finding)
        
        logger.info(f"Analyzed {len(self.vulnerabilities)} vulnerabilities")
    
    def _analyze_consensus_results(self) -> None:
        """Analyze consensus debate mode results"""
        logger.info("Analyzing consensus results...")
        
        consensus_data = self.session_data.get('consensus_analysis', [])
        
        for consensus in consensus_data:
            analysis = ConsensusAnalysis(
                vulnerability_id=consensus.get('vulnerability_id', 'unknown'),
                severity=consensus.get('severity', 'unknown'),
                primary_model=consensus.get('primary_model', 'unknown'),
                secondary_model=consensus.get('secondary_model', 'unknown'),
                primary_confidence=consensus.get('primary_confidence', 0.0),
                secondary_confidence=consensus.get('secondary_confidence', 0.0),
                consensus_score=consensus.get('consensus_score', 0.0),
                agreement=consensus.get('agreement', False),
                flaws_detected=consensus.get('flaws_detected', []),
                final_determination=consensus.get('final_determination', 'unknown'),
                reasoning=consensus.get('reasoning', ''),
                recommendation=self._generate_consensus_recommendation(consensus)
            )
            self.consensus_analyses.append(analysis)
        
        logger.info(f"Analyzed {len(self.consensus_analyses)} consensus results")
    
    def _generate_consensus_recommendation(self, consensus: Dict[str, Any]) -> str:
        """Generate recommendation based on consensus analysis"""
        determination = consensus.get('final_determination', 'unknown')
        severity = consensus.get('severity', 'unknown')
        flaws = consensus.get('flaws_detected', [])
        
        if determination == 'pass' and severity in ['P1', 'critical']:
            return "IMMEDIATE ACTION REQUIRED: High-confidence critical vulnerability confirmed."
        elif determination == 'review':
            if 'false positive' in ' '.join(flaws).lower():
                return "MANUAL VERIFICATION: Potential false positive - verify exploitability."
            else:
                return "CAREFUL ASSESSMENT: Models disagree - requires manual validation."
        elif determination == 'fail':
            return "DO NOT PURSUE: Low confidence or critical flaws detected."
        else:
            return "FURTHER INVESTIGATION: Unclear consensus - gather more evidence."
    
    def _analyze_template_status(self) -> None:
        """Analyze Nuclei template generation status"""
        logger.info("Analyzing template status...")
        
        templates_data = self.session_data.get('nuclei_templates', [])
        
        for template in templates_data:
            status = TemplateStatus(
                template_id=template.get('template_id', 'unknown'),
                template_name=template.get('template_name', 'unknown'),
                template_path=template.get('template_path', ''),
                generated_at=template.get('generated_at', ''),
                validation_status=template.get('validation_status', 'unknown'),
                validation_errors=template.get('validation_errors', []),
                template_info=template.get('template_info', {})
            )
            self.template_statuses.append(status)
        
        logger.info(f"Analyzed {len(self.template_statuses)} templates")
    
    def _analyze_deltas(self) -> None:
        """Analyze watchdog delta changes"""
        logger.info("Analyzing delta changes...")
        
        deltas = self.session_data.get('watchdog_deltas', {})
        logger.info(f"Delta data type: {type(deltas)}")
        
        if not deltas:
            deltas = {
                'new_subdomains': [],
                'js_changes': [],
                'ssl_changes': [],
                'header_changes': [],
                'technology_changes': []
            }
        
        # Ensure deltas is a dictionary
        if isinstance(deltas, str):
            logger.warning("Delta data is a string, creating empty dict")
            deltas = {
                'new_subdomains': [],
                'js_changes': [],
                'ssl_changes': [],
                'header_changes': [],
                'technology_changes': []
            }
        
        self.delta_analysis = DeltaAnalysis(
            new_subdomains=self._extract_subdomain_details(),
            js_changes=self._extract_js_change_details(),
            ssl_changes=deltas.get('ssl_changes', []),
            header_changes=deltas.get('header_changes', []),
            technology_changes=deltas.get('technology_changes', []),
            total_changes=self._count_total_changes(deltas),
            risk_assessment=self._assess_delta_risk(deltas)
        )
        
        logger.info(f"Analyzed {self.delta_analysis.total_changes} delta changes")
    
    def _extract_subdomain_details(self) -> List[Dict[str, Any]]:
        """Extract detailed subdomain information"""
        subdomains = []
        phase_1 = self.session_data.get('phases', {}).get('phase_1', {})
        findings = phase_1.get('findings', [])
        
        for finding in findings:
            if finding.get('type') == 'new_subdomain':
                subdomains.append(finding.get('data', {}))
        
        return subdomains
    
    def _extract_js_change_details(self) -> List[Dict[str, Any]]:
        """Extract detailed JavaScript change information"""
        js_changes = []
        phase_1 = self.session_data.get('phases', {}).get('phase_1', {})
        findings = phase_1.get('findings', [])
        
        for finding in findings:
            if finding.get('type') == 'js_file_change':
                js_changes.append(finding.get('data', {}))
        
        return js_changes
    
    def _count_total_changes(self, deltas: Dict[str, Any]) -> int:
        """Count total number of changes"""
        total = 0
        for key, value in deltas.items():
            if isinstance(value, list):
                total += len(value)
        return total
    
    def _assess_delta_risk(self, deltas: Dict[str, Any]) -> str:
        """Assess risk level of delta changes"""
        risk_score = 0
        
        # New subdomains increase attack surface
        risk_score += len(deltas.get('new_subdomains', [])) * 2
        
        # JS changes with sensitive data are high risk
        js_changes = deltas.get('js_changes', [])
        for js_change in js_changes:
            if isinstance(js_change, dict) and js_change.get('sensitive_data'):
                risk_score += 5
        
        # Technology changes can introduce new vulnerabilities
        risk_score += len(deltas.get('technology_changes', [])) * 3
        
        if risk_score >= 10:
            return "HIGH"
        elif risk_score >= 5:
            return "MEDIUM"
        elif risk_score >= 1:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _calculate_exploitability(self) -> None:
        """Calculate exploitability scores for vulnerabilities"""
        logger.info("Calculating exploitability scores...")
        
        for vuln in self.vulnerabilities:
            vuln_type = vuln.type
            confidence = vuln.confidence
            
            # Get base exploitability score
            exploit_info = self.exploitability_matrix.get(vuln_type, {'base_score': 0.5, 'immediate': False})
            base_score = exploit_info['base_score']
            is_immediate = exploit_info['immediate']
            
            # Adjust based on confidence
            adjusted_score = base_score * confidence
            
            # Determine exploitability level
            if adjusted_score >= 0.8:
                exploitability = ExploitabilityLevel.IMMEDIATE
            elif adjusted_score >= 0.6:
                exploitability = ExploitabilityLevel.HIGH
            elif adjusted_score >= 0.4:
                exploitability = ExploitabilityLevel.MEDIUM
            elif adjusted_score >= 0.2:
                exploitability = ExploitabilityLevel.LOW
            else:
                exploitability = ExploitabilityLevel.THEORETICAL
            
            # Override for immediate threats
            if is_immediate and confidence >= 0.8:
                exploitability = ExploitabilityLevel.IMMEDIATE
            
            vuln.exploitability = exploitability
            
            # Generate verification command
            vuln.verification_command = self._generate_verification_command(vuln)
            
            # Calculate business impact
            vuln.business_impact = self._calculate_business_impact(vuln)
            
            # Calculate remediation priority
            vuln.remediation_priority = self._calculate_remediation_priority(vuln)
        
        logger.info(f"Calculated exploitability for {len(self.vulnerabilities)} vulnerabilities")
    
    def _generate_verification_command(self, vuln: VulnerabilityFinding) -> str:
        """Generate curl command for vulnerability verification"""
        if vuln.type == 'sql_injection':
            return f"curl -X '{vuln.method}' '{vuln.endpoint}' -H 'Content-Type: application/json' -d '{{\"user_id\":\"{vuln.payload}\"}}'"
        elif vuln.type == 'xss_reflected':
            return f"curl -X '{vuln.method}' '{vuln.endpoint}?q={vuln.payload}'"
        elif vuln.type in ['idor', 'ssrf', 'lfi']:
            return f"curl -X '{vuln.method}' '{vuln.endpoint}' -d '{vuln.payload}'"
        else:
            return f"curl -X '{vuln.method}' '{vuln.endpoint}'"
    
    def _calculate_business_impact(self, vuln: VulnerabilityFinding) -> str:
        """Calculate business impact of vulnerability"""
        severity = vuln.severity.lower()
        exploitability = vuln.exploitability.value
        
        if severity in ['p1', 'critical'] and exploitability == 'immediate':
            return "CRITICAL: Immediate data breach risk, potential complete system compromise"
        elif severity in ['p1', 'critical']:
            return "HIGH: Critical vulnerability with potential significant data exposure"
        elif severity in ['p2', 'high'] and exploitability in ['immediate', 'high']:
            return "HIGH: High-impact vulnerability requiring immediate attention"
        elif severity in ['p2', 'high']:
            return "MEDIUM: High-severity vulnerability with moderate business impact"
        else:
            return "LOW: Lower-impact vulnerability with limited business risk"
    
    def _calculate_remediation_priority(self, vuln: VulnerabilityFinding) -> int:
        """Calculate remediation priority (1-10, 1 being highest)"""
        priority = 10
        
        # Adjust based on severity
        severity = vuln.severity.lower()
        if severity in ['p1', 'critical']:
            priority -= 5
        elif severity in ['p2', 'high']:
            priority -= 3
        elif severity in ['p3', 'medium']:
            priority -= 1
        
        # Adjust based on exploitability
        exploitability = vuln.exploitability.value
        if exploitability == 'immediate':
            priority -= 3
        elif exploitability == 'high':
            priority -= 2
        elif exploitability == 'medium':
            priority -= 1
        
        # Adjust based on confidence
        if vuln.confidence >= 0.9:
            priority -= 1
        elif vuln.confidence < 0.5:
            priority += 2
        
        return max(1, min(10, priority))
    
    def _generate_action_items(self) -> None:
        """Generate prioritized action items"""
        logger.info("Generating action items...")
        
        # Sort vulnerabilities by remediation priority
        self.vulnerabilities.sort(key=lambda x: x.remediation_priority)
        
        logger.info("Action items generated")
    
    def _generate_soc_report(self) -> Dict[str, Any]:
        """Generate comprehensive SOC report"""
        logger.info("Generating SOC report...")
        
        return {
            'analysis_metadata': {
                'session_id': self.session_data.get('session_id', 'unknown'),
                'target': self.session_data.get('target', 'unknown'),
                'analysis_time': datetime.now().isoformat(),
                'data_sources': [str(self.session_manifest_path), str(self.notifications_log_path)]
            },
            
            'executive_summary': {
                'total_vulnerabilities': len(self.vulnerabilities),
                'critical_count': len([v for v in self.vulnerabilities if v.severity in ['P1', 'critical']]),
                'high_count': len([v for v in self.vulnerabilities if v.severity in ['P2', 'high']]),
                'immediate_threats': len([v for v in self.vulnerabilities if v.exploitability == ExploitabilityLevel.IMMEDIATE]),
                'new_subdomains': len(self.delta_analysis.new_subdomains) if self.delta_analysis else 0,
                'js_changes': len(self.delta_analysis.js_changes) if self.delta_analysis else 0,
                'templates_generated': len(self.template_statuses),
                'consensus_debates': len(self.consensus_analyses)
            },
            
            'delta_analysis': {
                'total_changes': self.delta_analysis.total_changes if self.delta_analysis else 0,
                'new_subdomains': self.delta_analysis.new_subdomains if self.delta_analysis else [],
                'js_changes': self.delta_analysis.js_changes if self.delta_analysis else [],
                'risk_assessment': self.delta_analysis.risk_assessment if self.delta_analysis else 'UNKNOWN',
                'recommendations': self._generate_delta_recommendations()
            },
            
            'consensus_review': {
                'total_debates': len(self.consensus_analyses),
                'agreements': len([c for c in self.consensus_analyses if c.agreement]),
                'disagreements': len([c for c in self.consensus_analyses if not c.agreement]),
                'high_confidence_consensus': len([c for c in self.consensus_analyses if c.consensus_score >= 0.8]),
                'analyses': [asdict(analysis) for analysis in self.consensus_analyses]
            },
            
            'template_status': {
                'total_templates': len(self.template_statuses),
                'valid_templates': len([t for t in self.template_statuses if t.validation_status == 'valid']),
                'invalid_templates': len([t for t in self.template_statuses if t.validation_status != 'valid']),
                'templates': [asdict(template) for template in self.template_statuses]
            },
            
            'vulnerability_ranking': {
                'by_exploitability': self._rank_by_exploitability(),
                'by_severity': self._rank_by_severity(),
                'by_business_impact': self._rank_by_business_impact(),
                'top_critical': self._get_top_critical_findings()
            },
            
            'action_items': {
                'immediate_actions': self._get_immediate_actions(),
                'verification_commands': self._get_verification_commands(),
                'remediation_priorities': self._get_remediation_priorities(),
                'monitoring_recommendations': self._get_monitoring_recommendations()
            },
            
            'recommendations': {
                'strategic': self._generate_strategic_recommendations(),
                'tactical': self._generate_tactical_recommendations(),
                'operational': self._generate_operational_recommendations()
            }
        }
    
    def _generate_delta_recommendations(self) -> List[str]:
        """Generate recommendations based on delta analysis"""
        recommendations = []
        
        if self.delta_analysis:
            if self.delta_analysis.new_subdomains:
                recommendations.append(f"INVESTIGATE {len(self.delta_analysis.new_subdomains)} new subdomains - potential attack surface expansion")
            
            if self.delta_analysis.js_changes:
                recommendations.append(f"REVIEW {len(self.delta_analysis.js_changes)} JavaScript changes - check for sensitive data exposure")
            
            if self.delta_analysis.risk_assessment == 'HIGH':
                recommendations.append("HIGH RISK: Implement immediate monitoring for new assets")
        
        return recommendations
    
    def _rank_by_exploitability(self) -> List[Dict[str, Any]]:
        """Rank vulnerabilities by exploitability"""
        sorted_vulns = sorted(self.vulnerabilities, key=lambda x: {
            ExploitabilityLevel.IMMEDIATE: 0,
            ExploitabilityLevel.HIGH: 1,
            ExploitabilityLevel.MEDIUM: 2,
            ExploitabilityLevel.LOW: 3,
            ExploitabilityLevel.THEORETICAL: 4
        }[x.exploitability])
        
        return [{
            'id': vuln.id,
            'type': vuln.type,
            'severity': vuln.severity,
            'exploitability': vuln.exploitability.value,
            'confidence': vuln.confidence,
            'endpoint': vuln.endpoint,
            'verification_command': vuln.verification_command
        } for vuln in sorted_vulns]
    
    def _rank_by_severity(self) -> List[Dict[str, Any]]:
        """Rank vulnerabilities by severity"""
        severity_order = {'P1': 0, 'critical': 0, 'P2': 1, 'high': 1, 'P3': 2, 'medium': 2, 'P4': 3, 'low': 3, 'P5': 4, 'info': 4}
        
        sorted_vulns = sorted(self.vulnerabilities, key=lambda x: severity_order.get(x.severity.lower(), 5))
        
        return [{
            'id': vuln.id,
            'type': vuln.type,
            'severity': vuln.severity,
            'confidence': vuln.confidence,
            'endpoint': vuln.endpoint,
            'business_impact': vuln.business_impact
        } for vuln in sorted_vulns]
    
    def _rank_by_business_impact(self) -> List[Dict[str, Any]]:
        """Rank vulnerabilities by business impact"""
        impact_order = {
            'CRITICAL': 0,
            'HIGH': 1,
            'MEDIUM': 2,
            'LOW': 3
        }
        
        sorted_vulns = sorted(self.vulnerabilities, key=lambda x: impact_order.get(x.business_impact.split(':')[0], 4))
        
        return [{
            'id': vuln.id,
            'type': vuln.type,
            'severity': vuln.severity,
            'business_impact': vuln.business_impact,
            'remediation_priority': vuln.remediation_priority
        } for vuln in sorted_vulns]
    
    def _get_top_critical_findings(self) -> List[Dict[str, Any]]:
        """Get top critical findings"""
        critical_vulns = [v for v in self.vulnerabilities if v.severity in ['P1', 'critical']]
        critical_vulns.sort(key=lambda x: x.remediation_priority)
        
        return [{
            'id': vuln.id,
            'type': vuln.type,
            'severity': vuln.severity,
            'confidence': vuln.confidence,
            'endpoint': vuln.endpoint,
            'payload': vuln.payload,
            'evidence': vuln.evidence,
            'verification_command': vuln.verification_command,
            'business_impact': vuln.business_impact
        } for vuln in critical_vulns[:5]]
    
    def _get_immediate_actions(self) -> List[str]:
        """Get immediate action items"""
        actions = []
        
        immediate_vulns = [v for v in self.vulnerabilities if v.exploitability == ExploitabilityLevel.IMMEDIATE]
        
        for vuln in immediate_vulns[:3]:
            actions.append(f"CRITICAL: Verify {vuln.type} at {vuln.endpoint} - {vuln.business_impact}")
        
        if self.delta_analysis and self.delta_analysis.js_changes:
            actions.append("URGENT: Review JavaScript changes for sensitive data exposure")
        
        if self.delta_analysis and self.delta_analysis.new_subdomains:
            actions.append(f"PRIORITY: Investigate {len(self.delta_analysis.new_subdomains)} new subdomains")
        
        return actions
    
    def _get_verification_commands(self) -> List[Dict[str, Any]]:
        """Get verification commands for top vulnerabilities"""
        top_vulns = sorted(self.vulnerabilities, key=lambda x: x.remediation_priority)[:5]
        
        return [{
            'vulnerability_id': vuln.id,
            'vulnerability_type': vuln.type,
            'severity': vuln.severity,
            'command': vuln.verification_command,
            'expected_result': vuln.evidence,
            'priority': vuln.remediation_priority
        } for vuln in top_vulns]
    
    def _get_remediation_priorities(self) -> List[Dict[str, Any]]:
        """Get prioritized remediation list"""
        sorted_vulns = sorted(self.vulnerabilities, key=lambda x: x.remediation_priority)
        
        return [{
            'priority': i + 1,
            'vulnerability_id': vuln.id,
            'type': vuln.type,
            'severity': vuln.severity,
            'endpoint': vuln.endpoint,
            'remediation_steps': self._generate_remediation_steps(vuln),
            'estimated_effort': self._estimate_remediation_effort(vuln)
        } for i, vuln in enumerate(sorted_vulns[:10])]
    
    def _get_monitoring_recommendations(self) -> List[str]:
        """Get monitoring recommendations"""
        recommendations = []
        
        recommendations.append("Implement real-time monitoring for new subdomains")
        recommendations.append("Set up alerts for JavaScript file changes")
        recommendations.append("Monitor for consensus debate mode triggers")
        recommendations.append("Track template validation failures")
        
        if self.consensus_analyses:
            disagreements = [c for c in self.consensus_analyses if not c.agreement]
            if disagreements:
                recommendations.append("Manual verification required for model disagreements")
        
        return recommendations
    
    def _generate_strategic_recommendations(self) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        if len(self.vulnerabilities) > 0:
            critical_count = len([v for v in self.vulnerabilities if v.severity in ['P1', 'critical']])
            if critical_count > 0:
                recommendations.append("IMMEDIATE: Address all critical vulnerabilities within 24 hours")
            
            recommendations.append("Implement secure coding practices to prevent similar vulnerabilities")
            recommendations.append("Enhance input validation and output encoding")
            recommendations.append("Regular security assessments and penetration testing")
        
        if self.delta_analysis and self.delta_analysis.total_changes > 0:
            recommendations.append("Establish change management process for application updates")
            recommendations.append("Implement automated security testing in CI/CD pipeline")
        
        return recommendations
    
    def _generate_tactical_recommendations(self) -> List[str]:
        """Generate tactical recommendations"""
        recommendations = []
        
        for vuln in self.vulnerabilities[:3]:
            if vuln.type == 'sql_injection':
                recommendations.append(f"Implement parameterized queries for {vuln.endpoint}")
            elif vuln.type == 'xss_reflected':
                recommendations.append(f"Add output encoding and CSP headers for {vuln.endpoint}")
            elif vuln.type == 'idor':
                recommendations.append(f"Add authorization checks for {vuln.endpoint}")
        
        return recommendations
    
    def _generate_operational_recommendations(self) -> List[str]:
        """Generate operational recommendations"""
        recommendations = []
        
        recommendations.append("Schedule regular vulnerability scans")
        recommendations.append("Implement security monitoring and alerting")
        recommendations.append("Train development team on secure coding practices")
        recommendations.append("Establish incident response procedures")
        recommendations.append("Document and track all security findings")
        
        return recommendations
    
    def _generate_remediation_steps(self, vuln: VulnerabilityFinding) -> List[str]:
        """Generate remediation steps for vulnerability"""
        if vuln.type == 'sql_injection':
            return [
                "Implement parameterized queries/prepared statements",
                "Add input validation and sanitization",
                "Apply principle of least privilege to database accounts",
                "Implement database activity monitoring"
            ]
        elif vuln.type == 'xss_reflected':
            return [
                "Implement output encoding for user input",
                "Add Content Security Policy (CSP) headers",
                "Validate and sanitize all user input",
                "Use secure frameworks with built-in XSS protection"
            ]
        elif vuln.type == 'idor':
            return [
                "Implement proper authorization checks",
                "Add user ownership verification",
                "Implement access control lists",
                "Regular access rights audits"
            ]
        else:
            return [
                "Conduct thorough security review",
                "Implement defense in depth",
                "Add logging and monitoring",
                "Regular security testing"
            ]
    
    def _estimate_remediation_effort(self, vuln: VulnerabilityFinding) -> str:
        """Estimate remediation effort"""
        effort_matrix = {
            'sql_injection': 'HIGH',
            'xss_reflected': 'MEDIUM',
            'xss_stored': 'HIGH',
            'idor': 'MEDIUM',
            'ssrf': 'HIGH',
            'rce': 'CRITICAL',
            'lfi': 'MEDIUM',
            'business_logic': 'HIGH'
        }
        
        return effort_matrix.get(vuln.type, 'MEDIUM')


def main():
    """Main function to run SOC analysis"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python soc_analysis.py <session_manifest.json> <notifications.log>")
        sys.exit(1)
    
    session_manifest_path = sys.argv[1]
    notifications_log_path = sys.argv[2]
    
    # Create analyzer
    analyzer = SOCAnalyzer(session_manifest_path, notifications_log_path)
    
    # Run analysis
    try:
        report = analyzer.analyze()
        
        # Print report
        print("\n" + "="*80)
        print("RECONX-ELITE SOC ANALYSIS REPORT")
        print("="*80)
        
        print("\nEXECUTIVE SUMMARY:")
        print("-" * 40)
        summary = report['executive_summary']
        print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"Critical (P1): {summary['critical_count']}")
        print(f"High (P2): {summary['high_count']}")
        print(f"Immediate Threats: {summary['immediate_threats']}")
        print(f"New Subdomains: {summary['new_subdomains']}")
        print(f"JavaScript Changes: {summary['js_changes']}")
        print(f"Templates Generated: {summary['templates_generated']}")
        print(f"Consensus Debates: {summary['consensus_debates']}")
        
        print("\nDELTA ANALYSIS:")
        print("-" * 40)
        delta = report['delta_analysis']
        print(f"Total Changes: {delta['total_changes']}")
        print(f"Risk Assessment: {delta['risk_assessment']}")
        
        if delta['new_subdomains']:
            print(f"\nNew Subdomains ({len(delta['new_subdomains'])}):")
            for subdomain in delta['new_subdomains']:
                print(f"  - {subdomain.get('subdomain', 'unknown')} ({subdomain.get('ip_address', 'unknown')})")
        
        if delta['js_changes']:
            print(f"\nJavaScript Changes ({len(delta['js_changes'])}):")
            for js_change in delta['js_changes']:
                print(f"  - {js_change.get('file', 'unknown')} (Size: {js_change.get('size_diff', 'unknown')})")
        
        print("\nCONSENSUS REVIEW:")
        print("-" * 40)
        consensus = report['consensus_review']
        print(f"Total Debates: {consensus['total_debates']}")
        print(f"Agreements: {consensus['agreements']}")
        print(f"Disagreements: {consensus['disagreements']}")
        print(f"High Confidence Consensus: {consensus['high_confidence_consensus']}")
        
        for analysis in consensus['analyses']:
            print(f"\n{analysis['vulnerability_id']} ({analysis['severity']}):")
            print(f"  Primary Model: {analysis['primary_model']} (Confidence: {analysis['primary_confidence']:.2f})")
            print(f"  Secondary Model: {analysis['secondary_model']} (Confidence: {analysis['secondary_confidence']:.2f})")
            print(f"  Consensus Score: {analysis['consensus_score']:.2f}")
            print(f"  Agreement: {analysis['agreement']}")
            print(f"  Determination: {analysis['final_determination']}")
            print(f"  Recommendation: {analysis['recommendation']}")
        
        print("\nTEMPLATE STATUS:")
        print("-" * 40)
        templates = report['template_status']
        print(f"Total Templates: {templates['total_templates']}")
        print(f"Valid Templates: {templates['valid_templates']}")
        print(f"Invalid Templates: {templates['invalid_templates']}")
        
        for template in templates['templates']:
            print(f"\n{template['template_name']}:")
            print(f"  Status: {template['validation_status']}")
            print(f"  Path: {template['template_path']}")
            print(f"  Generated: {template['generated_at']}")
        
        print("\nTOP CRITICAL FINDINGS:")
        print("-" * 40)
        critical = report['vulnerability_ranking']['top_critical']
        
        for i, finding in enumerate(critical, 1):
            print(f"\n{i}. {finding['id']} ({finding['type']}, {finding['severity']})")
            print(f"   Endpoint: {finding['endpoint']}")
            print(f"   Business Impact: {finding['business_impact']}")
            print(f"   Verification Command: {finding['verification_command']}")
        
        print("\nIMMEDIATE ACTIONS:")
        print("-" * 40)
        actions = report['action_items']['immediate_actions']
        for action in actions:
            print(f"  - {action}")
        
        print("\nVERIFICATION COMMANDS:")
        print("-" * 40)
        commands = report['action_items']['verification_commands']
        for cmd in commands:
            print(f"\n{cmd['vulnerability_id']} ({cmd['vulnerability_type']}, Priority: {cmd['priority']}):")
            print(f"  Command: {cmd['command']}")
            print(f"  Expected: {cmd['expected_result']}")
        
        print("\nRECOMMENDATIONS:")
        print("-" * 40)
        all_recommendations = (
            report['recommendations']['strategic'] +
            report['recommendations']['tactical'] +
            report['recommendations']['operational']
        )
        
        for i, rec in enumerate(all_recommendations, 1):
            print(f"{i}. {rec}")
        
        # Save detailed report
        with open('soc_analysis_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: soc_analysis_report.json")
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
