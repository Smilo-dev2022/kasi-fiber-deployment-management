# One Page Pilot Checklist

## Scope
- One ward
- One OLT site
- Two contractors Civil and Technical
- One Maintenance partner

## Day -3
- Create staging tenant
- Load `.env.staging` and run migrations
- Seed users with roles `PMO`, `NOC`, `CivilLead`, `SpliceLead`, `MaintenanceTech`
- Seed five PONs with geofences
- Import devices and link to PONs
- Create contracts and assignments by ward

## Day -2
- Configure NMS webhooks with HMAC and IP allowlist
- Send four test alerts: device down, LOS, low power, clear
- Verify incidents route and due times set
- Build WhatsApp or email alerts for P1 and P2

## Day -1
- Stock in system: poles, brackets, ducts, drums
- Print QR labels for poles and drums
- Train field teams on photo GPS rules
- Dry run photo upload and EXIF validation
- Create TestPlans per PON

## Day 0 start
- Kick off build on one PON
- Capture photos for Dig, Plant, CAC, Stringing
- Scan assets on issue and install
- Log floating run and splicing on first closure
- Record OTDR and LSPM against the plan

## Daily during pilot
- 09:00 standup. Review SLA breaches and blockers
- 12:00 NOC check. New incidents and routing
- 15:00 field audit. Random photo and GPS spot checks
- Close tasks with before and after readings and photos
- Update dashboards PMO, NOC, Finance

## Data to capture every day
- Poles planted, meters strung, trench meters, chambers
- Splices done and average loss per tray
- OTDR and LSPM results pass or fail
- Incidents MTTA, MTTR, repeats
- Stock issues and returns

## Quality gates
- CAC first pass 90 percent or higher
- Average splice loss per tray under 0.15 dB
- LSPM within plan budget
- Photos pass EXIF and geofence 95 percent or higher

## Finance checks
- Generate weekly pay sheets per SMME
- Export PDFs and verify totals vs rate cards
- Block invoices where tests or photos fail

## Exit criteria after two weeks
- Uptime report and MTTR within targets
- Zero P1 without page alert
- Test pack PDF per completed PON
- No cross org data access issues
- Sign off by PMO and NOC leads

## Rollback plan
- Keep daily DB backups
- Feature flags ready to disable routing or validation if needed
- Known good build tag noted for quick revert