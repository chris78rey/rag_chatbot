# State Management & Verification (Subproject 10)

## Overview

Subproject 10 implements state management and verification for the RAF Chatbot system. This ensures that the system maintains expected invariants across all services and components, providing visibility into system health and readiness.

## Objectives

- **State Tracking**: Monitor and document the expected state of all services and components
- **Verification**: Provide read-only scripts to verify current state matches expected state
- **Observability**: Enable operators to detect state drift and misconfigurations
- **Documentation**: Maintain clear records of system invariants and constraints

## Architecture

### Components

1. **State Definition** (`scripts/state_expected.json`)
   - JSON file defining expected system state
   - Includes service configuration, metrics, integrations, and constraints
   - Single source of truth for state validation

2. **State Verification** (`scripts/verify_state.py`)
   - Read-only Python script that checks current state against expected state
   - Validates API health, Qdrant connectivity, metrics availability
   - Reports errors and warnings
   - Returns exit code 0 (STATE_OK) or 1 (STATE_FAIL)

3. **Documentation** (`docs/state_management.md`)
   - This file: guides for operators and developers

## Expected State Definition

The `scripts/state_expected.json` file defines:

### Services
- **API Service**
  - Port: 8000 (mapped to 8001 on host)
  - Endpoints: `/health`, `/query`, `/metrics`
  - Status: healthy

- **Qdrant Service**
  - Port: 6333
  - Collections: `documents` with vector_size 384
  - Status: healthy

- **Nginx (Reverse Proxy)**
  - Port: 80
  - Route: `/api` → API service

### Observability
- **Metrics Endpoint**: `/metrics`
- **Required Metrics**:
  - `requests_total`: Counter of total requests
  - `errors_total`: Counter of total errors
  - `avg_latency_ms`: Average request latency
  - `p95_latency_ms`: 95th percentile latency

### Integrations
- **LLM**: OpenRouter with fallback enabled
- **Vector DB**: Qdrant connected and ready

### Constraints
- **Max P95 Latency**: 5000ms
- **Min Availability**: 95%
- **Max Error Rate**: 5%

## Verification Process

### Running State Verification

```bash
cd G:\zed_projects\raf_chatbot
python scripts/verify_state.py
```

### Verification Checks

The script performs the following checks:

1. **API Health Check**
   - Calls `GET /health`
   - Expects HTTP 200
   - Confirms API service is running

2. **API Endpoints Check**
   - Validates `/query` and `/metrics` are accessible
   - Confirms endpoints are registered and responding

3. **Metrics Availability Check**
   - Calls `GET /metrics`
   - Verifies all required metrics are present
   - Confirms observability is configured

4. **Qdrant Health Check**
   - Calls `GET /health`
   - Expects HTTP 200
   - Confirms Qdrant service is running

5. **Qdrant Collection Check**
   - Lists collections via `GET /collections`
   - Verifies `documents` collection exists
   - Confirms vector database is seeded

6. **System Constraints Check**
   - Parses metrics and compares against constraints
   - Warns if p95_latency_ms exceeds threshold
   - Warns if error rates approach limit

### Output Format

```
STATE VERIFICATION REPORT
========================================================
✓ PASS: API Health
✓ PASS: API Endpoints
✓ PASS: Metrics Availability
✓ PASS: Qdrant Health
✓ PASS: Qdrant Collection
✓ PASS: System Constraints

ERRORS:
  (none if all pass)

WARNINGS:
  (warnings if thresholds approached)

========================================================
FINAL STATUS: STATE_OK
========================================================
```

### Exit Codes

- **0 (STATE_OK)**: All checks passed, system is in expected state
- **1 (STATE_FAIL)**: One or more checks failed, system state is invalid

## Integration Points

### Manual Verification
Operators can run verification manually before deployments:

```bash
python scripts/verify_state.py
```

### Pre-Deployment Checklist
1. Run state verification
2. Confirm STATE_OK output
3. Proceed with deployment

### CI/CD Integration
Include in your CI pipeline:

```yaml
- name: Verify System State
  run: python scripts/verify_state.py
  condition: always  # Run even if previous steps fail
```

### Continuous Monitoring
In production, consider:
- Running verification on a schedule (e.g., every 5 minutes)
- Alerting on STATE_FAIL
- Tracking state transitions in logs
- Collecting metrics for SLO tracking

## Troubleshooting

### Common Issues

#### STATE_FAIL: API Health
- **Cause**: API service not running or unreachable
- **Solution**: 
  ```bash
  docker compose ps
  docker compose logs api
  docker compose restart api
  ```

#### STATE_FAIL: Qdrant Health
- **Cause**: Qdrant service not running
- **Solution**:
  ```bash
  docker compose ps
  docker compose logs qdrant
  docker compose restart qdrant
  ```

#### STATE_FAIL: Qdrant Collection
- **Cause**: `documents` collection not seeded
- **Solution**:
  ```bash
  python scripts/seed_demo_data.py
  ```

#### STATE_FAIL: Metrics Availability
- **Cause**: `/metrics` endpoint not responding with required metrics
- **Solution**:
  - Verify API is running
  - Check observability module is imported in `main.py`
  - Review `services/api/app/observability.py`

#### STATE_FAIL: Cannot Connect
- **Cause**: Port mappings incorrect or services not exposed
- **Solution**:
  - Verify `docker-compose.yml` has correct port mappings
  - Check firewall rules allow access to ports 8001, 6333
  - Run from project root directory where `docker-compose.yml` exists

### Debug Mode

For more detailed output:

```bash
# Add debug logging
export LOG_LEVEL=DEBUG
python scripts/verify_state.py
```

## Best Practices

### Operators
1. **Before Deployment**: Always run state verification
2. **After Restarts**: Verify state before resuming traffic
3. **On Alerts**: Run verification to diagnose issues
4. **Regular Checks**: Schedule periodic verification (daily/weekly)

### Developers
1. **After Changes**: Verify state isn't broken by your changes
2. **Before PR**: Ensure state verification passes
3. **Add Tests**: Include state checks in test suite
4. **Update Constraints**: Adjust thresholds if behavior changes

### DevOps
1. **Automation**: Add to deployment pipelines
2. **Monitoring**: Integrate with alerting systems
3. **Dashboards**: Track state_ok vs state_fail over time
4. **Alerting**: Send alerts when STATE_FAIL is detected

## Future Enhancements

### Phase 2
- JSON output format for parsing in tools
- Detailed state report with component metrics
- State history tracking
- Drift detection and alerts

### Phase 3
- Automated remediation (e.g., restart failed services)
- Predictive health checks
- Integration with APM tools (DataDog, New Relic)
- Custom metric thresholds per environment

## References

- [Observability Documentation](./observability.md)
- [Docker Compose Configuration](../docker-compose.yml)
- [API Routes](../services/api/app/routes/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

## Summary

State Management & Verification (SP10) provides operators with a clear, automated way to verify system health. The read-only verification script ensures no side effects while giving full visibility into system state, enabling confident deployments and rapid issue diagnosis.