-- Minimal seed data for local development
insert into client(name) values ('Demo Client') on conflict do nothing;

-- Create a default ward linked to the demo client
insert into ward(client_id, name)
select id, 'Ward 1' from client where name='Demo Client'
on conflict do nothing;

