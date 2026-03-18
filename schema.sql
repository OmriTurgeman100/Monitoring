create database monitoring;

create table if not exists http (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text not null unique,
    type text not null check (type in ('system', 'service'))
);

create table if not exists routes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent BIGINT references http(id),
    route text not null,
    description text,
    desired_time int not null
);

create table if not exists routes_metrics (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent BIGINT references routes(id),
    value int not null,
    created_at timestamp default now()
);

