CREATE REL TABLE hyprlink(FROM links TO links, session_id STRING);
CREATE NODE TABLE links(linkid SERIAL PRIMARY KEY, link STRING, session_id STRING);
