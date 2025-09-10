-- Idempotent seed for organizations, contracts, assignments
insert into organizations (id, tenant_id, name, type)
values ('00000000-0000-0000-0000-0000000000a1', null, 'Alpha Civils', 'Civil')
on conflict (id) do nothing;

insert into organizations (id, tenant_id, name, type)
values ('00000000-0000-0000-0000-0000000000b2', null, 'Bravo Technical', 'Technical')
on conflict (id) do nothing;

insert into contracts (id, tenant_id, org_id, scope_type, wards, sla_p1_min, sla_p2_min, sla_p3_min, sla_p4_min, valid_from, active)
values ('00000000-0000-0000-0000-0000000000c3', null, '00000000-0000-0000-0000-0000000000b2', 'Technical', null, 60, 180, 480, 1440, current_date, true)
on conflict (id) do nothing;

insert into assignments (id, tenant_id, org_id, pon_id, ward, step_type)
values ('00000000-0000-0000-0000-0000000000d4', null, '00000000-0000-0000-0000-0000000000b2', null, null, 'Technical')
on conflict (id) do nothing;

