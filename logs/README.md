# Domain Management CLI Logs Directory

This directory contains application log files:

- `domain-cli.log` - Main application log with all levels
- `domain-cli-errors.log` - Error-only log for critical issues

Log files are automatically rotated when they reach 10MB (main) / 5MB (error) with 5/3 backup files retained.

## Log Format

```
TIMESTAMP | LEVEL    | COMPONENT        | CORRELATION_ID | MESSAGE
```

Example:
```
2025-01-20 10:30:45 | INFO     | domain-cli.database  | abc12345     | DB | SELECT | 15.23ms | 5 rows | SELECT d.fqdn FROM domain...
```

## Environment Configuration

Configure logging via environment variables:
- `LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `LOG_TO_FILE` - true/false (default: true)
- `LOG_TO_CONSOLE` - true/false (default: true)