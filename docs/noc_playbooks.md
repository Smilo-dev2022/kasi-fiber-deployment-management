## NOC Playbooks

Playbooks for common incident categories. Customize per tenant and environment.

### Device Down (P1)
- Identify impacted OLT/ONT/SWITCH. Verify via NMS.
- Auto-created incident should be assigned to NOC.
- Acknowledge within 5 minutes. Dispatch field if no remote restore in 15 minutes.
- Due: per contract P1 SLA.

### Optical Low Power (P2)
- Check historical readings and recent splices.
- Assign to Technical contractor for OTDR/LSPM testing.
- Due: per contract P2 SLA.

### Power Failure (P2/P3)
- Confirm grid status, UPS runtime.
- Notify Facilities; if UPS fault, raise maintenance task.

### Capacity Threshold (P3/P4)
- Review utilization trend. Plan augmentation.

Escalation follows the matrix in `docs/escalation_matrix.md`.

