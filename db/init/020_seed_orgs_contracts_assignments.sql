-- Orgs
insert into organizations (id, name, type) values
(gen_random_uuid(), 'Main Civil Co', 'Civil'),
(gen_random_uuid(), 'Tech Splice Co', 'Technical'),
(gen_random_uuid(), 'Maint Ops Co', 'Maintenance');

-- Contracts
insert into contracts (id, org_id, scope, wards, sla_minutes_p1, sla_minutes_p2, sla_minutes_p3, sla_minutes_p4)
select gen_random_uuid(), id, 'Maintenance', array['48','49'], 120, 240, 1440, 4320 from organizations where name='Maint Ops Co';

-- Assignments by ward
insert into assignments (id, org_id, scope, ward, priority)
select gen_random_uuid(), id, 'Civil', '48', 10 from organizations where name='Main Civil Co';
insert into assignments (id, org_id, scope, ward, priority)
select gen_random_uuid(), id, 'Technical', '48', 10 from organizations where name='Tech Splice Co';

