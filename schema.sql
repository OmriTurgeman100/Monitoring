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

alter table routes_metrics
add column log text,
add column type text;

alter table routes_metrics
alter column created_at type timestamptz
using created_at at time zone 'UTC';

ALTER TABLE routes_metrics
ADD COLUMN latency DOUBLE PRECISION;