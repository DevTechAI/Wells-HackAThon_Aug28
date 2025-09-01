# PII Scanning Toggle Feature

## Overview
The PII (Personally Identifiable Information) scanning feature can be toggled on/off to balance between security and performance during application initialization.

## Why Toggle PII Scanning?

### When PII Scanning is ENABLED (Default):
- ✅ **Security**: Detects and protects sensitive data (emails, phone numbers, SSNs, credit cards)
- ✅ **Compliance**: Helps meet privacy regulations
- ✅ **Protection**: Automatically masks/removes PII before sending to external LLMs
- ❌ **Performance**: Slows down initialization due to content scanning

### When PII Scanning is DISABLED:
- ⚡ **Speed**: Faster application startup
- ⚡ **Performance**: No content scanning overhead
- ⚡ **Development**: Useful for development and testing
- ⚠️ **Security**: No PII protection (use only in trusted environments)

## How to Toggle PII Scanning

### Method 1: Using the Toggle Utility (Recommended)

```bash
# Check current status
python toggle_pii_scanning.py status

# Toggle PII scanning on/off
python toggle_pii_scanning.py
```

### Method 2: Manual Environment Variable

Create or update your `.env` file:

```bash
# To DISABLE PII scanning (faster startup)
ENABLE_PII_SCANNING=false

# To ENABLE PII scanning (default, more secure)
ENABLE_PII_SCANNING=true
```

## What Gets Scanned

When PII scanning is enabled, the system scans for:

### High Risk (Automatically Removed):
- 🔴 Social Security Numbers (SSN)
- 🔴 Credit Card Numbers

### Medium Risk (Automatically Masked):
- 🟡 Email Addresses
- 🟡 Phone Numbers
- 🟡 Dates of Birth

### Low Risk (Logged but Preserved):
- 🟢 Physical Addresses
- 🟢 Names

## Performance Impact

### With PII Scanning ENABLED:
- Schema initialization: ~30-60 seconds
- Content processing: ~10-20 seconds per large document
- Memory usage: +15-25% due to pattern matching

### With PII Scanning DISABLED:
- Schema initialization: ~10-20 seconds
- Content processing: ~2-5 seconds per large document
- Memory usage: Baseline

## Security Recommendations

### For Development/Testing:
```bash
ENABLE_PII_SCANNING=false
```

### For Production:
```bash
ENABLE_PII_SCANNING=true
```

### For Staging/QA:
```bash
ENABLE_PII_SCANNING=true
```

## Monitoring PII Detection

When PII scanning is enabled, the application will:

1. **Display Status**: Show whether PII scanning is enabled/disabled
2. **Log Findings**: Record all PII detection events
3. **Show Metrics**: Display counts of detected PII types
4. **Provide Recommendations**: Suggest security measures

## Example Output

### PII Scanning Enabled:
```
🔒 PII scanning is enabled - checking for sensitive data...
⚠️ PII (Personally Identifiable Information) detected during schema processing!
Total PII Findings: 5
High Risk Items: 2
Medium Risk Items: 3
```

### PII Scanning Disabled:
```
⚡ PII scanning is disabled - initialization completed faster
💡 To enable PII scanning, set ENABLE_PII_SCANNING=true in your .env file
```

## Troubleshooting

### PII Scanning Not Working:
1. Check if `.env` file exists
2. Verify `ENABLE_PII_SCANNING=true` is set
3. Restart the application after changing the setting

### Performance Still Slow:
1. Ensure `ENABLE_PII_SCANNING=false` is set
2. Check for other performance bottlenecks
3. Monitor system resources during initialization

## Best Practices

1. **Development**: Use `ENABLE_PII_SCANNING=false` for faster iteration
2. **Testing**: Use `ENABLE_PII_SCANNING=true` to test security features
3. **Production**: Always use `ENABLE_PII_SCANNING=true`
4. **Documentation**: Keep track of which environments have PII scanning enabled
5. **Monitoring**: Regularly check PII detection logs in production
