CREATE TABLE public.tasks
(
    id bigserial,
    userid bigint NOT NULL,
    title character varying,
    description character varying,
    status character varying DEFAULT 'pending',
    priority bigint DEFAULT 1,
    due_date timestamp without time zone,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.tasks
    OWNER to postgres;

CREATE TABLE public.chat_sessions
(
    session_id bigserial,
    user_id bigint NOT NULL,
    created_at timestamp without time zone,
    PRIMARY KEY (session_id)
);

ALTER TABLE IF EXISTS public.chat_sessions
    OWNER to postgres;

CREATE TABLE public.messages
(
    id bigserial,
    session_id bigint,
    role character varying NOT NULL,
    content character varying,
    msg_time timestamp without time zone,
    PRIMARY KEY (id),
    CONSTRAINT session FOREIGN KEY (session_id)
        REFERENCES public.chat_sessions (session_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
);

ALTER TABLE IF EXISTS public.messages
    OWNER to postgres;

CREATE TABLE public.knowledge_base
(
    id bigserial,
    user_id bigint,
    content character varying,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.knowledge_base
    OWNER to postgres;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE public.knowledge_base 
ADD COLUMN embedding vector(1536);

ALTER TABLE knowledge_base ALTER COLUMN embedding TYPE vector(768);

CREATE TABLE public.users
(
    userid bigserial,
    email character varying NOT NULL,
    password character varying,
    created_at timestamp without time zone DEFAULT NOW(),
    PRIMARY KEY (userid)
);

ALTER TABLE IF EXISTS public.users
    OWNER to postgres;

ALTER TABLE IF EXISTS public.tasks
    ADD CONSTRAINT userid FOREIGN KEY (userid)
    REFERENCES public.users (userid) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS public.knowledge_base
    ADD CONSTRAINT userid FOREIGN KEY (user_id)
    REFERENCES public.users (userid) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;