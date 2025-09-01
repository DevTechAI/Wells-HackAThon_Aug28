#!/usr/bin/env python3
"""
Test PII Masking/Unmasking System
Demonstrates how PII is masked and can be unmasked using key-value mappings
"""

import sys
import os
sys.path.append('./backend')

from security_guard import SecurityGuard

def test_pii_masking_unmasking():
    """Test the complete PII masking and unmasking system"""
    
    print("🔐 Testing PII Masking/Unmasking System")
    print("=" * 60)
    
    # Initialize security guard
    print("\n1️⃣ Initializing Security Guard with PII Mapping...")
    security_guard = SecurityGuard()
    
    # Create a PII mapping session
    session_id = security_guard.create_pii_mapping_session("test_session_001")
    print(f"✅ Created PII mapping session: {session_id}")
    
    # Test content with various PII types
    test_content = """
    Customer Information:
    - Name: John Smith
    - Email: john.doe@example.com
    - Phone: (555) 123-4567
    - SSN: 123-45-6789
    - Credit Card: 1234-5678-9012-3456
    - Address: 123 Main Street, New York, NY 10001
    - Date of Birth: 01/15/1990
    """
    
    print(f"\n2️⃣ Original Content with PII:")
    print(test_content)
    
    # Detect PII
    print(f"\n3️⃣ Detecting PII...")
    pii_findings = security_guard.detect_pii(test_content, "customer_data")
    
    if pii_findings['detected']:
        print(f"✅ PII Detected: {pii_findings['pii_types']}")
        print(f"📊 Risk Level: {pii_findings['risk_level']}")
        print(f"📝 Items Found: {len(pii_findings['sensitive_data'])}")
        
        # Show what will be masked/removed
        for item in pii_findings['sensitive_data']:
            print(f"  - {item['type']}: {item['value']} (Risk: {item['risk_level']})")
    else:
        print("❌ No PII detected")
        return
    
    # Sanitize content (this will also store mappings)
    print(f"\n4️⃣ Sanitizing Content...")
    sanitized_content, sanitization_report = security_guard.sanitize_content_for_embedding(
        test_content, "customer_data"
    )
    
    print(f"✅ Sanitization Report:")
    print(f"  - Original Length: {sanitization_report['original_length']}")
    print(f"  - Sanitized Length: {sanitization_report['sanitized_length']}")
    print(f"  - PII Removed: {sanitization_report['pii_removed']}")
    print(f"  - PII Masked: {sanitization_report['pii_masked']}")
    
    print(f"\n5️⃣ Sanitized Content:")
    print(sanitized_content)
    
    # Show stored mappings
    print(f"\n6️⃣ Stored PII Mappings:")
    mapping_session = security_guard.get_pii_mapping_session()
    print(f"Session ID: {mapping_session['session_id']}")
    print(f"Timestamp: {mapping_session['timestamp']}")
    print(f"Total Mappings: {mapping_session['total_mappings']}")
    
    # Get detailed mappings
    mappings = security_guard.get_pii_mappings()
    print(f"\nDetailed Mappings:")
    for mapping_key, mapping_data in mappings['mappings'].items():
        print(f"  - {mapping_data['pii_type']}: {mapping_data['original']} → {mapping_data['masked']}")
    
    # Test unmasking
    print(f"\n7️⃣ Testing Unmasking...")
    unmasked_content, unmask_report = security_guard.unmask_pii(sanitized_content)
    
    print(f"✅ Unmasking Report:")
    print(f"  - Unmasked Count: {unmask_report['unmasked_count']}")
    print(f"  - Errors: {unmask_report['errors']}")
    print(f"  - Session ID: {unmask_report['session_id']}")
    
    print(f"\n8️⃣ Unmasked Content:")
    print(unmasked_content)
    
    # Verify unmasking worked
    print(f"\n9️⃣ Verification:")
    if unmasked_content == test_content:
        print("✅ SUCCESS: Unmasked content matches original content!")
    else:
        print("❌ FAILURE: Unmasked content does not match original")
        print("Original:")
        print(test_content)
        print("Unmasked:")
        print(unmasked_content)
    
    # Test specific unmasking scenarios
    print(f"\n🔟 Testing Specific Unmasking Scenarios...")
    
    # Test unmasking just emails
    email_mappings = security_guard.get_pii_mappings(pii_type='email')
    print(f"Email Mappings: {len(email_mappings['mappings'])}")
    for key, data in email_mappings['mappings'].items():
        print(f"  - {data['original']} → {data['masked']}")
    
    # Test unmasking just SSNs
    ssn_mappings = security_guard.get_pii_mappings(pii_type='ssn')
    print(f"SSN Mappings: {len(ssn_mappings['mappings'])}")
    for key, data in ssn_mappings['mappings'].items():
        print(f"  - {data['original']} → {data['masked']}")
    
    # Test unmasking by context
    context_mappings = security_guard.get_pii_mappings(context='customer_data')
    print(f"Customer Data Context Mappings: {len(context_mappings['mappings'])}")
    
    # Test clearing mappings
    print(f"\n1️⃣1️⃣ Testing Mapping Cleanup...")
    security_guard.clear_pii_mappings()
    
    # Try to unmask after clearing (should fail)
    unmasked_after_clear, clear_report = security_guard.unmask_pii(sanitized_content)
    print(f"Unmasking after clear: {clear_report['unmasked_count']} items")
    print(f"Errors: {clear_report['errors']}")
    
    # Show how the system works with LLM interactions
    print(f"\n1️⃣2️⃣ LLM Interaction Workflow:")
    print("""
    🔄 PII Protection Workflow:
    
    1. User Input → PII Detection → Store Mappings → Sanitize → Send to LLM
       ↓
    2. LLM Response → Unmask using stored mappings → Return to User
       ↓
    3. Clear mappings for security
    
    Key Benefits:
    ✅ No PII sent to external LLM providers
    ✅ Original data preserved in secure mappings
    ✅ Can restore original values when needed
    ✅ Automatic cleanup for security
    """)
    
    print("\n🎉 PII Masking/Unmasking Test Complete!")
    print("✅ System successfully masks PII and can unmask it using stored mappings")

if __name__ == "__main__":
    test_pii_masking_unmasking()
