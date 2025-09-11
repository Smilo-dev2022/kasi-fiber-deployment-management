-- Sample seed data
insert into tenants (id, name) values ('acme', 'Acme Corp') on conflict do nothing;
insert into users (id, tenant_id, email) values ('u_acme_admin', 'acme', 'admin@acme.com') on conflict do nothing;