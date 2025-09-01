#!/usr/bin/env python3
"""
Security Guard Module
Full implementation for security validation and access control
"""

import re
import json
import sqlite3
import hashlib
import logging
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import ipaddress
import threading

logger = logging.getLogger(__name__)

class SecurityGuard:
    """Advanced security guard for SQL injection, access control, and threat detection"""
    
    def __init__(self, db_path: str = "tests/security_guard.db"):
        self.db_path = db_path
        
        # Check if PII scanning is enabled via environment variable
        self.enable_pii_scanning = os.getenv("ENABLE_PII_SCANNING", "true").lower() == "true"
        logger.info(f"🔒 SecurityGuard: PII scanning {'enabled' if self.enable_pii_scanning else 'disabled'}")
        
        self.dangerous_patterns = [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM",
            r"TRUNCATE\s+TABLE",
            r"ALTER\s+TABLE",
            r"CREATE\s+TABLE",
            r"INSERT\s+INTO",
            r"UPDATE\s+SET",
            r"GRANT\s+",
            r"REVOKE\s+",
            r"EXEC\s+",
            r"EXECUTE\s+",
            r"xp_",
            r"sp_",
            r"WAITFOR\s+",
            r"BULK\s+INSERT",
            r"BACKUP\s+DATABASE",
            r"RESTORE\s+DATABASE",
            r"SHUTDOWN",
            r"KILL",
            r"RECONFIGURE",
            r"DBCC",
            r"xp_cmdshell",
            r"sp_configure"
        ]
        
        # PII Detection Patterns
        self.pii_patterns = {
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'email\s*[:=]\s*["\']?[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}["\']?'
            ],
            'phone': [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
                r'\b\+1\s*\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'phone\s*[:=]\s*["\']?\d{3}[-.]?\d{3}[-.]?\d{4}["\']?'
            ],
            'ssn': [
                r'\b\d{3}-\d{2}-\d{4}\b',
                r'\b\d{9}\b',
                r'ssn\s*[:=]\s*["\']?\d{3}-\d{2}-\d{4}["\']?'
            ],
            'credit_card': [
                r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                r'\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b',
                r'credit_card\s*[:=]\s*["\']?\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}["\']?'
            ],
            'address': [
                r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Terrace|Ter)\b',
                r'address\s*[:=]\s*["\']?\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl|Way|Terrace|Ter)["\']?'
            ],
            'name': [
                r'name\s*[:=]\s*["\']?[A-Z][a-z]+\s+[A-Z][a-z]+["\']?',
                r'first_name\s*[:=]\s*["\']?[A-Z][a-z]+["\']?',
                r'last_name\s*[:=]\s*["\']?[A-Z][a-z]+["\']?'
            ],
            'date_of_birth': [
                r'\b(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}\b',
                r'\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b',
                r'birth_date\s*[:=]\s*["\']?(?:0[1-9]|1[0-2])/(?:0[1-9]|[12]\d|3[01])/\d{4}["\']?'
            ]
        }
        
        # PII Risk Levels
        self.pii_risk_levels = {
            'email': 'medium',
            'phone': 'medium',
            'ssn': 'high',
            'credit_card': 'high',
            'address': 'low',
            'name': 'low',
            'date_of_birth': 'medium'
        }
        
        self.allowed_operations = ["SELECT", "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT", "GROUP BY", "ORDER BY", "HAVING"]
        self.blocked_ips = set()
        self.rate_limits = {}  # IP -> {count: int, reset_time: datetime}
        
        # PII Masking/Unmasking System
        self.pii_mapping = {}  # Maps masked values to original values
        self.masked_to_original = {}  # Maps masked values to original values
        self.original_to_masked = {}  # Maps original values to masked values
        self.mapping_session_id = None  # Session ID for mapping
        self.mapping_timestamp = None  # Timestamp for mapping
        self._lock = threading.Lock()
        self._init_database()
    
    def detect_pii(self, content: str, context: str = "unknown") -> Dict[str, Any]:
        """Detect PII in content before embedding into vector database"""
        
        # Check if PII scanning is disabled
        if not self.enable_pii_scanning:
            logger.info(f"🔒 SecurityGuard: PII scanning disabled, skipping scan for {context}")
            return {
                'detected': False,
                'pii_types': [],
                'risk_level': 'low',
                'sensitive_data': [],
                'recommendations': [],
                'context': context,
                'content_length': len(content),
                'scanning_disabled': True
            }
        
        logger.info(f"🔒 SecurityGuard: Scanning content for PII (context: {context})")
        
        pii_findings = {
            'detected': False,
            'pii_types': [],
            'risk_level': 'low',
            'sensitive_data': [],
            'recommendations': [],
            'context': context,
            'content_length': len(content)
        }
        
        detected_pii = []
        
        # Scan for each PII type
        for pii_type, patterns in self.pii_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    detected_pii.append({
                        'type': pii_type,
                        'value': match.group(),
                        'position': match.start(),
                        'risk_level': self.pii_risk_levels.get(pii_type, 'medium'),
                        'pattern': pattern
                    })
        
        if detected_pii:
            pii_findings['detected'] = True
            pii_findings['pii_types'] = list(set([item['type'] for item in detected_pii]))
            pii_findings['sensitive_data'] = detected_pii
            
            # Determine overall risk level
            risk_levels = [item['risk_level'] for item in detected_pii]
            if 'high' in risk_levels:
                pii_findings['risk_level'] = 'high'
            elif 'medium' in risk_levels:
                pii_findings['risk_level'] = 'medium'
            else:
                pii_findings['risk_level'] = 'low'
            
            # Generate recommendations
            pii_findings['recommendations'] = self._generate_pii_recommendations(detected_pii)
            
            # Log PII detection
            self._log_pii_detection(pii_findings)
            
            logger.warning(f"⚠️ SecurityGuard: PII detected in {context} - {len(detected_pii)} items found")
        else:
            logger.info(f"✅ SecurityGuard: No PII detected in {context}")
        
        return pii_findings
    
    def _generate_pii_recommendations(self, detected_pii: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for handling detected PII"""
        recommendations = []
        
        high_risk_types = [item['type'] for item in detected_pii if item['risk_level'] == 'high']
        medium_risk_types = [item['type'] for item in detected_pii if item['risk_level'] == 'medium']
        
        if high_risk_types:
            recommendations.append(f"🚨 HIGH RISK: Remove or anonymize {', '.join(high_risk_types)} data before embedding")
            recommendations.append("🔒 Consider using data masking or tokenization for sensitive fields")
        
        if medium_risk_types:
            recommendations.append(f"⚠️ MEDIUM RISK: Review {', '.join(medium_risk_types)} data for privacy compliance")
            recommendations.append("📧 Consider using generic placeholders for contact information")
        
        if detected_pii:
            recommendations.append("🛡️ Implement data anonymization before vector embedding")
            recommendations.append("📋 Add privacy controls to prevent PII exposure in search results")
        
        return recommendations
    
    def _log_pii_detection(self, pii_findings: Dict[str, Any]):
        """Log PII detection event to security database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events (
                    timestamp, event_type, query, threat_level, action_taken, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                'PII_DETECTION',
                f"Context: {pii_findings['context']}",
                pii_findings['risk_level'],
                'BLOCKED' if pii_findings['risk_level'] == 'high' else 'FLAGGED',
                json.dumps(pii_findings)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to log PII detection: {e}")
    
    def sanitize_content_for_embedding(self, content: str, context: str = "unknown") -> Tuple[str, Dict[str, Any]]:
        """Sanitize content by removing or masking PII before embedding"""
        
        # Check if PII scanning is disabled
        if not self.enable_pii_scanning:
            logger.info(f"🛡️ SecurityGuard: PII scanning disabled, returning original content for {context}")
            return content, {
                'original_length': len(content),
                'sanitized_length': len(content),
                'pii_removed': 0,
                'pii_masked': 0,
                'sanitization_applied': False,
                'scanning_disabled': True
            }
        
        logger.info(f"🛡️ SecurityGuard: Sanitizing content for embedding (context: {context})")
        
        # Detect PII first
        pii_findings = self.detect_pii(content, context)
        
        sanitized_content = content
        sanitization_report = {
            'original_length': len(content),
            'sanitized_length': len(content),
            'pii_removed': 0,
            'pii_masked': 0,
            'sanitization_applied': False
        }
        
        if pii_findings['detected']:
            sanitized_content = content
            
            for pii_item in pii_findings['sensitive_data']:
                original_value = pii_item['value']
                pii_type = pii_item['type']
                risk_level = pii_item['risk_level']
                
                if risk_level == 'high':
                    # Remove high-risk PII completely
                    masked_value = f"[{pii_type.upper()}_REMOVED]"
                    sanitized_content = sanitized_content.replace(original_value, masked_value)
                    sanitization_report['pii_removed'] += 1
                    
                    # Store mapping for unmasking
                    self.store_pii_mapping(original_value, masked_value, pii_type, context)
                    
                elif risk_level == 'medium':
                    # Mask medium-risk PII
                    if pii_type == 'email':
                        masked_value = self._mask_email(original_value)
                    elif pii_type == 'phone':
                        masked_value = self._mask_phone(original_value)
                    elif pii_type == 'credit_card':
                        masked_value = self._mask_credit_card(original_value)
                    else:
                        masked_value = f"[{pii_type.upper()}_MASKED]"
                    
                    sanitized_content = sanitized_content.replace(original_value, masked_value)
                    sanitization_report['pii_masked'] += 1
                    
                    # Store mapping for unmasking
                    self.store_pii_mapping(original_value, masked_value, pii_type, context)
            
            sanitization_report['sanitized_length'] = len(sanitized_content)
            sanitization_report['sanitization_applied'] = True
            
            logger.info(f"🛡️ SecurityGuard: Sanitized {sanitization_report['pii_removed']} removed, {sanitization_report['pii_masked']} masked")
        
        return sanitized_content, sanitization_report
    
    def _mask_email(self, email: str) -> str:
        """Mask email address while preserving domain"""
        if '@' in email:
            username, domain = email.split('@', 1)
            if len(username) > 2:
                masked_username = username[:2] + '*' * (len(username) - 2)
            else:
                masked_username = '*' * len(username)
            return f"{masked_username}@{domain}"
        return "[EMAIL_MASKED]"
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number while preserving format"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) ***-{digits[-4:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) ***-{digits[-4:]}"
        return "[PHONE_MASKED]"
    
    def _mask_credit_card(self, card: str) -> str:
        """Mask credit card number"""
        digits = re.sub(r'\D', '', card)
        if len(digits) >= 13:
            return f"****-****-****-{digits[-4:]}"
        return "[CREDIT_CARD_MASKED]"
    
    def _init_database(self):
        """Initialize SQLite database for security logging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create security_events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user TEXT,
                    ip_address TEXT,
                    query TEXT,
                    sql_query TEXT,
                    threat_level TEXT,
                    action_taken TEXT,
                    details TEXT
                )
            ''')
            
            # Create blocked_ips table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    blocked_at TEXT NOT NULL,
                    reason TEXT,
                    expires_at TEXT
                )
            ''')
            
            # Create user_permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL,
                    role TEXT NOT NULL,
                    permissions TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON security_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON security_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user ON security_events(user)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip ON security_events(ip_address)')
            
            conn.commit()
            conn.close()
            logger.info("✅ Security guard database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize security guard database: {e}")
            raise
    
    def create_pii_mapping_session(self, session_id: str = None) -> str:
        """Create a new PII mapping session for tracking masked values"""
        import uuid
        from datetime import datetime
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.mapping_session_id = session_id
        self.mapping_timestamp = datetime.now()
        
        # Clear previous mappings
        self.pii_mapping = {}
        self.masked_to_original = {}
        self.original_to_masked = {}
        
        logger.info(f"🔐 SecurityGuard: Created PII mapping session {session_id}")
        return session_id
    
    def get_pii_mapping_session(self) -> Dict[str, Any]:
        """Get current PII mapping session information"""
        return {
            'session_id': self.mapping_session_id,
            'timestamp': self.mapping_timestamp,
            'total_mappings': len(self.pii_mapping),
            'masked_count': len(self.masked_to_original),
            'original_count': len(self.original_to_masked)
        }
    
    def store_pii_mapping(self, original_value: str, masked_value: str, pii_type: str, context: str = "unknown") -> None:
        """Store a mapping between original and masked PII values"""
        if not self.mapping_session_id:
            self.create_pii_mapping_session()
        
        # Store the mapping
        mapping_key = f"{pii_type}_{context}_{hash(original_value)}"
        self.pii_mapping[mapping_key] = {
            'original': original_value,
            'masked': masked_value,
            'pii_type': pii_type,
            'context': context,
            'session_id': self.mapping_session_id,
            'timestamp': self.mapping_timestamp
        }
        
        # Store bidirectional mappings
        self.masked_to_original[masked_value] = original_value
        self.original_to_masked[original_value] = masked_value
        
        logger.info(f"🔐 SecurityGuard: Stored PII mapping for {pii_type} in {context}")
    
    def unmask_pii(self, masked_content: str) -> Tuple[str, Dict[str, Any]]:
        """Unmask PII content using stored mappings"""
        if not self.mapping_session_id:
            logger.warning("⚠️ SecurityGuard: No PII mapping session active")
            return masked_content, {'unmasked_count': 0, 'errors': ['No mapping session']}
        
        unmasked_content = masked_content
        unmasked_count = 0
        errors = []
        
        # Replace masked values with original values
        for masked_value, original_value in self.masked_to_original.items():
            if masked_value in unmasked_content:
                unmasked_content = unmasked_content.replace(masked_value, original_value)
                unmasked_count += 1
                logger.info(f"🔓 SecurityGuard: Unmasked {masked_value} → {original_value}")
        
        # Also handle removed values (high-risk PII)
        removed_patterns = {
            '[SSN_REMOVED]': 'ssn',
            '[CREDIT_CARD_REMOVED]': 'credit_card',
            '[DATE_OF_BIRTH_MASKED]': 'date_of_birth'
        }
        
        for removed_pattern, pii_type in removed_patterns.items():
            if removed_pattern in unmasked_content:
                # Try to find original value in mappings
                for mapping_key, mapping_data in self.pii_mapping.items():
                    if mapping_data['pii_type'] == pii_type and mapping_data['masked'] == removed_pattern:
                        unmasked_content = unmasked_content.replace(removed_pattern, mapping_data['original'])
                        unmasked_count += 1
                        logger.info(f"🔓 SecurityGuard: Restored {removed_pattern} → {mapping_data['original']}")
                        break
                else:
                    errors.append(f"Could not restore {removed_pattern} - no mapping found")
        
        return unmasked_content, {
            'unmasked_count': unmasked_count,
            'errors': errors,
            'session_id': self.mapping_session_id
        }
    
    def get_pii_mappings(self, pii_type: str = None, context: str = None) -> Dict[str, Any]:
        """Get stored PII mappings with optional filtering"""
        mappings = {}
        
        for mapping_key, mapping_data in self.pii_mapping.items():
            if pii_type and mapping_data['pii_type'] != pii_type:
                continue
            if context and mapping_data['context'] != context:
                continue
            
            mappings[mapping_key] = mapping_data
        
        return {
            'mappings': mappings,
            'total_count': len(mappings),
            'session_id': self.mapping_session_id,
            'timestamp': self.mapping_timestamp
        }
    
    def clear_pii_mappings(self) -> None:
        """Clear all PII mappings (for security)"""
        self.pii_mapping = {}
        self.masked_to_original = {}
        self.original_to_masked = {}
        self.mapping_session_id = None
        self.mapping_timestamp = None
        
        logger.info("🗑️ SecurityGuard: Cleared all PII mappings")
    
    def validate_sql(self, sql: str, user: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[bool, str, str]:
        """Validate SQL for security issues with detailed analysis"""
        try:
            sql_upper = sql.upper().strip()
            guards_applied = {}
            total_guards = 0
            
            # Check for dangerous patterns (only these should trigger guards)
            dangerous_operations = [
                ("DROP", r"DROP\s+(TABLE|DATABASE|INDEX|VIEW|TRIGGER|PROCEDURE|FUNCTION)"),
                ("DELETE", r"DELETE\s+FROM"),
                ("TRUNCATE", r"TRUNCATE\s+TABLE"),
                ("ALTER", r"ALTER\s+TABLE"),
                ("CREATE", r"CREATE\s+(TABLE|DATABASE|INDEX|VIEW|TRIGGER|PROCEDURE|FUNCTION)"),
                ("INSERT", r"INSERT\s+INTO"),
                ("UPDATE", r"UPDATE\s+SET"),
                ("GRANT", r"GRANT\s+"),
                ("REVOKE", r"REVOKE\s+"),
                ("EXEC", r"EXEC\s+"),
                ("EXECUTE", r"EXECUTE\s+"),
                ("SHUTDOWN", r"SHUTDOWN"),
                ("KILL", r"KILL"),
                ("BACKUP", r"BACKUP\s+DATABASE"),
                ("RESTORE", r"RESTORE\s+DATABASE")
            ]
            
            # Check for dangerous operations
            for operation, pattern in dangerous_operations:
                if re.search(pattern, sql_upper, re.IGNORECASE):
                    guards_applied[f"{operation}_DETECTED"] = f"⚠️ Dangerous {operation} operation detected"
                    total_guards += 1
                    self._log_security_event(
                        "dangerous_operation_detected", user, ip_address, 
                        sql_query=sql, threat_level="HIGH", 
                        action_taken="BLOCKED", 
                        details=f"Dangerous {operation} operation detected"
                    )
                    return False, f"⚠️ Dangerous {operation} operation detected", "BLOCKED"
            
            # Check for suspicious patterns (warn but don't block)
            suspicious_patterns = [
                ("UNION", r"UNION\s+SELECT"),
                ("OR_INJECTION", r"OR\s+1\s*=\s*1"),
                ("OR_TRUE", r"OR\s+TRUE"),
                ("SCRIPT_TAG", r"<script"),
                ("JAVASCRIPT", r"javascript:"),
                ("ONLOAD", r"onload="),
                ("ONERROR", r"onerror=")
            ]
            
            for pattern_name, pattern in suspicious_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    guards_applied[f"{pattern_name}_DETECTED"] = f"⚠️ Suspicious {pattern_name} pattern detected"
                    total_guards += 1
                    self._log_security_event(
                        "suspicious_pattern", user, ip_address,
                        sql_query=sql, threat_level="MEDIUM",
                        action_taken="FLAGGED",
                        details=f"Suspicious pattern detected: {pattern_name}"
                    )
            
            # If no dangerous operations found, return success with no guards
            if total_guards == 0:
                # Log successful validation (no guards needed)
                self._log_security_event(
                    "sql_validated", user, ip_address,
                    sql_query=sql, threat_level="LOW",
                    action_taken="ALLOWED",
                    details="SQL validation passed - no dangerous operations detected"
                )
                return True, "SQL validation passed", "ALLOWED"
            else:
                # Return success but with guards applied
                return True, f"Query processed with {total_guards} security guard(s) applied", "GUARDED"
            
        except Exception as e:
            logger.error(f"❌ SQL validation error: {e}")
            return False, f"Validation error: {str(e)}", "ERROR"
    
    def validate_query(self, query: str, user: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Validate natural language query"""
        try:
            # Basic validation
            if len(query.strip()) == 0:
                return False, "Empty query"
            
            if len(query) > 1000:
                return False, "Query too long"
            
            # Check for suspicious content
            suspicious_terms = [
                "password", "admin", "root", "system", "config", "secret",
                "delete", "drop", "truncate", "alter", "create", "insert", "update"
            ]
            
            query_lower = query.lower()
            for term in suspicious_terms:
                if term in query_lower:
                    self._log_security_event(
                        "suspicious_query_term", user, ip_address,
                        query=query, threat_level="LOW",
                        action_taken="FLAGGED",
                        details=f"Suspicious term detected: {term}"
                    )
                    return True, f"Query flagged for review: contains '{term}'"
            
            return True, "Query validation passed"
            
        except Exception as e:
            logger.error(f"❌ Query validation error: {e}")
            return False, f"Validation error: {str(e)}"
    
    def check_permissions(self, user: str, operation: str, resource: Optional[str] = None) -> bool:
        """Check user permissions for operations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user permissions
            cursor.execute('''
                SELECT permissions FROM user_permissions 
                WHERE user = ? AND role = ?
            ''', (user, "default"))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                permissions = json.loads(result[0])
                return operation in permissions.get("allowed_operations", [])
            
            # Default permissions for new users
            return operation in ["SELECT", "COUNT", "SUM", "AVG", "MAX", "MIN"]
            
        except Exception as e:
            logger.error(f"❌ Permission check error: {e}")
            return False
    
    def check_rate_limit(self, ip_address: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check rate limiting for IP address"""
        with self._lock:
            now = datetime.now()
            
            # Clean up expired entries
            self.rate_limits = {
                ip: data for ip, data in self.rate_limits.items()
                if data['reset_time'] > now
            }
            
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                return False
            
            # Get current rate limit data
            if ip_address not in self.rate_limits:
                self.rate_limits[ip_address] = {
                    'count': 0,
                    'reset_time': now + timedelta(minutes=window_minutes)
                }
            
            data = self.rate_limits[ip_address]
            
            # Check if window has reset
            if now > data['reset_time']:
                data['count'] = 0
                data['reset_time'] = now + timedelta(minutes=window_minutes)
            
            # Increment count
            data['count'] += 1
            
            # Check if limit exceeded
            if data['count'] > max_requests:
                self._block_ip(ip_address, f"Rate limit exceeded: {data['count']} requests")
                return False
            
            return True
    
    def _block_ip(self, ip_address: str, reason: str, duration_hours: int = 24):
        """Block an IP address"""
        try:
            with self._lock:
                self.blocked_ips.add(ip_address)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO blocked_ips 
                (ip_address, blocked_at, reason, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (
                ip_address,
                datetime.now().isoformat(),
                reason,
                expires_at
            ))
            
            conn.commit()
            conn.close()
            
            self._log_security_event(
                "ip_blocked", None, ip_address,
                threat_level="HIGH",
                action_taken="BLOCKED",
                details=f"IP blocked: {reason}"
            )
            
            logger.warning(f"⚠️ IP {ip_address} blocked: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Failed to block IP {ip_address}: {e}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        with self._lock:
            return ip_address in self.blocked_ips
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        try:
            with self._lock:
                self.blocked_ips.discard(ip_address)
            
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM blocked_ips WHERE ip_address = ?', (ip_address,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ IP {ip_address} unblocked")
            
        except Exception as e:
            logger.error(f"❌ Failed to unblock IP {ip_address}: {e}")
    
    def _log_security_event(self, event_type: str, user: Optional[str], ip_address: Optional[str],
                           query: Optional[str] = None, sql_query: Optional[str] = None,
                           threat_level: str = "LOW", action_taken: str = "LOGGED",
                           details: Optional[str] = None):
        """Log security events to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_events 
                (timestamp, event_type, user, ip_address, query, sql_query, 
                 threat_level, action_taken, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                event_type,
                user,
                ip_address,
                query,
                sql_query,
                threat_level,
                action_taken,
                details
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to log security event: {e}")
    
    def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive security report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Total events
            cursor.execute('SELECT COUNT(*) FROM security_events WHERE timestamp > ?', (cutoff_time,))
            total_events = cursor.fetchone()[0]
            
            # Events by type
            cursor.execute('''
                SELECT event_type, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY event_type
                ORDER BY count DESC
            ''', (cutoff_time,))
            events_by_type = dict(cursor.fetchall())
            
            # Events by threat level
            cursor.execute('''
                SELECT threat_level, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY threat_level
            ''', (cutoff_time,))
            events_by_threat = dict(cursor.fetchall())
            
            # Top blocked IPs
            cursor.execute('''
                SELECT ip_address, COUNT(*) as count 
                FROM security_events 
                WHERE timestamp > ? AND action_taken = 'BLOCKED'
                GROUP BY ip_address 
                ORDER BY count DESC 
                LIMIT 10
            ''', (cutoff_time,))
            top_blocked_ips = dict(cursor.fetchall())
            
            # Currently blocked IPs
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE expires_at > ?', (datetime.now().isoformat(),))
            currently_blocked = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'period_hours': hours,
                'total_events': total_events,
                'events_by_type': events_by_type,
                'events_by_threat': events_by_threat,
                'top_blocked_ips': top_blocked_ips,
                'currently_blocked_ips': currently_blocked,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate security report: {e}")
            return {}
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM security_events 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                events.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'user': row[3],
                    'ip_address': row[4],
                    'query': row[5],
                    'sql_query': row[6],
                    'threat_level': row[7],
                    'action_taken': row[8],
                    'details': row[9]
                })
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent events: {e}")
            return []
    
    def clear_security_logs(self, days: int = 30):
        """Clear security logs older than specified days"""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM security_events WHERE timestamp < ?', (cutoff_time,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Cleared {deleted_count} old security logs")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear security logs: {e}")
            raise
    
    def export_security_data(self, format: str = "json", hours: int = 24) -> str:
        """Export security data in specified format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT * FROM security_events 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                events.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'event_type': row[2],
                    'user': row[3],
                    'ip_address': row[4],
                    'query': row[5],
                    'sql_query': row[6],
                    'threat_level': row[7],
                    'action_taken': row[8],
                    'details': row[9]
                })
            
            if format.lower() == "json":
                return json.dumps(events, indent=2)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['ID', 'Timestamp', 'Event Type', 'User', 'IP Address', 
                               'Query', 'SQL Query', 'Threat Level', 'Action Taken', 'Details'])
                
                # Write data
                for event in events:
                    writer.writerow([
                        event['id'],
                        event['timestamp'],
                        event['event_type'],
                        event['user'] or '',
                        event['ip_address'] or '',
                        event['query'] or '',
                        event['sql_query'] or '',
                        event['threat_level'],
                        event['action_taken'],
                        event['details'] or ''
                    ])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export security data: {e}")
            raise
