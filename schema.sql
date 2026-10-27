-- Supabase -> SQL Editor me ye paste karke Run karo
create table if not exists rules (
  id bigint generated always as identity primary key,
  media_id text unique not null,      -- reel ki id, ya '*' = default rule
  keyword text default '',            -- comma se alag: link,price (khali = har comment)
  reply_text text default '',         -- public reply (kai options ho to naye line me likho)
  dm_text text default '',            -- DM ka message
  active boolean default true,
  created_at timestamptz default now()
);
