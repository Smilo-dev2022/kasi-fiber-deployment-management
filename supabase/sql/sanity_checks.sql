-- Sanity checks. Some queries may require tables to exist.

-- Counts
SELECT count(*) AS wards FROM geo_wards;
SELECT count(*) AS suburbs FROM geo_suburbs;
SELECT count(*) AS poles_geo FROM poles WHERE geom_geojson IS NOT NULL;
SELECT count(*) AS closures_geo FROM closures WHERE geom_geojson IS NOT NULL;
SELECT count(*) AS cables_geo FROM cable_register WHERE geom_geojson IS NOT NULL;
SELECT count(*) AS pons_geo FROM pons WHERE geofence IS NOT NULL;

-- Validate geometry
SELECT id FROM geo_wards WHERE ST_IsValid(ST_GeomFromWKB(geom)) = false LIMIT 10;
SELECT id FROM geo_suburbs WHERE ST_IsValid(ST_GeomFromWKB(geom)) = false LIMIT 10;

-- Optional: Photo geofence test on 20 random photos (requires v_photos, v_pons, photos views)
-- SELECT ph.id, ST_Contains(vp.geofence_geom, vp2.gps_geom) AS inside
-- FROM v_photos vp2
-- JOIN v_pons vp ON vp.id = vp2.pon_id
-- JOIN photos ph ON ph.id = vp2.id
-- WHERE vp2.gps_geom IS NOT NULL AND vp.geofence_geom IS NOT NULL
-- LIMIT 20;

