import type { PoolClient } from 'pg';

type AuditInput = {
  actorUserId: string | null;
  action: string;
  entity?: string | null;
  entityId?: string | null;
  metadata?: any;
  ip?: string | null;
};

export async function audit(client: PoolClient, tenantId: string, input: AuditInput) {
  await client.query(
    `insert into audit_logs (tenant_id, actor_user_id, action, entity, entity_id, metadata, ip)
     values ($1, $2, $3, $4, $5, $6, $7)`,
    [tenantId, input.actorUserId, input.action, input.entity ?? null, input.entityId ?? null, input.metadata ?? {}, input.ip ?? null]
  );
}

