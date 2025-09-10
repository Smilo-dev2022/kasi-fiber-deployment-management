# NOC Playbooks

## Device Down (P1)
1. Auto-incident from NMS webhook (severity map sets P1)
2. Auto-assign to Technical contractor via `assignments`
3. SLA set from `contracts` -> due_at
4. Page on-call; acknowledge within 15 minutes
5. Verify power/optical; escalate to field if unresolved

## Optical Degradation (P2/P3)
1. Validate alarms; check LOS/BER
2. Trigger OTDR/LSPM test plan if required
3. If threshold exceeded, dispatch splicing team

## Power Failure (P2)
1. Confirm site power status; engage facilities
2. Track generator deployment if applicable