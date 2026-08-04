--
-- PostgreSQL database dump
--


-- Dumped from database version 15.18 (Debian 15.18-1.pgdg13+1)
-- Dumped by pg_dump version 15.18 (Debian 15.18-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: status; Type: TYPE; Schema: public; Owner: wwwanalys_user
--

CREATE TYPE public.status AS ENUM (
    'PENDING',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED'
);


ALTER TYPE public.status OWNER TO wwwanalys_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analysis_plans; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.analysis_plans (
    id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    plan_date date NOT NULL,
    created_by integer,
    created_at timestamp without time zone,
    is_completed boolean
);


ALTER TABLE public.analysis_plans OWNER TO wwwanalys_user;

--
-- Name: analysis_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.analysis_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analysis_plans_id_seq OWNER TO wwwanalys_user;

--
-- Name: analysis_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.analysis_plans_id_seq OWNED BY public.analysis_plans.id;


--
-- Name: analysis_types; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.analysis_types (
    id integer NOT NULL,
    name character varying,
    description character varying,
    created_at timestamp without time zone,
    created_by integer,
    is_active boolean,
    external_id character varying(255)
);


ALTER TABLE public.analysis_types OWNER TO wwwanalys_user;

--
-- Name: analysis_types_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.analysis_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analysis_types_id_seq OWNER TO wwwanalys_user;

--
-- Name: analysis_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.analysis_types_id_seq OWNED BY public.analysis_types.id;


--
-- Name: indicator_library; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.indicator_library (
    id integer NOT NULL,
    name character varying,
    unit character varying,
    data_type character varying(20),
    options text,
    description text,
    category character varying(50),
    is_required boolean,
    default_value character varying,
    validation_rules text,
    created_by integer,
    created_at timestamp without time zone,
    external_id character varying(255)
);


ALTER TABLE public.indicator_library OWNER TO wwwanalys_user;

--
-- Name: indicator_library_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.indicator_library_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.indicator_library_id_seq OWNER TO wwwanalys_user;

--
-- Name: indicator_library_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.indicator_library_id_seq OWNED BY public.indicator_library.id;


--
-- Name: indicator_library_versions; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.indicator_library_versions (
    id integer NOT NULL,
    indicator_id integer NOT NULL,
    version integer NOT NULL,
    name character varying NOT NULL,
    unit character varying NOT NULL,
    data_type character varying(20),
    options text,
    description text,
    category character varying(50),
    is_required boolean,
    default_value character varying,
    validation_rules text,
    changed_by integer,
    change_type character varying(20),
    change_notes text,
    created_at timestamp without time zone
);


ALTER TABLE public.indicator_library_versions OWNER TO wwwanalys_user;

--
-- Name: indicator_library_versions_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.indicator_library_versions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.indicator_library_versions_id_seq OWNER TO wwwanalys_user;

--
-- Name: indicator_library_versions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.indicator_library_versions_id_seq OWNED BY public.indicator_library_versions.id;


--
-- Name: indicator_values; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.indicator_values (
    id integer NOT NULL,
    process_log_id integer,
    indicator_id integer,
    value double precision,
    text_value character varying,
    is_normal boolean,
    measured_at timestamp without time zone,
    notes character varying
);


ALTER TABLE public.indicator_values OWNER TO wwwanalys_user;

--
-- Name: indicator_values_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.indicator_values_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.indicator_values_id_seq OWNER TO wwwanalys_user;

--
-- Name: indicator_values_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.indicator_values_id_seq OWNED BY public.indicator_values.id;


--
-- Name: indicators; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.indicators (
    id integer NOT NULL,
    name character varying,
    unit character varying,
    min_value double precision,
    max_value double precision,
    data_type character varying(20),
    options text,
    analysis_type_id integer
);


ALTER TABLE public.indicators OWNER TO wwwanalys_user;

--
-- Name: indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.indicators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.indicators_id_seq OWNER TO wwwanalys_user;

--
-- Name: indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.indicators_id_seq OWNED BY public.indicators.id;


--
-- Name: integration_configs; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.integration_configs (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    base_url character varying(512),
    api_key character varying(512),
    username character varying(255),
    password character varying(512),
    timeout integer NOT NULL,
    verify_ssl boolean NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    endpoint character varying(512),
    indicators_endpoint character varying(512),
    templates_endpoint character varying(512),
    plans_endpoint character varying(512)
);


ALTER TABLE public.integration_configs OWNER TO wwwanalys_user;

--
-- Name: COLUMN integration_configs.name; Type: COMMENT; Schema: public; Owner: wwwanalys_user
--

COMMENT ON COLUMN public.integration_configs.name IS 'Идентификатор интеграции, напр. ''1c''';


--
-- Name: COLUMN integration_configs.verify_ssl; Type: COMMENT; Schema: public; Owner: wwwanalys_user
--

COMMENT ON COLUMN public.integration_configs.verify_ssl IS 'Проверять SSL-сертификат';


--
-- Name: integration_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.integration_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.integration_configs_id_seq OWNER TO wwwanalys_user;

--
-- Name: integration_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.integration_configs_id_seq OWNED BY public.integration_configs.id;


--
-- Name: plan_items; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.plan_items (
    id integer NOT NULL,
    plan_id integer,
    template_id integer NOT NULL,
    batch_number character varying,
    sort_order integer,
    is_completed boolean,
    completed_report_id integer
);


ALTER TABLE public.plan_items OWNER TO wwwanalys_user;

--
-- Name: plan_items_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.plan_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.plan_items_id_seq OWNER TO wwwanalys_user;

--
-- Name: plan_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.plan_items_id_seq OWNED BY public.plan_items.id;


--
-- Name: preset_indicators; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.preset_indicators (
    id integer NOT NULL,
    preset_id integer,
    indicator_id integer,
    min_value double precision,
    max_value double precision,
    sort_order integer,
    is_required integer
);


ALTER TABLE public.preset_indicators OWNER TO wwwanalys_user;

--
-- Name: preset_indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.preset_indicators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.preset_indicators_id_seq OWNER TO wwwanalys_user;

--
-- Name: preset_indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.preset_indicators_id_seq OWNED BY public.preset_indicators.id;


--
-- Name: presets; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.presets (
    id integer NOT NULL,
    name character varying,
    description text,
    category character varying(50),
    created_at timestamp without time zone,
    created_by integer
);


ALTER TABLE public.presets OWNER TO wwwanalys_user;

--
-- Name: presets_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.presets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.presets_id_seq OWNER TO wwwanalys_user;

--
-- Name: presets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.presets_id_seq OWNED BY public.presets.id;


--
-- Name: process_logs; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.process_logs (
    id integer NOT NULL,
    batch_number character varying,
    analysis_type_id integer,
    created_by integer,
    status public.status,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    notes character varying
);


ALTER TABLE public.process_logs OWNER TO wwwanalys_user;

--
-- Name: process_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.process_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.process_logs_id_seq OWNER TO wwwanalys_user;

--
-- Name: process_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.process_logs_id_seq OWNED BY public.process_logs.id;


--
-- Name: template_indicators; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.template_indicators (
    id integer NOT NULL,
    template_id integer,
    indicator_id integer,
    min_value double precision,
    max_value double precision,
    sort_order integer,
    is_custom boolean,
    template_notes text,
    external_id character varying(255)
);


ALTER TABLE public.template_indicators OWNER TO wwwanalys_user;

--
-- Name: template_indicators_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.template_indicators_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.template_indicators_id_seq OWNER TO wwwanalys_user;

--
-- Name: template_indicators_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.template_indicators_id_seq OWNED BY public.template_indicators.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: wwwanalys_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying,
    email character varying,
    hashed_password character varying,
    is_active boolean,
    is_admin boolean
);


ALTER TABLE public.users OWNER TO wwwanalys_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: wwwanalys_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO wwwanalys_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wwwanalys_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: analysis_plans id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_plans ALTER COLUMN id SET DEFAULT nextval('public.analysis_plans_id_seq'::regclass);


--
-- Name: analysis_types id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_types ALTER COLUMN id SET DEFAULT nextval('public.analysis_types_id_seq'::regclass);


--
-- Name: indicator_library id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_library ALTER COLUMN id SET DEFAULT nextval('public.indicator_library_id_seq'::regclass);


--
-- Name: indicator_library_versions id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_library_versions ALTER COLUMN id SET DEFAULT nextval('public.indicator_library_versions_id_seq'::regclass);


--
-- Name: indicator_values id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_values ALTER COLUMN id SET DEFAULT nextval('public.indicator_values_id_seq'::regclass);


--
-- Name: indicators id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicators ALTER COLUMN id SET DEFAULT nextval('public.indicators_id_seq'::regclass);


--
-- Name: integration_configs id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.integration_configs ALTER COLUMN id SET DEFAULT nextval('public.integration_configs_id_seq'::regclass);


--
-- Name: plan_items id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.plan_items ALTER COLUMN id SET DEFAULT nextval('public.plan_items_id_seq'::regclass);


--
-- Name: preset_indicators id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.preset_indicators ALTER COLUMN id SET DEFAULT nextval('public.preset_indicators_id_seq'::regclass);


--
-- Name: presets id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.presets ALTER COLUMN id SET DEFAULT nextval('public.presets_id_seq'::regclass);


--
-- Name: process_logs id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.process_logs ALTER COLUMN id SET DEFAULT nextval('public.process_logs_id_seq'::regclass);


--
-- Name: template_indicators id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.template_indicators ALTER COLUMN id SET DEFAULT nextval('public.template_indicators_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: analysis_plans; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.analysis_plans (id, name, description, plan_date, created_by, created_at, is_completed) FROM stdin;
1	смена 1		2026-06-17	1	2026-06-17 13:55:28.587097	t
2	смена 1		2026-07-17	1	2026-07-17 10:34:58.40014	t
3	смена 1		2026-07-24	1	2026-07-24 12:20:26.759761	f
4	смена 1		2026-07-28	1	2026-07-28 17:31:34.734197	f
5	смена 1		2026-07-30	1	2026-07-30 09:38:16.721577	t
\.


--
-- Data for Name: analysis_types; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.analysis_types (id, name, description, created_at, created_by, is_active, external_id) FROM stdin;
1	Варка сусла	Шаблон варки	2026-06-17 13:18:26.269584	1	t	1
\.


--
-- Data for Name: indicator_library; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.indicator_library (id, name, unit, data_type, options, description, category, is_required, default_value, validation_rules, created_by, created_at, external_id) FROM stdin;
1	температура	С	number	\N	\N	\N	f	\N	\N	1	2026-06-17 13:54:24.55555	\N
2	Экстрактивность	%	number	\N	Экстрактивность сусла	Варка	t	11.5	\N	\N	2026-07-16 09:38:02.346432	1
3	Кислотность	pH	number	\N	Кислотность сусла	Варка	t	5.5	\N	\N	2026-07-16 09:38:02.346436	2
6	Фактическая дата анализа		number	\N	Фактическая дата анализа		f		\N	\N	2026-07-16 10:48:16.385586	fd1dfec3-7d76-11ea-803b-00155d6ac507
7	RLU		number	\N	RLU		f		\N	\N	2026-07-16 10:48:16.38559	5d2c51e8-1194-11e8-81e7-00155d6ac501
4	Цветность	EBC	number	\N	Цвет пива	Варка	f		\N	\N	2026-07-16 09:38:02.346437	3
5	Сорт ячменя		select	Альфа,Беты,Гамма	Сорт ячменя	Сырьё	f		\N	\N	2026-07-16 09:38:02.346437	4
8	Вкус		number	\N	Вкус	Стойкость	f		\N	\N	2026-07-16 10:48:16.385591	0dbab828-1b79-11e7-8705-00155d6ac501
9	Аромат		number	\N	Аромат	Стойкость	f		\N	\N	2026-07-16 10:48:16.385591	0dbab829-1b79-11e7-8705-00155d6ac501
61	Тип тары		number	\N	Тип тары		f		\N	\N	2026-07-16 10:48:16.385611	e977458f-65eb-11e7-a199-00155d6ac501
10	Стойкость результат		number	\N	Стойкость результат	Стойкость	f		\N	\N	2026-07-16 10:48:16.385594	1e0d3d8e-1b79-11e7-8705-00155d6ac501
11	Кол-во мертвых кл, %		number	\N	Кол-во мертвых кл, %		f		\N	\N	2026-07-16 10:48:16.385594	01749640-1b8b-11e7-8705-00155d6ac501
12	Упитанность, %		number	\N	Упитанность, %		f		\N	\N	2026-07-16 10:48:16.385595	13e273b0-1b8b-11e7-8705-00155d6ac501
13	Стойкость		number	\N	Стойкость		f		\N	\N	2026-07-16 10:48:16.385595	28900445-2108-11e7-8705-00155d6ac501
14	Внешний вид		number	\N	Внешний вид	Стойкость	f		\N	\N	2026-07-16 10:48:16.385596	49ad057b-2108-11e7-8705-00155d6ac501
15	Номер ТУД		number	\N	Номер ТУД		f		\N	\N	2026-07-16 10:48:16.385596	31177fd9-237f-11e7-8705-00155d6ac501
16	Бак. Кат+		number	\N	Бак. Кат+		f		\N	\N	2026-07-16 10:48:16.385596	40d55a26-237f-11e7-8705-00155d6ac501
17	Плесени		number	\N	Плесени		f		\N	\N	2026-07-16 10:48:16.385597	6b14e89f-237f-11e7-8705-00155d6ac501
18	МКБ		number	\N	МКБ		f		\N	\N	2026-07-16 10:48:16.385597	759fe1fb-237f-11e7-8705-00155d6ac501
19	Дикие дрожжи		number	\N	Дикие дрожжи		f		\N	\N	2026-07-16 10:48:16.385597	8e452e8c-237f-11e7-8705-00155d6ac501
20	Номер Варки		number	\N	Номер Варки		f		\N	\N	2026-07-16 10:48:16.385598	f7959f0c-237f-11e7-8705-00155d6ac501
21	Дрожжи		number	\N	Дрожжи		f		\N	\N	2026-07-16 10:48:16.385598	2b973819-2380-11e7-8705-00155d6ac501
22	Аэробный посев		number	\N	Аэробный посев		f		\N	\N	2026-07-16 10:48:16.385598	1212da11-2383-11e7-8705-00155d6ac501
23	Анаэробный посев		number	\N	Анаэробный посев		f		\N	\N	2026-07-16 10:48:16.385599	518f4eae-2383-11e7-8705-00155d6ac501
24	Солод		number	\N	Солод		f		\N	\N	2026-07-16 10:48:16.385599	ea63756d-2670-11e7-8705-00155d6ac501
25	Влажность		number	\N	Влажность	Солод	f		\N	\N	2026-07-16 10:48:16.385599	085497f9-2671-11e7-8705-00155d6ac501
26	АСВ экстракт		number	\N	АСВ экстракт	Солод	f		\N	\N	2026-07-16 10:48:16.385599	55156fa6-2671-11e7-8705-00155d6ac501
27	Концентрация, %		number	\N	Концентрация, %		f		\N	\N	2026-07-16 10:48:16.3856	8f197c01-613f-11e7-91ff-00155d6ac501
28	Сброс дрожжей		number	\N	Сброс дрожжей	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.3856	8a319459-2c0e-11e7-9245-00155d6ac501
29	Жесткость		number	\N	Жесткость		f		\N	\N	2026-07-16 10:48:16.3856	0d6f9a0a-479f-11e8-925b-00155d6ac501
30	Щелочность (общ)		number	\N	Щелочность (общ)		f		\N	\N	2026-07-16 10:48:16.385601	339f9c46-479f-11e8-925b-00155d6ac501
31	Щелочность (по ф/ф)		number	\N	Щелочность (по ф/ф)		f		\N	\N	2026-07-16 10:48:16.385601	4b271459-479f-11e8-925b-00155d6ac501
32	Остаточный хлор		number	\N	Остаточный хлор		f		\N	\N	2026-07-16 10:48:16.385601	603d706c-479f-11e8-925b-00155d6ac501
33	Fe		number	\N	Fe		f		\N	\N	2026-07-16 10:48:16.385602	86c007fd-479f-11e8-925b-00155d6ac501
34	Точка отбора		number	\N	Точка отбора		f		\N	\N	2026-07-16 10:48:16.385602	07f3c4cb-47a0-11e8-925b-00155d6ac501
35	Остаточный хлор (ячейка)		number	\N	Остаточный хлор (ячейка)		f		\N	\N	2026-07-16 10:48:16.385602	0a6d49d6-47ac-11e8-925b-00155d6ac501
36	Альфа кислота		number	\N	Альфа кислота		f		\N	\N	2026-07-16 10:48:16.385603	eb2c6c1f-47ac-11e8-925b-00155d6ac501
37	Цвет		number	\N	Цвет		f		\N	\N	2026-07-16 10:48:16.385603	23c9f31b-47ad-11e8-925b-00155d6ac501
38	Содержание карбонатов, %		number	\N	Содержание карбонатов, %		f		\N	\N	2026-07-16 10:48:16.385603	5056a3a5-47ad-11e8-925b-00155d6ac501
39	Плотность, г/см3		number	\N	Плотность, г/см3		f		\N	\N	2026-07-16 10:48:16.385604	ad8441ca-47ad-11e8-925b-00155d6ac501
40	Масса 1 канистры (сред), кг		number	\N	Масса 1 канистры (сред), кг		f		\N	\N	2026-07-16 10:48:16.385604	dc8c4974-47ad-11e8-925b-00155d6ac501
41	Сепарация,фильтрация,дегустация,дрожжи		number	\N	Сепарация,фильтрация,дегустация,дрожжи		f		\N	\N	2026-07-16 10:48:16.385605	f8555328-ff52-11e6-968a-00155d6ac501
42	Ф.И.О.		number	\N	Ф.И.О.	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.385605	048d3cdb-ff53-11e6-968a-00155d6ac501
43	Результат		number	\N	Результат	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.385605	156c1773-ff53-11e6-968a-00155d6ac501
44	СО2	г/л	number	\N	СО2		f		\N	\N	2026-07-16 10:48:16.385606	db01e5ac-0594-11e7-968a-00155d6ac501
45	О2 (ppb)	ppb	number	\N	О2 (ppb)		f		\N	\N	2026-07-16 10:48:16.385606	ebd847ac-0594-11e7-968a-00155d6ac501
46	Мутность		number	\N	Мутность		f		\N	\N	2026-07-16 10:48:16.385606	f638ba0d-0594-11e7-968a-00155d6ac501
47	Формат тары		number	\N	Формат тары		f		\N	\N	2026-07-16 10:48:16.385607	660ee46d-8eff-11e8-97d5-00155d6ac501
48	Пенообразование		number	\N	Пенообразование		f		\N	\N	2026-07-16 10:48:16.385607	27aeed05-cf95-11e7-9883-00155d6ac501
49	Пеностойкость		number	\N	Пеностойкость		f		\N	\N	2026-07-16 10:48:16.385607	316f2da5-cf95-11e7-9883-00155d6ac501
50	Полнота налива		number	\N	Полнота налива		f		\N	\N	2026-07-16 10:48:16.385607	3d51d901-cf95-11e7-9883-00155d6ac501
51	Адрес торговой точки		number	\N	Адрес торговой точки		f		\N	\N	2026-07-16 10:48:16.385608	40351cfe-654d-11e7-a199-00155d6ac501
52	Причина возврата		number	\N	Причина возврата		f		\N	\N	2026-07-16 10:48:16.385608	4c80395e-654d-11e7-a199-00155d6ac501
53	Контрагент		number	\N	Контрагент		f		\N	\N	2026-07-16 10:48:16.385608	59690d14-654d-11e7-a199-00155d6ac501
54	Номенклатура (сорт)		number	\N	Номенклатура (сорт)		f		\N	\N	2026-07-16 10:48:16.385609	4f70edab-65eb-11e7-a199-00155d6ac501
55	Документ реализации		number	\N	Документ реализации		f		\N	\N	2026-07-16 10:48:16.385609	622b478d-65eb-11e7-a199-00155d6ac501
56	№ реализации		number	\N	№ реализации		f		\N	\N	2026-07-16 10:48:16.385609	78995c87-65eb-11e7-a199-00155d6ac501
57	Дата реализации		number	\N	Дата реализации		f		\N	\N	2026-07-16 10:48:16.38561	936d95a1-65eb-11e7-a199-00155d6ac501
58	Номер розлива		number	\N	Номер розлива		f		\N	\N	2026-07-16 10:48:16.38561	a7378c60-65eb-11e7-a199-00155d6ac501
59	Дата розлива		number	\N	Дата розлива		f		\N	\N	2026-07-16 10:48:16.38561	b6183a43-65eb-11e7-a199-00155d6ac501
60	Сутки на момент изъятия		number	\N	Сутки на момент изъятия		f		\N	\N	2026-07-16 10:48:16.385611	ce35e627-65eb-11e7-a199-00155d6ac501
62	Объем, л		number	\N	Объем, л		f		\N	\N	2026-07-16 10:48:16.385611	0c4c670b-65ec-11e7-a199-00155d6ac501
63	Результат по возврату		number	\N	Результат по возврату		f		\N	\N	2026-07-16 10:48:16.385611	49d7f8d9-660e-11e7-a199-00155d6ac501
64	Дата возврата		number	\N	Дата возврата		f		\N	\N	2026-07-16 10:48:16.385612	a3862e88-6616-11e7-a199-00155d6ac501
65	Номер возврата		number	\N	Номер возврата		f		\N	\N	2026-07-16 10:48:16.385612	c045a5bc-6616-11e7-a199-00155d6ac501
66	номер сусловой		number	\N	номер сусловой		f		\N	\N	2026-07-16 10:48:16.385612	24d1d50a-6e17-11e7-a199-00155d6ac501
67	Партия		number	\N	Партия		f		\N	\N	2026-07-16 10:48:16.385613	75c63612-6e17-11e7-a199-00155d6ac501
68	Вкусовая стойкость		number	\N	Вкусовая стойкость		f		\N	\N	2026-07-16 10:48:16.385613	d45a2d4c-6e17-11e7-a199-00155d6ac501
69	Коллоидная стойкость		number	\N	Коллоидная стойкость		f		\N	\N	2026-07-16 10:48:16.385613	07c2b037-6e18-11e7-a199-00155d6ac501
70	М/Б стойкость		number	\N	М/Б стойкость		f		\N	\N	2026-07-16 10:48:16.385614	2092ff04-6e18-11e7-a199-00155d6ac501
71	не исп БГКП		number	\N	не исп БГКП		f		\N	\N	2026-07-16 10:48:16.385614	abaedc06-6e18-11e7-a199-00155d6ac501
72	БГКП		number	\N	БГКП		f		\N	\N	2026-07-16 10:48:16.385614	d57edb6e-706d-11e7-a199-00155d6ac501
73	ОМЧ, КОЕ	КОЕ	number	\N	ОМЧ, КОЕ		f		\N	\N	2026-07-16 10:48:16.385614	145a3d00-7c59-11e7-a199-00155d6ac501
74	ФИО Химик		number	\N	ФИО Химик	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.385615	9d26c7ee-a59d-11ef-a1fb-000c29c66ae9
75	ФИО допустившего к розливу		number	\N	ФИО допустившего к розливу	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.385615	aa099794-a59d-11ef-a1fb-000c29c66ae9
76	ФИО Начальник смены		number	\N	ФИО Начальник смены	Сепарация,фильтрация,дегустация,дрожжи	f		\N	\N	2026-07-16 10:48:16.385615	b2a3f695-a59d-11ef-a1fb-000c29c66ae9
77	Мутность 90 (паст.)	ЕВС	number	\N	Мутность 90 (паст.)		f		\N	\N	2026-07-16 10:48:16.385616	b14c9d9f-b30a-11ef-a1fb-000c29c66ae9
78	Мутность 25 (паст.)	ЕВС	number	\N	Мутность 25 (паст.)		f		\N	\N	2026-07-16 10:48:16.385616	c456273f-b30a-11ef-a1fb-000c29c66ae9
79	Бликфельдт мод.1		number	\N	Бликфельдт мод.1		f		\N	\N	2026-07-16 10:48:16.385616	85dbc3c7-bc91-11ef-a1fb-000c29c66ae9
80	ФИО (химик)		number	\N	ФИО (химик)		f		\N	\N	2026-07-16 10:48:16.385617	07e6f779-cc0d-11ef-a1fb-000c29c66ae9
81	Пастеризационные единицы (право)		number	\N	Пастеризационные единицы (право)		f		\N	\N	2026-07-16 10:48:16.385617	2c4859cb-d1d4-11ef-a1fb-000c29c66ae9
82	Пастеризационные единицы (середина)		number	\N	Пастеризационные единицы (середина)		f		\N	\N	2026-07-16 10:48:16.385617	38c74bfa-d1d4-11ef-a1fb-000c29c66ae9
83	Покупатель (ИП, ООО)		number	\N	Покупатель (ИП, ООО)		f		\N	\N	2026-07-16 10:48:16.385617	aca251a2-d2a9-11ef-a1fb-000c29c66ae9
84	СО2 (органолептика)		number	\N	СО2 (органолептика)		f		\N	\N	2026-07-16 10:48:16.385618	dc15948e-d98c-11ef-a1fb-000c29c66ae9
85	Влажность, %		number	\N	Влажность, %		f		\N	\N	2026-07-16 10:48:16.385618	0fe2ebba-da30-11ef-a1fb-000c29c66ae9
86	Экстрактивность, %		number	\N	Экстрактивность, %		f		\N	\N	2026-07-16 10:48:16.385618	73471341-da30-11ef-a1fb-000c29c66ae9
87	Дата оформления претензии		number	\N	Дата оформления претензии		f		\N	\N	2026-07-16 10:48:16.385619	905efd1e-f82f-11ef-a1fb-000c29c66ae9
88	ОМЧ (КОЕ/мл)		number	\N	ОМЧ (КОЕ/мл)		f		\N	\N	2026-07-16 10:48:16.385619	8451e393-2684-11f0-a202-000c29c66ae9
89	Партия форфаса		number	\N	Партия форфаса		f		\N	\N	2026-07-16 10:48:16.385619	e22a2e42-268e-11f0-a202-000c29c66ae9
90	Мутность 90 (Стрекозел)	ЕВС	number	\N	Мутность 90 (Стрекозел)		f		\N	\N	2026-07-16 10:48:16.38562	def13241-4206-11f0-a202-000c29c66ae9
91	Пастеризатор		number	\N	Пастеризатор	Начальные условия	f		\N	\N	2026-07-16 10:48:16.38562	0712c6ae-6727-11f0-a203-000c29c66ae9
92	pH	ед рН	number	\N	pH		f		\N	\N	2026-07-16 10:48:16.38562	a10f4324-6727-11f0-a203-000c29c66ae9
93	pH (2 ветка)	ед рН	number	\N	pH (2 ветка)		f		\N	\N	2026-07-16 10:48:16.38562	a8107e1b-6727-11f0-a203-000c29c66ae9
94	pH (3 ветка)	ед рН	number	\N	pH (3 ветка)		f		\N	\N	2026-07-16 10:48:16.385621	ac3f9356-6727-11f0-a203-000c29c66ae9
95	Мутность 90 (1 ветка)	ЕВС	number	\N	Мутность 90 (1 ветка)		f		\N	\N	2026-07-16 10:48:16.385621	30bc013f-6728-11f0-a203-000c29c66ae9
96	Мутность 90 (2 ветка)	ЕВС	number	\N	Мутность 90 (2 ветка)		f		\N	\N	2026-07-16 10:48:16.385621	501e9438-6728-11f0-a203-000c29c66ae9
97	Мутность 90 (3 ветка)	ЕВС	number	\N	Мутность 90 (3 ветка)		f		\N	\N	2026-07-16 10:48:16.385622	6675b042-6728-11f0-a203-000c29c66ae9
98	Мутность 25 (1 ветка)	ЕВС	number	\N	Мутность 25 (1 ветка)		f		\N	\N	2026-07-16 10:48:16.385622	49ddf904-6729-11f0-a203-000c29c66ae9
99	Мутность 25 (2 ветка)	ЕВС	number	\N	Мутность 25 (2 ветка)		f		\N	\N	2026-07-16 10:48:16.385622	667d2622-6729-11f0-a203-000c29c66ae9
100	Мутность 25 (3 ветка)	ЕВС	number	\N	Мутность 25 (3 ветка)		f		\N	\N	2026-07-16 10:48:16.385622	71c2900d-6729-11f0-a203-000c29c66ae9
101	Вкус (1 ветка)		number	\N	Вкус (1 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385623	b16fc2ef-6729-11f0-a203-000c29c66ae9
102	Вкус (2 ветка)		number	\N	Вкус (2 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385623	ff14c2a9-6729-11f0-a203-000c29c66ae9
103	Вкус (3 ветка)		number	\N	Вкус (3 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385623	3b7aa51d-672a-11f0-a203-000c29c66ae9
104	Аромат (1 ветка)		number	\N	Аромат (1 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385624	813cae9e-672a-11f0-a203-000c29c66ae9
105	Аромат (2 ветка)		number	\N	Аромат (2 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385624	9398e45b-672a-11f0-a203-000c29c66ae9
106	Аромат (3 ветка)		number	\N	Аромат (3 ветка)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385624	aeb2d716-672a-11f0-a203-000c29c66ae9
107	Кислотность (1 ветка)	ед. кислотности	number	\N	Кислотность (1 ветка)		f		\N	\N	2026-07-16 10:48:16.385624	4f7afc89-672c-11f0-a203-000c29c66ae9
321	Шпунт, bar		number	\N	Шпунт, bar		f		\N	\N	2026-07-16 10:48:16.385695	afe5ef19-f353-11e6-aa1b-0021f60b3798
108	Кислотность (2 ветка)	ед. кислотности	number	\N	Кислотность (2 ветка)		f		\N	\N	2026-07-16 10:48:16.385625	561c3cbb-672c-11f0-a203-000c29c66ae9
109	Кислотность (3 ветка)	ед. кислотности	number	\N	Кислотность (3 ветка)		f		\N	\N	2026-07-16 10:48:16.385625	5d98258a-672c-11f0-a203-000c29c66ae9
110	Линия розлива		number	\N	Линия розлива	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385625	2a222c69-672e-11f0-a203-000c29c66ae9
111	pH (КС)	ед рН	number	\N	pH (КС)		f		\N	\N	2026-07-16 10:48:16.385626	2c4dcd2d-672f-11f0-a203-000c29c66ae9
112	pH (КС+)	ед рН	number	\N	pH (КС+)		f		\N	\N	2026-07-16 10:48:16.385626	3f08b63b-672f-11f0-a203-000c29c66ae9
113	Кислотность (КС)	ед. кислотности	number	\N	Кислотность (КС)		f		\N	\N	2026-07-16 10:48:16.385626	5da7d286-672f-11f0-a203-000c29c66ae9
114	Кислотность (КС+)	ед. кислотности	number	\N	Кислотность (КС+)		f		\N	\N	2026-07-16 10:48:16.385626	6ac79872-672f-11f0-a203-000c29c66ae9
115	Мутность 90 (КС)	ЕВС	number	\N	Мутность 90 (КС)		f		\N	\N	2026-07-16 10:48:16.385627	8170a6be-672f-11f0-a203-000c29c66ae9
116	Мутность 25 (КС)	ЕВС	number	\N	Мутность 25 (КС)		f		\N	\N	2026-07-16 10:48:16.385627	98945360-672f-11f0-a203-000c29c66ae9
117	Мутность 90 (КС+)	ЕВС	number	\N	Мутность 90 (КС+)		f		\N	\N	2026-07-16 10:48:16.385627	a5a6cbf7-672f-11f0-a203-000c29c66ae9
118	Мутность 25 (КС+)	ЕВС	number	\N	Мутность 25 (КС+)		f		\N	\N	2026-07-16 10:48:16.385628	b66d7016-672f-11f0-a203-000c29c66ae9
119	Вкус (КС)		number	\N	Вкус (КС)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385628	c9a40f0d-672f-11f0-a203-000c29c66ae9
120	Вкус (КС+)		number	\N	Вкус (КС+)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385628	16fb19e4-6730-11f0-a203-000c29c66ae9
121	Аромат (КС)		number	\N	Аромат (КС)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385629	38f91864-6730-11f0-a203-000c29c66ae9
122	Аромат (КС+)		number	\N	Аромат (КС+)	Стойкость	f		\N	\N	2026-07-16 10:48:16.385629	6278c414-6730-11f0-a203-000c29c66ae9
123	Заключение		number	\N	Заключение		f		\N	\N	2026-07-16 10:48:16.385629	46a63061-6736-11f0-a203-000c29c66ae9
124	Время отбора		number	\N	Время отбора		f		\N	\N	2026-07-16 10:48:16.38563	6f59541a-79b7-11f0-a203-000c29c66ae9
125	Пропагатор		number	\N	Пропагатор		f		\N	\N	2026-07-16 10:48:16.38563	9074fe18-79b7-11f0-a203-000c29c66ae9
126	Экстракт, %		number	\N	Экстракт, %		f		\N	\N	2026-07-16 10:48:16.38563	ab276c7b-79b7-11f0-a203-000c29c66ae9
127	Температура, С		number	\N	Температура, С		f		\N	\N	2026-07-16 10:48:16.38563	c1166c4b-79b7-11f0-a203-000c29c66ae9
128	КДК, млн/мл	млн/мл	number	\N	КДК, млн/мл		f		\N	\N	2026-07-16 10:48:16.385631	dbad550f-79b7-11f0-a203-000c29c66ae9
129	Количество мёртвых клеток, %		number	\N	Количество мёртвых клеток, %		f		\N	\N	2026-07-16 10:48:16.385631	1f1f1352-79b8-11f0-a203-000c29c66ae9
130	Раса дрожжей		number	\N	Раса дрожжей		f		\N	\N	2026-07-16 10:48:16.385631	83f2145b-79b8-11f0-a203-000c29c66ae9
131	Генерация дрожжей		number	\N	Генерация дрожжей		f		\N	\N	2026-07-16 10:48:16.385632	9841933d-79b8-11f0-a203-000c29c66ae9
132	Питательная среда		number	\N	Питательная среда		f		\N	\N	2026-07-16 10:48:16.385632	6bde5a7b-79bf-11f0-a203-000c29c66ae9
133	ОМЧ, КОЕ/мл		number	\N	ОМЧ, КОЕ/мл		f		\N	\N	2026-07-16 10:48:16.385632	368a1a32-79c0-11f0-a203-000c29c66ae9
134	М/о вредители		number	\N	М/о вредители		f		\N	\N	2026-07-16 10:48:16.385633	6d9bd192-79c0-11f0-a203-000c29c66ae9
135	М/о по идентификации		number	\N	М/о по идентификации		f		\N	\N	2026-07-16 10:48:16.385633	c3dd12e1-79c1-11f0-a203-000c29c66ae9
136	Номер ёмкости		number	\N	Номер ёмкости	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385633	b9f19b9d-79c4-11f0-a203-000c29c66ae9
137	КДК		number	\N	КДК		f		\N	\N	2026-07-16 10:48:16.385633	0193a49b-922b-11f0-a203-000c29c66ae9
138	Заданы (партия)		number	\N	Заданы (партия)		f		\N	\N	2026-07-16 10:48:16.385634	65ba6eb7-922b-11f0-a203-000c29c66ae9
139	Заданы (ЦКТ, танк)		number	\N	Заданы (ЦКТ, танк)		f		\N	\N	2026-07-16 10:48:16.385634	acb5454b-922b-11f0-a203-000c29c66ae9
140	Тип отбора		number	\N	Тип отбора		f		\N	\N	2026-07-16 10:48:16.385634	ee3616dd-922f-11f0-a203-000c29c66ae9
141	Микроорганизмы вредители		number	\N	Микроорганизмы вредители		f		\N	\N	2026-07-16 10:48:16.385635	96505f49-9230-11f0-a203-000c29c66ae9
142	Отбор		number	\N	Отбор		f		\N	\N	2026-07-16 10:48:16.385635	ce834644-af46-11f0-a208-000c29c66ae9
143	Момент отбора		number	\N	Момент отбора		f		\N	\N	2026-07-16 10:48:16.385635	2dcd9c40-f20a-11f0-a20e-000c29c66ae9
144	Дегустация		number	\N	Дегустация		f		\N	\N	2026-07-16 10:48:16.385636	3b688d2a-17bc-11f1-a210-000c29c66ae9
145	Ф/х		number	\N	Ф/х	Дегустация	f		\N	\N	2026-07-16 10:48:16.385636	4e1fd2ed-17bc-11f1-a210-000c29c66ae9
146	Пена	балл	number	\N	Пена	Ф/х	f		\N	\N	2026-07-16 10:48:16.385636	8302ea78-17c3-11f1-a210-000c29c66ae9
147	Насыщенность	балл	number	\N	Насыщенность	Ф/х	f		\N	\N	2026-07-16 10:48:16.385636	a7b7c0b4-17c3-11f1-a210-000c29c66ae9
148	Взвешенные частицы	балл	number	\N	Взвешенные частицы	Ф/х	f		\N	\N	2026-07-16 10:48:16.385637	d5e8f059-17c3-11f1-a210-000c29c66ae9
149	Эфиры (аромат)		number	\N	Эфиры (аромат)	Дегустация	f		\N	\N	2026-07-16 10:48:16.385637	132882d8-17c4-11f1-a210-000c29c66ae9
150	Изоамилацетат (леденцы, банан)	балл	number	\N	Изоамилацетат (леденцы, банан)	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385637	60005ab3-17c5-11f1-a210-000c29c66ae9
151	Этилгексаноат (спелые яблоки)	балл	number	\N	Этилгексаноат (спелые яблоки)	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385638	72773849-17c5-11f1-a210-000c29c66ae9
152	Фруктовый	балл	number	\N	Фруктовый	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385638	801ca008-17c5-11f1-a210-000c29c66ae9
153	Цветочный/медовый	балл	number	\N	Цветочный/медовый	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385638	8ee2d389-17c5-11f1-a210-000c29c66ae9
154	Гвоздичный (специи)	балл	number	\N	Гвоздичный (специи)	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385638	9e4ba250-17c5-11f1-a210-000c29c66ae9
155	Общая оценка группы (от 1 до 5)	балл	number	\N	Общая оценка группы (от 1 до 5)	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385639	b5edbf3d-17c5-11f1-a210-000c29c66ae9
156	Хмелевой аромат	балл	number	\N	Хмелевой аромат	Эфиры (аромат)	f		\N	\N	2026-07-16 10:48:16.385639	c1781cd7-17c5-11f1-a210-000c29c66ae9
157	Старение (окисление)		number	\N	Старение (окисление)	Дегустация	f		\N	\N	2026-07-16 10:48:16.385639	f804a03a-17c5-11f1-a210-000c29c66ae9
158	Фруктовое окисление	балл	number	\N	Фруктовое окисление	Старение (окисление)	f		\N	\N	2026-07-16 10:48:16.38564	06b13684-17c6-11f1-a210-000c29c66ae9
159	Бумажный/картонный тон	балл	number	\N	Бумажный/картонный тон	Старение (окисление)	f		\N	\N	2026-07-16 10:48:16.38564	608562ac-17c6-11f1-a210-000c29c66ae9
160	Хлебный тон	балл	number	\N	Хлебный тон	Старение (окисление)	f		\N	\N	2026-07-16 10:48:16.38564	6c947327-17c6-11f1-a210-000c29c66ae9
161	Старого хмеля (кожа, табак, изовалерьяновый)	балл	number	\N	Старого хмеля (кожа, табак, изовалерьяновый)	Старение (окисление)	f		\N	\N	2026-07-16 10:48:16.38564	876d2289-17c6-11f1-a210-000c29c66ae9
162	Старение общее	балл	number	\N	Старение общее	Старение (окисление)	f		\N	\N	2026-07-16 10:48:16.385641	9bed861c-17c6-11f1-a210-000c29c66ae9
163	Серные тона		number	\N	Серные тона	Дегустация	f		\N	\N	2026-07-16 10:48:16.385641	1066dbd9-1867-11f1-a210-000c29c66ae9
164	Сульфитный (спички)	балл	number	\N	Сульфитный (спички)	Серные тона	f		\N	\N	2026-07-16 10:48:16.385641	2075291e-1867-11f1-a210-000c29c66ae9
165	Сероводород (тухлые яйца)	балл	number	\N	Сероводород (тухлые яйца)	Серные тона	f		\N	\N	2026-07-16 10:48:16.385642	30795e28-1867-11f1-a210-000c29c66ae9
166	Луковый	балл	number	\N	Луковый	Серные тона	f		\N	\N	2026-07-16 10:48:16.385642	482ffbac-1867-11f1-a210-000c29c66ae9
167	Меркаптан (стоки, гнилой лук)	балл	number	\N	Меркаптан (стоки, гнилой лук)	Серные тона	f		\N	\N	2026-07-16 10:48:16.385642	767c00ec-1867-11f1-a210-000c29c66ae9
168	Горелая резина	балл	number	\N	Горелая резина	Серные тона	f		\N	\N	2026-07-16 10:48:16.385642	862b352f-1867-11f1-a210-000c29c66ae9
169	Дрожжевой	балл	number	\N	Дрожжевой	Серные тона	f		\N	\N	2026-07-16 10:48:16.385643	9424a19e-1867-11f1-a210-000c29c66ae9
170	ДМС (вар. капуста, вар.кукуруза)	балл	number	\N	ДМС (вар. капуста, вар.кукуруза)	Серные тона	f		\N	\N	2026-07-16 10:48:16.385643	adc5005f-1867-11f1-a210-000c29c66ae9
171	Автолизат дрожжей	балл	number	\N	Автолизат дрожжей	Серные тона	f		\N	\N	2026-07-16 10:48:16.385643	bd18bc4a-1867-11f1-a210-000c29c66ae9
172	Засвеченный (скунс)	балл	number	\N	Засвеченный (скунс)	Серные тона	f		\N	\N	2026-07-16 10:48:16.385644	e092fd74-1867-11f1-a210-000c29c66ae9
173	Брожение		number	\N	Брожение	Дегустация	f		\N	\N	2026-07-16 10:48:16.385644	44fb813e-1868-11f1-a210-000c29c66ae9
174	Спиртовой	балл	number	\N	Спиртовой	Брожение	f		\N	\N	2026-07-16 10:48:16.385644	5256a25f-1868-11f1-a210-000c29c66ae9
175	Высшие спирты (сивушные)	балл	number	\N	Высшие спирты (сивушные)	Брожение	f		\N	\N	2026-07-16 10:48:16.385644	5f94701e-1868-11f1-a210-000c29c66ae9
176	Ацетальдегид	балл	number	\N	Ацетальдегид	Брожение	f		\N	\N	2026-07-16 10:48:16.385645	a67d94bf-1868-11f1-a210-000c29c66ae9
177	Фенольный (аптечный)	балл	number	\N	Фенольный (аптечный)	Брожение	f		\N	\N	2026-07-16 10:48:16.385645	b3690ab5-1868-11f1-a210-000c29c66ae9
178	Аромат порчи		number	\N	Аромат порчи	Дегустация	f		\N	\N	2026-07-16 10:48:16.385645	c142ba94-1868-11f1-a210-000c29c66ae9
179	Уксусный	балл	number	\N	Уксусный	Аромат порчи	f		\N	\N	2026-07-16 10:48:16.385646	cd3dc8a5-1868-11f1-a210-000c29c66ae9
180	Диацетил (масляный, сливочный)	балл	number	\N	Диацетил (масляный, сливочный)	Аромат порчи	f		\N	\N	2026-07-16 10:48:16.385646	34d9d7c1-1869-11f1-a210-000c29c66ae9
181	Бутирик (детские нечистоты)	балл	number	\N	Бутирик (детские нечистоты)	Аромат порчи	f		\N	\N	2026-07-16 10:48:16.385646	47ac0eff-1869-11f1-a210-000c29c66ae9
182	Вес кеги (30 л), кг	кг	number	\N	Вес кеги (30 л), кг		f		\N	\N	2026-07-16 10:48:16.385646	9889675e-243e-11f1-a210-000c29c66ae9
183	Вес кеги (20 л), кг	кг	number	\N	Вес кеги (20 л), кг		f		\N	\N	2026-07-16 10:48:16.385647	ae2da724-243e-11f1-a210-000c29c66ae9
184	Маркировка		number	\N	Маркировка		f		\N	\N	2026-07-16 10:48:16.385647	e87254a3-2443-11f1-a210-000c29c66ae9
185	Грам принадлежность		number	\N	Грам принадлежность		f		\N	\N	2026-07-16 10:48:16.385647	35c4a3bc-268b-11f1-a210-000c29c66ae9
186	Каталазный тест		number	\N	Каталазный тест		f		\N	\N	2026-07-16 10:48:16.385648	d1ce3752-268b-11f1-a210-000c29c66ae9
187	Тип п/о		number	\N	Тип п/о		f		\N	\N	2026-07-16 10:48:16.385648	7785fc72-268d-11f1-a210-000c29c66ae9
188	Затхлый (погреб, винная пробка)	балл	number	\N	Затхлый (погреб, винная пробка)	Аромат порчи	f		\N	\N	2026-07-16 10:48:16.385648	6fef7709-2809-11f1-a211-000c29c66ae9
189	Кошачий (смородина)	балл	number	\N	Кошачий (смородина)	Аромат порчи	f		\N	\N	2026-07-16 10:48:16.385648	85754664-2809-11f1-a211-000c29c66ae9
190	Кислый	балл	number	\N	Кислый	Вкус	f		\N	\N	2026-07-16 10:48:16.385649	ea960f5c-2809-11f1-a211-000c29c66ae9
191	Сладкий	балл	number	\N	Сладкий	Вкус	f		\N	\N	2026-07-16 10:48:16.385649	f3e03382-2809-11f1-a211-000c29c66ae9
192	Горечь хмелевая	балл	number	\N	Горечь хмелевая	Вкус	f		\N	\N	2026-07-16 10:48:16.385649	01295ea9-280a-11f1-a211-000c29c66ae9
193	Остаточная горечь	балл	number	\N	Остаточная горечь	Вкус	f		\N	\N	2026-07-16 10:48:16.38565	5be01c1a-280a-11f1-a211-000c29c66ae9
194	Танниновая вязкость	балл	number	\N	Танниновая вязкость	Вкус	f		\N	\N	2026-07-16 10:48:16.38565	92316206-280a-11f1-a211-000c29c66ae9
195	Металлический вкус	балл	number	\N	Металлический вкус	Вкус	f		\N	\N	2026-07-16 10:48:16.38565	a116f845-280a-11f1-a211-000c29c66ae9
196	Полнота вкуса (тело)	балл	number	\N	Полнота вкуса (тело)	Вкус	f		\N	\N	2026-07-16 10:48:16.385651	b8f8063d-280a-11f1-a211-000c29c66ae9
197	Зерновые тона		number	\N	Зерновые тона	Дегустация	f		\N	\N	2026-07-16 10:48:16.385651	c684d38b-280a-11f1-a211-000c29c66ae9
198	Солодовый	балл	number	\N	Солодовый	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385651	d5b0a3f6-280a-11f1-a211-000c29c66ae9
199	Меланоидиновый	балл	number	\N	Меланоидиновый	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385652	e5919866-280a-11f1-a211-000c29c66ae9
200	Карамельный	балл	number	\N	Карамельный	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385652	f055780c-280a-11f1-a211-000c29c66ae9
201	Шоколадный	балл	number	\N	Шоколадный	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385652	fc7664dd-280a-11f1-a211-000c29c66ae9
202	Жженый	балл	number	\N	Жженый	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385653	558d5f60-280b-11f1-a211-000c29c66ae9
203	Копченый	балл	number	\N	Копченый	Зерновые тона	f		\N	\N	2026-07-16 10:48:16.385653	5e890c21-280b-11f1-a211-000c29c66ae9
204	Итоговая оценка образца (от 1 до 9)	балл	number	\N	Итоговая оценка образца (от 1 до 9)	Дегустация	f		\N	\N	2026-07-16 10:48:16.385653	3ecb3081-2810-11f1-a211-000c29c66ae9
205	Фосфаты (РО4)	мг/л	number	\N	Фосфаты (РО4)		f		\N	\N	2026-07-16 10:48:16.385656	38db8e69-3194-11f1-a213-000c29c66ae9
206	Концентрация щелочи		number	\N	Концентрация щелочи		f		\N	\N	2026-07-16 10:48:16.385656	b79274e5-3194-11f1-a213-000c29c66ae9
207	Концентрация кислоты (HNO3)		number	\N	Концентрация кислоты (HNO3)		f		\N	\N	2026-07-16 10:48:16.385657	d76bdf6f-3194-11f1-a213-000c29c66ae9
208	Розлив согласован ФИО		number	\N	Розлив согласован ФИО		f		\N	\N	2026-07-16 10:48:16.385657	10c1d079-3198-11f1-a213-000c29c66ae9
209	Дегустация ИТОГИ		number	\N	Дегустация ИТОГИ	Дегустация	f		\N	\N	2026-07-16 10:48:16.385657	a271a097-331f-11f1-a213-000c29c66ae9
210	Суток на момент дегустации	Дни	number	\N	Суток на момент дегустации	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385657	d7958632-331f-11f1-a213-000c29c66ae9
211	Средняя оценка образца	балл	number	\N	Средняя оценка образца	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385658	eb202189-331f-11f1-a213-000c29c66ae9
212	Несоответствия органолептическому стандарту, отмеченные более чем 1 дегустатором.		number	\N	Несоответствия органолептическому стандарту, отмеченные более чем 1 дегустатором.	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385658	2187d34e-3320-11f1-a213-000c29c66ae9
213	Результаты Ф/Х или М/Б образца. В зависимости от отмеченных несоответствий.		number	\N	Результаты Ф/Х или М/Б образца. В зависимости от отмеченных несоответствий.	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385658	44ab5e1e-3320-11f1-a213-000c29c66ae9
214	Действия по несоответствиям		number	\N	Действия по несоответствиям	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385659	53722ef0-3320-11f1-a213-000c29c66ae9
215	Дата дегустации		number	\N	Дата дегустации	Дегустация ИТОГИ	f		\N	\N	2026-07-16 10:48:16.385659	867942e0-3320-11f1-a213-000c29c66ae9
216	Микробиолог (ФИО)		number	\N	Микробиолог (ФИО)		f		\N	\N	2026-07-16 10:48:16.385659	e7c49b41-3418-11f1-a213-000c29c66ae9
217	Йодное число		number	\N	Йодное число		f		\N	\N	2026-07-16 10:48:16.38566	824a4abb-373e-11f1-a213-000c29c66ae9
218	Концентрация раствора (БАК №1), %		number	\N	Концентрация раствора (БАК №1), %		f		\N	\N	2026-07-16 10:48:16.38566	cbde33b5-38b0-11f1-a213-000c29c66ae9
219	Концентрация раствора (БАК №2), %		number	\N	Концентрация раствора (БАК №2), %		f		\N	\N	2026-07-16 10:48:16.38566	eb5bf526-38b0-11f1-a213-000c29c66ae9
220	Концентрация карбонатов (БАК №1)		number	\N	Концентрация карбонатов (БАК №1)		f		\N	\N	2026-07-16 10:48:16.38566	1932f03f-38b1-11f1-a213-000c29c66ae9
221	Концентрация карбонатов (БАК №2)		number	\N	Концентрация карбонатов (БАК №2)		f		\N	\N	2026-07-16 10:48:16.385661	4c7fa4ab-38b1-11f1-a213-000c29c66ae9
222	Концентрация кислоты, %		number	\N	Концентрация кислоты, %		f		\N	\N	2026-07-16 10:48:16.385661	7c0cdb8d-38b1-11f1-a213-000c29c66ae9
223	Концентрация щелочи (КС), %		number	\N	Концентрация щелочи (КС), %		f		\N	\N	2026-07-16 10:48:16.385661	f79364e4-38b1-11f1-a213-000c29c66ae9
224	Концентрация кислоты (КС), %		number	\N	Концентрация кислоты (КС), %		f		\N	\N	2026-07-16 10:48:16.385662	49297c88-38b2-11f1-a213-000c29c66ae9
225	Концентрация карбонатов (КС), %		number	\N	Концентрация карбонатов (КС), %		f		\N	\N	2026-07-16 10:48:16.385662	78ce26a9-38b2-11f1-a213-000c29c66ae9
226	Герметичность укупора		number	\N	Герметичность укупора		f		\N	\N	2026-07-16 10:48:16.385662	1fbd6aae-3f0c-11f1-a213-000c29c66ae9
227	Качество наклейки этикетки		number	\N	Качество наклейки этикетки		f		\N	\N	2026-07-16 10:48:16.385662	a8502bca-3f0c-11f1-a213-000c29c66ae9
228	ОМЧ (качественный)		number	\N	ОМЧ (качественный)		f		\N	\N	2026-07-16 10:48:16.385663	621754c4-493e-11f1-a213-000c29c66ae9
229	М/О вредители (качественный)		number	\N	М/О вредители (качественный)		f		\N	\N	2026-07-16 10:48:16.385663	b86c4e6b-493e-11f1-a213-000c29c66ae9
230	М/О вредители, КОЕ	КОЕ	number	\N	М/О вредители, КОЕ		f		\N	\N	2026-07-16 10:48:16.385663	e051bfcd-493e-11f1-a213-000c29c66ae9
231	Диацетил, мг/л		number	\N	Диацетил, мг/л		f		\N	\N	2026-07-16 10:48:16.385664	2bf0aa6c-6959-11f1-a218-000c29c66ae9
232	Эфирная нота	балл	number	\N	Эфирная нота		f		\N	\N	2026-07-16 10:48:16.385664	e2e30929-76af-11f1-a218-000c29c66ae9
233	Солодовые тона	балл	number	\N	Солодовые тона		f		\N	\N	2026-07-16 10:48:16.385664	f1466b74-76af-11f1-a218-000c29c66ae9
234	Хмелевая горечь	балл	number	\N	Хмелевая горечь		f		\N	\N	2026-07-16 10:48:16.385665	0a787632-76b0-11f1-a218-000c29c66ae9
235	Пшеничная мягкость	балл	number	\N	Пшеничная мягкость		f		\N	\N	2026-07-16 10:48:16.385665	78661626-78ff-11f1-a218-000c29c66ae9
236	Аромат пшеничного пива (цитрус, гвоздика)	балл	number	\N	Аромат пшеничного пива (цитрус, гвоздика)		f		\N	\N	2026-07-16 10:48:16.385665	9f19c377-78ff-11f1-a218-000c29c66ae9
322	Дата		number	\N	Дата	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385695	e508d6d8-f353-11e6-aa1b-0021f60b3798
237	Солодовая сладость	балл	number	\N	Солодовая сладость		f		\N	\N	2026-07-16 10:48:16.385665	737c383b-7900-11f1-a218-000c29c66ae9
238	Пряный	балл	number	\N	Пряный		f		\N	\N	2026-07-16 10:48:16.385666	a21ae090-7900-11f1-a218-000c29c66ae9
239	Сливочно-карамельная полнота	балл	number	\N	Сливочно-карамельная полнота		f		\N	\N	2026-07-16 10:48:16.385666	35975071-790f-11f1-a218-000c29c66ae9
240	Карамельная сладость	балл	number	\N	Карамельная сладость		f		\N	\N	2026-07-16 10:48:16.385666	69afb0fc-790f-11f1-a218-000c29c66ae9
241	Сливочный вкус	балл	number	\N	Сливочный вкус		f		\N	\N	2026-07-16 10:48:16.385667	8cf67bc7-790f-11f1-a218-000c29c66ae9
242	Освежающая игристость	балл	number	\N	Освежающая игристость		f		\N	\N	2026-07-16 10:48:16.385667	d56b01cf-790f-11f1-a218-000c29c66ae9
243	Вишневый флейвор	балл	number	\N	Вишневый флейвор		f		\N	\N	2026-07-16 10:48:16.385667	698faac1-7911-11f1-a218-000c29c66ae9
244	Эфирная элевая нота	балл	number	\N	Эфирная элевая нота		f		\N	\N	2026-07-16 10:48:16.385667	7debcb9a-7911-11f1-a218-000c29c66ae9
245	МАлиново-ежевичный флейвор	балл	number	\N	МАлиново-ежевичный флейвор		f		\N	\N	2026-07-16 10:48:16.385668	ad403592-7911-11f1-a218-000c29c66ae9
246	Толщина, мкм	мкм	number	\N	Толщина, мкм		f		\N	\N	2026-07-16 10:48:16.385668	31222705-7ea7-11f1-a218-000c29c66ae9
247	Диаметр втулки, мм	мм	number	\N	Диаметр втулки, мм		f		\N	\N	2026-07-16 10:48:16.385668	5be2e60e-7ea7-11f1-a218-000c29c66ae9
248	Диаметр рулона (max), мм	мм	number	\N	Диаметр рулона (max), мм		f		\N	\N	2026-07-16 10:48:16.385669	8632c00b-7ea7-11f1-a218-000c29c66ae9
249	Продольная усадка, %	%	number	\N	Продольная усадка, %		f		\N	\N	2026-07-16 10:48:16.385669	a2cb27b2-7ea7-11f1-a218-000c29c66ae9
250	Поперечная усадка, %	%	number	\N	Поперечная усадка, %		f		\N	\N	2026-07-16 10:48:16.385669	bed32e4e-7ea7-11f1-a218-000c29c66ae9
251	Допуск		number	\N	Допуск		f		\N	\N	2026-07-16 10:48:16.385669	1ee5ad63-7ea8-11f1-a218-000c29c66ae9
252	Ширина, мм	мм	number	\N	Ширина, мм		f		\N	\N	2026-07-16 10:48:16.38567	30a99048-7ebd-11f1-a218-000c29c66ae9
253	Длина намотки, м	м	number	\N	Длина намотки, м		f		\N	\N	2026-07-16 10:48:16.38567	5be87c38-7ebd-11f1-a218-000c29c66ae9
254	Длина втулки, мм	мм	number	\N	Длина втулки, мм		f		\N	\N	2026-07-16 10:48:16.38567	9200e1a8-7ebd-11f1-a218-000c29c66ae9
255	Внутренний диаметр гильзы, мм	мм	number	\N	Внутренний диаметр гильзы, мм		f		\N	\N	2026-07-16 10:48:16.385671	b6eebeab-7ebd-11f1-a218-000c29c66ae9
256	Масса нетто, кг	кг	number	\N	Масса нетто, кг		f		\N	\N	2026-07-16 10:48:16.385671	e1474f75-7ebd-11f1-a218-000c29c66ae9
257	Ссылка на КУ		number	\N	Ссылка на КУ		f		\N	\N	2026-07-16 10:48:16.385671	4dbf4f45-7ebe-11f1-a218-000c29c66ae9
258	Прочность при разрыве (вдоль), МПа	МПа	number	\N	Прочность при разрыве (вдоль), МПа		f		\N	\N	2026-07-16 10:48:16.385671	2f23ba84-7ebf-11f1-a218-000c29c66ae9
259	Прочность при разрыве (поперек), МПа	МПа	number	\N	Прочность при разрыве (поперек), МПа		f		\N	\N	2026-07-16 10:48:16.385672	474821d1-7ebf-11f1-a218-000c29c66ae9
260	Относительное удлинение (вдоль), %	%	number	\N	Относительное удлинение (вдоль), %		f		\N	\N	2026-07-16 10:48:16.385672	6cc641c6-7ebf-11f1-a218-000c29c66ae9
261	Относительное длинение (поперек), %	%	number	\N	Относительное длинение (поперек), %		f		\N	\N	2026-07-16 10:48:16.385672	8c319acf-7ebf-11f1-a218-000c29c66ae9
262	Упругое восстановление, %	%	number	\N	Упругое восстановление, %		f		\N	\N	2026-07-16 10:48:16.385673	a4119331-7ebf-11f1-a218-000c29c66ae9
263	Прочность на прокол, Н	Н	number	\N	Прочность на прокол, Н		f		\N	\N	2026-07-16 10:48:16.385673	c11e65ce-7ebf-11f1-a218-000c29c66ae9
264	Предварительное растяжение, %	%	number	\N	Предварительное растяжение, %		f		\N	\N	2026-07-16 10:48:16.385673	dbd774e9-7ebf-11f1-a218-000c29c66ae9
265	Код учёта (ЕГАИС)		number	\N	Код учёта (ЕГАИС)		f		\N	\N	2026-07-16 10:48:16.385673	368ebcd1-7f55-11f1-a218-000c29c66ae9
266	Издательство (поставщик)		number	\N	Издательство (поставщик)		f		\N	\N	2026-07-16 10:48:16.385674	48289197-7f55-11f1-a218-000c29c66ae9
267	Наименование товара (этикетка)		number	\N	Наименование товара (этикетка)		f		\N	\N	2026-07-16 10:48:16.385674	ae14d413-7f55-11f1-a218-000c29c66ae9
268	Номер партии		number	\N	Номер партии		f		\N	\N	2026-07-16 10:48:16.385674	0c8729d4-7f56-11f1-a218-000c29c66ae9
269	Геометрический размер к эталону		number	\N	Геометрический размер к эталону		f		\N	\N	2026-07-16 10:48:16.385675	47475c1e-7f56-11f1-a218-000c29c66ae9
270	Цветовая гамма к эталону		number	\N	Цветовая гамма к эталону		f		\N	\N	2026-07-16 10:48:16.385675	873442cf-7f56-11f1-a218-000c29c66ae9
271	Текстовая часть к эталону		number	\N	Текстовая часть к эталону		f		\N	\N	2026-07-16 10:48:16.385675	b998966f-7f56-11f1-a218-000c29c66ae9
272	Межэтикеточное расстояние (этикетка), мм		number	\N	Межэтикеточное расстояние (этикетка), мм		f		\N	\N	2026-07-16 10:48:16.385675	f345421b-7f56-11f1-a218-000c29c66ae9
273	Кромка (этикетка), мм		number	\N	Кромка (этикетка), мм		f		\N	\N	2026-07-16 10:48:16.385676	1bc2bafd-7f57-11f1-a218-000c29c66ae9
274	Наименование товара (кольеретка)		number	\N	Наименование товара (кольеретка)		f		\N	\N	2026-07-16 10:48:16.385676	4ea568c9-7f57-11f1-a218-000c29c66ae9
275	Длина (этикетка), мм		number	\N	Длина (этикетка), мм		f		\N	\N	2026-07-16 10:48:16.385676	93320f63-7f57-11f1-a218-000c29c66ae9
276	Ширина (этикетка), мм		number	\N	Ширина (этикетка), мм		f		\N	\N	2026-07-16 10:48:16.385677	b5105b7f-7f57-11f1-a218-000c29c66ae9
277	Длина (кольеретка), мм		number	\N	Длина (кольеретка), мм		f		\N	\N	2026-07-16 10:48:16.385677	d7aead65-7f57-11f1-a218-000c29c66ae9
278	Ширина (кольеретка), мм		number	\N	Ширина (кольеретка), мм		f		\N	\N	2026-07-16 10:48:16.385677	0389d47a-7f58-11f1-a218-000c29c66ae9
323	Сорт		number	\N	Сорт	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385696	e508d6d9-f353-11e6-aa1b-0021f60b3798
279	Межэтикеточное расстояние (кольеретка), мм		number	\N	Межэтикеточное расстояние (кольеретка), мм		f		\N	\N	2026-07-16 10:48:16.385677	1ecb9d22-7f58-11f1-a218-000c29c66ae9
280	Кромка (кольеретка), мм		number	\N	Кромка (кольеретка), мм		f		\N	\N	2026-07-16 10:48:16.385678	3745042e-7f58-11f1-a218-000c29c66ae9
281	Ссылка на внешний вид комплекта		number	\N	Ссылка на внешний вид комплекта		f		\N	\N	2026-07-16 10:48:16.385678	1bc58f12-7f5e-11f1-a218-000c29c66ae9
282	Плотность материала (этикетка/кольеретка), гр/кв.м		number	\N	Плотность материала (этикетка/кольеретка), гр/кв.м		f		\N	\N	2026-07-16 10:48:16.385678	455c90cb-7f5e-11f1-a218-000c29c66ae9
283	Толщина материала (этикетка/кольеретка), мкм		number	\N	Толщина материала (этикетка/кольеретка), мкм		f		\N	\N	2026-07-16 10:48:16.385679	da0c3e5c-7f5e-11f1-a218-000c29c66ae9
284	Степень отлипания от подложки (этикетка/кольеретка)		number	\N	Степень отлипания от подложки (этикетка/кольеретка)		f		\N	\N	2026-07-16 10:48:16.385679	3301e0eb-7f5f-11f1-a218-000c29c66ae9
285	Наличие и качество вырубки (этикетка/кольеретка)		number	\N	Наличие и качество вырубки (этикетка/кольеретка)		f		\N	\N	2026-07-16 10:48:16.385679	a2712c9a-7f5f-11f1-a218-000c29c66ae9
286	Комментарий		number	\N	Комментарий		f		\N	\N	2026-07-16 10:48:16.38568	f97c08a2-803e-11f1-a218-000c29c66ae9
287	Содержание белка, %	%	number	\N	Содержание белка, %		f		\N	\N	2026-07-16 10:48:16.38568	34b7bd8a-80e9-11f1-a218-000c29c66ae9
288	Сорная примесь, %	%	number	\N	Сорная примесь, %		f		\N	\N	2026-07-16 10:48:16.38568	4d96ac43-80e9-11f1-a218-000c29c66ae9
289	Зерновая примесь, %	%	number	\N	Зерновая примесь, %		f		\N	\N	2026-07-16 10:48:16.385685	69b41d8c-80e9-11f1-a218-000c29c66ae9
290	Объемная доля двуокиси углерода, %	%	number	\N	Объемная доля двуокиси углерода, %		f		\N	\N	2026-07-16 10:48:16.385686	ad0aaa3f-80fc-11f1-a218-000c29c66ae9
291	Поставщик		number	\N	Поставщик		f		\N	\N	2026-07-16 10:48:16.385687	6500515a-80fe-11f1-a218-000c29c66ae9
292	Номер качественного удостоверения		number	\N	Номер качественного удостоверения		f		\N	\N	2026-07-16 10:48:16.385687	d2d10d09-80ff-11f1-a218-000c29c66ae9
293	Номер танка		number	\N	Номер танка	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385687	130c0a28-ee9f-11e6-aa1b-0021f60b3798
294	Экстрактивность горячего сусла		number	\N	Экстрактивность горячего сусла	Варка	f		\N	\N	2026-07-16 10:48:16.385687	306b4408-ee9f-11e6-aa1b-0021f60b3798
295	Экстрактивность сусла	%	number	\N	Экстрактивность сусла	Варка	f		\N	\N	2026-07-16 10:48:16.385688	36faa5e8-ee9f-11e6-aa1b-0021f60b3798
296	pH затора		number	\N	pH затора	Варка	f		\N	\N	2026-07-16 10:48:16.385688	3fdf9088-ee9f-11e6-aa1b-0021f60b3798
297	pH сусла		number	\N	pH сусла	Варка	f		\N	\N	2026-07-16 10:48:16.385688	4b3d6a68-ee9f-11e6-aa1b-0021f60b3798
298	Кислотность сусла		number	\N	Кислотность сусла	Варка	f		\N	\N	2026-07-16 10:48:16.385688	4b3d6a69-ee9f-11e6-aa1b-0021f60b3798
299	Цвет, EBC	ЕВС	number	\N	Цвет, EBC		f		\N	\N	2026-07-16 10:48:16.385689	6066e568-ee9f-11e6-aa1b-0021f60b3798
300	Горечь	IBU	number	\N	Горечь		f		\N	\N	2026-07-16 10:48:16.385689	77129398-ee9f-11e6-aa1b-0021f60b3798
301	Полифенолы		number	\N	Полифенолы	Варка	f		\N	\N	2026-07-16 10:48:16.385689	81e1e918-ee9f-11e6-aa1b-0021f60b3798
302	Видимый экстракт	% масс	number	\N	Видимый экстракт		f		\N	\N	2026-07-16 10:48:16.38569	9c3f7bb8-ee9f-11e6-aa1b-0021f60b3798
303	КДК, млн.	млн/см3	number	\N	КДК, млн.		f		\N	\N	2026-07-16 10:48:16.38569	9c3f7bb9-ee9f-11e6-aa1b-0021f60b3798
304	Начальные условия		number	\N	Начальные условия		f		\N	\N	2026-07-16 10:48:16.38569	c0b374ea-f351-11e6-aa1b-0021f60b3798
305	Номера варок		number	\N	Номера варок	Начальные условия	f		\N	\N	2026-07-16 10:48:16.38569	db837868-f351-11e6-aa1b-0021f60b3798
306	Начало заполнения, время		number	\N	Начало заполнения, время	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385691	ee3a93d8-f351-11e6-aa1b-0021f60b3798
307	ЦКТ полный, время		number	\N	ЦКТ полный, время	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385691	092dd6c8-f352-11e6-aa1b-0021f60b3798
308	Количество (Гл)		number	\N	Количество (Гл)	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385691	27a0a388-f352-11e6-aa1b-0021f60b3798
309	Количество дрожжевых клеток		number	\N	Количество дрожжевых клеток	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385692	3428305a-f352-11e6-aa1b-0021f60b3798
310	Количество мертвых дрожжей, %		number	\N	Количество мертвых дрожжей, %	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385692	44e57799-f352-11e6-aa1b-0021f60b3798
311	Гликоген, %		number	\N	Гликоген, %	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385692	503b3b28-f352-11e6-aa1b-0021f60b3798
312	Дрожжи из пропагатора		number	\N	Дрожжи из пропагатора	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385692	62086bc8-f352-11e6-aa1b-0021f60b3798
313	Количество дрожжей, кг		number	\N	Количество дрожжей, кг	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385693	6c8d23b8-f352-11e6-aa1b-0021f60b3798
314	Варница, Е%		number	\N	Варница, Е%	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385693	dd767959-f352-11e6-aa1b-0021f60b3798
315	ЦКТ полный, Е%		number	\N	ЦКТ полный, Е%	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385693	f2173c59-f352-11e6-aa1b-0021f60b3798
316	Температура брожения		number	\N	Температура брожения	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385694	1b4ba2f8-f353-11e6-aa1b-0021f60b3798
317	Температура дображивания		number	\N	Температура дображивания	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385694	21eedaf8-f353-11e6-aa1b-0021f60b3798
318	Температура		number	\N	Температура		f		\N	\N	2026-07-16 10:48:16.385694	3a5187f8-f353-11e6-aa1b-0021f60b3798
319	Урожай, кг		number	\N	Урожай, кг		f		\N	\N	2026-07-16 10:48:16.385694	7523d1d8-f353-11e6-aa1b-0021f60b3798
320	VDK		number	\N	VDK		f		\N	\N	2026-07-16 10:48:16.385695	83d850c8-f353-11e6-aa1b-0021f60b3798
324	Варка		number	\N	Варка		f		\N	\N	2026-07-16 10:48:16.385696	2a1242f8-f356-11e6-aa1b-0021f60b3798
325	Алкоголь	% об	number	\N	Алкоголь		f		\N	\N	2026-07-16 10:48:16.385696	542b3d38-f356-11e6-aa1b-0021f60b3798
326	Температура спуска		number	\N	Температура спуска		f		\N	\N	2026-07-16 10:48:16.385696	3c7c1732-1e8f-11eb-ab3d-b8ca3a612e81
327	Температура спусков		number	\N	Температура спусков	Начальные условия	f		\N	\N	2026-07-16 10:48:16.385697	3c7c1733-1e8f-11eb-ab3d-b8ca3a612e81
328	Тип посева		number	\N	Тип посева		f		\N	\N	2026-07-16 10:48:16.385697	3c7c1734-1e8f-11eb-ab3d-b8ca3a612e81
329	Формат		number	\N	Формат		f		\N	\N	2026-07-16 10:48:16.385697	3c7c1735-1e8f-11eb-ab3d-b8ca3a612e81
330	NBB-B/MRS-B		number	\N	NBB-B/MRS-B		f		\N	\N	2026-07-16 10:48:16.385698	3c4abd7f-510c-11ed-ab66-5cf9ddf10004
331	плотность		number	\N	плотность		f		\N	\N	2026-07-16 10:48:16.385698	11299ca0-6bea-11ed-ab67-5cf9ddf10004
332	Декларация		number	\N	Декларация		f		\N	\N	2026-07-16 10:48:16.385698	e087cd8b-6beb-11ed-ab67-5cf9ddf10004
333	Результат входного контроля		number	\N	Результат входного контроля		f		\N	\N	2026-07-16 10:48:16.385698	28fa396c-6bec-11ed-ab67-5cf9ddf10004
334	Логотип		number	\N	Логотип		f		\N	\N	2026-07-16 10:48:16.385699	5c372d76-6bec-11ed-ab67-5cf9ddf10004
335	NBB-C		number	\N	NBB-C		f		\N	\N	2026-07-16 10:48:16.385699	c80dde36-8082-11ed-ab67-5cf9ddf10004
336	Пастеризационные единицы (лево)		number	\N	Пастеризационные единицы (лево)		f		\N	\N	2026-07-16 10:48:16.385699	1e49883e-af89-11ee-ab76-5cf9ddf10004
337	Мероприятие		number	\N	Мероприятие		f		\N	\N	2026-07-16 10:48:16.385699	49d8da8b-e04a-11ee-ab7a-5cf9ddf10004
338	Экстрактивность холодного сусла		number	\N	Экстрактивность холодного сусла	Варка	f		\N	\N	2026-07-16 10:48:16.3857	e310ea8a-255e-11e9-abcf-00155d6ac508
339	Органолептика		number	\N	Органолептика		f		\N	\N	2026-07-16 10:48:16.3857	edeb5d3e-a277-11ef-abf7-5cf9ddf10004
340	Допуск к розливу		number	\N	Допуск к розливу		f		\N	\N	2026-07-16 10:48:16.3857	0b6072d8-a278-11ef-abf7-5cf9ddf10004
341	Показание поляриметра		number	\N	Показание поляриметра		f		\N	\N	2026-07-16 10:48:16.385701	6ce2dee8-f87b-11e8-b03b-00155d6ac508
342	Влажность,%		number	\N	Влажность,%	Солод	f		\N	\N	2026-07-16 10:48:16.385701	a80ed223-f87b-11e8-b03b-00155d6ac508
343	Мутность 90	ЕВС	number	\N	Мутность 90		f		\N	\N	2026-07-16 10:48:16.385701	b86a5ad2-45f5-11e7-b486-00155d6ac501
344	Мутность 25	ЕВС	number	\N	Мутность 25		f		\N	\N	2026-07-16 10:48:16.385702	c61cf337-45f5-11e7-b486-00155d6ac501
\.


--
-- Data for Name: indicator_library_versions; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.indicator_library_versions (id, indicator_id, version, name, unit, data_type, options, description, category, is_required, default_value, validation_rules, changed_by, change_type, change_notes, created_at) FROM stdin;
1	1	1	температура	С	number	\N	\N	\N	f	\N	\N	1	create	Показатель создан	2026-06-17 13:54:24.563972
2	1	2	температура	С	number	\N	\N	\N	f	\N	\N	1	update	Обновление показателя: температура	2026-06-18 05:40:00.55137
\.


--
-- Data for Name: indicator_values; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.indicator_values (id, process_log_id, indicator_id, value, text_value, is_normal, measured_at, notes) FROM stdin;
6	3	2	13	\N	f	2026-07-17 10:36:46.557112	\N
7	3	3	5.5	\N	t	2026-07-17 10:36:46.557115	\N
12	2	2	13	\N	f	2026-07-17 10:46:28.83049	\N
13	2	3	5.5	\N	t	2026-07-17 10:46:28.830495	\N
14	1	2	11	\N	t	2026-07-17 10:47:22.43814	\N
15	1	3	5	\N	f	2026-07-17 10:47:22.438143	\N
16	4	2	13	\N	f	2026-07-24 12:21:07.017321	\N
17	4	3	5.5	\N	t	2026-07-24 12:21:07.017323	\N
18	5	2	15	\N	f	2026-07-30 09:38:46.272527	\N
19	5	3	5	\N	f	2026-07-30 09:38:46.272534	\N
\.


--
-- Data for Name: indicators; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.indicators (id, name, unit, min_value, max_value, data_type, options, analysis_type_id) FROM stdin;
1	Экстрактивность	%	11	12	number	\N	1
2	Кислотность	pH	5.2	5.8	number	\N	1
\.


--
-- Data for Name: integration_configs; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.integration_configs (id, name, base_url, api_key, username, password, timeout, verify_ssl, is_active, created_at, updated_at, endpoint, indicators_endpoint, templates_endpoint, plans_endpoint) FROM stdin;
1	1c	http://host.docker.internal:8899	\N	obmenapi1c	Qasd33!!	30	f	t	2026-07-16 10:24:28.925757+00	2026-07-17 10:55:32.910553+00	/erp_24/hs/labindicators/indicators	/erp_24/hs/labindicators/indicators	/erp_24/hs/labindicators/templates	/erp_24/hs/labindicators/plans
\.


--
-- Data for Name: plan_items; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.plan_items (id, plan_id, template_id, batch_number, sort_order, is_completed, completed_report_id) FROM stdin;
1	1	1	клен	0	t	1
2	2	1	yt6784	0	t	2
3	3	1	рст2607	0	f	\N
4	4	1	р2607	0	f	\N
5	5	1	hcn3007	0	t	5
\.


--
-- Data for Name: preset_indicators; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.preset_indicators (id, preset_id, indicator_id, min_value, max_value, sort_order, is_required) FROM stdin;
\.


--
-- Data for Name: presets; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.presets (id, name, description, category, created_at, created_by) FROM stdin;
\.


--
-- Data for Name: process_logs; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.process_logs (id, batch_number, analysis_type_id, created_by, status, started_at, completed_at, notes) FROM stdin;
1	клен	1	1	PENDING	2026-06-17 13:55:37.658376	\N	\N
2	yt6784	1	2	PENDING	2026-07-17 10:35:52.297951	\N	\N
3	uu698	1	1	PENDING	2026-07-17 10:36:46.553752	\N	\N
4	рст2607	1	1	PENDING	2026-07-24 12:21:07.009639	\N	\N
5	hcn3007	1	1	PENDING	2026-07-30 09:38:46.259076	\N	\N
\.


--
-- Data for Name: template_indicators; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.template_indicators (id, template_id, indicator_id, min_value, max_value, sort_order, is_custom, template_notes, external_id) FROM stdin;
7	1	2	11	12	0	f	\N	10
8	1	3	5.2	5.8	1	f	\N	11
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: wwwanalys_user
--

COPY public.users (id, username, email, hashed_password, is_active, is_admin) FROM stdin;
1	admin	admin@brewery.com	$5$rounds=535000$tCW5tyvJGgB/6yAI$Xq1YzrQl1dXynricSUoU5MlUPQBwQlD8LvRlBXj1j21	t	t
2	lab	lab@brewery.com	$5$rounds=535000$OkbBA0hLM7tmibh6$2V2Jz6FLFj1R7ALIJBUX.JmDCb6IV4liqDMsje9uZk9	t	f
3	testuser	test@example.com	$5$rounds=535000$h84eaJmuaWhclKaC$HqWZ8kjW3nRxEKss1rA.rlbJz/VwAE7XwItZc4nrlbA	t	t
\.


--
-- Name: analysis_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.analysis_plans_id_seq', 5, true);


--
-- Name: analysis_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.analysis_types_id_seq', 1, true);


--
-- Name: indicator_library_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.indicator_library_id_seq', 348, true);


--
-- Name: indicator_library_versions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.indicator_library_versions_id_seq', 2, true);


--
-- Name: indicator_values_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.indicator_values_id_seq', 19, true);


--
-- Name: indicators_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.indicators_id_seq', 2, true);


--
-- Name: integration_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.integration_configs_id_seq', 1, true);


--
-- Name: plan_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.plan_items_id_seq', 5, true);


--
-- Name: preset_indicators_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.preset_indicators_id_seq', 1, false);


--
-- Name: presets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.presets_id_seq', 1, false);


--
-- Name: process_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.process_logs_id_seq', 5, true);


--
-- Name: template_indicators_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.template_indicators_id_seq', 8, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wwwanalys_user
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: analysis_plans analysis_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_plans
    ADD CONSTRAINT analysis_plans_pkey PRIMARY KEY (id);


--
-- Name: analysis_types analysis_types_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_types
    ADD CONSTRAINT analysis_types_pkey PRIMARY KEY (id);


--
-- Name: indicator_library indicator_library_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_library
    ADD CONSTRAINT indicator_library_pkey PRIMARY KEY (id);


--
-- Name: indicator_library_versions indicator_library_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_library_versions
    ADD CONSTRAINT indicator_library_versions_pkey PRIMARY KEY (id);


--
-- Name: indicator_values indicator_values_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_values
    ADD CONSTRAINT indicator_values_pkey PRIMARY KEY (id);


--
-- Name: indicators indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicators
    ADD CONSTRAINT indicators_pkey PRIMARY KEY (id);


--
-- Name: integration_configs integration_configs_name_key; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.integration_configs
    ADD CONSTRAINT integration_configs_name_key UNIQUE (name);


--
-- Name: integration_configs integration_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.integration_configs
    ADD CONSTRAINT integration_configs_pkey PRIMARY KEY (id);


--
-- Name: plan_items plan_items_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.plan_items
    ADD CONSTRAINT plan_items_pkey PRIMARY KEY (id);


--
-- Name: preset_indicators preset_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.preset_indicators
    ADD CONSTRAINT preset_indicators_pkey PRIMARY KEY (id);


--
-- Name: presets presets_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.presets
    ADD CONSTRAINT presets_pkey PRIMARY KEY (id);


--
-- Name: process_logs process_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.process_logs
    ADD CONSTRAINT process_logs_pkey PRIMARY KEY (id);


--
-- Name: template_indicators template_indicators_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.template_indicators
    ADD CONSTRAINT template_indicators_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_analysis_plans_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_analysis_plans_id ON public.analysis_plans USING btree (id);


--
-- Name: ix_analysis_plans_plan_date; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_analysis_plans_plan_date ON public.analysis_plans USING btree (plan_date);


--
-- Name: ix_analysis_types_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_analysis_types_id ON public.analysis_types USING btree (id);


--
-- Name: ix_analysis_types_name; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE UNIQUE INDEX ix_analysis_types_name ON public.analysis_types USING btree (name);


--
-- Name: ix_indicator_library_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicator_library_id ON public.indicator_library USING btree (id);


--
-- Name: ix_indicator_library_name; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE UNIQUE INDEX ix_indicator_library_name ON public.indicator_library USING btree (name);


--
-- Name: ix_indicator_library_versions_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicator_library_versions_id ON public.indicator_library_versions USING btree (id);


--
-- Name: ix_indicator_library_versions_indicator_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicator_library_versions_indicator_id ON public.indicator_library_versions USING btree (indicator_id);


--
-- Name: ix_indicator_values_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicator_values_id ON public.indicator_values USING btree (id);


--
-- Name: ix_indicators_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicators_id ON public.indicators USING btree (id);


--
-- Name: ix_indicators_name; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_indicators_name ON public.indicators USING btree (name);


--
-- Name: ix_integration_configs_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_integration_configs_id ON public.integration_configs USING btree (id);


--
-- Name: ix_plan_items_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_plan_items_id ON public.plan_items USING btree (id);


--
-- Name: ix_preset_indicators_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_preset_indicators_id ON public.preset_indicators USING btree (id);


--
-- Name: ix_presets_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_presets_id ON public.presets USING btree (id);


--
-- Name: ix_presets_name; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE UNIQUE INDEX ix_presets_name ON public.presets USING btree (name);


--
-- Name: ix_process_logs_batch_number; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_process_logs_batch_number ON public.process_logs USING btree (batch_number);


--
-- Name: ix_process_logs_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_process_logs_id ON public.process_logs USING btree (id);


--
-- Name: ix_template_indicators_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_template_indicators_id ON public.template_indicators USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: wwwanalys_user
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: analysis_plans analysis_plans_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_plans
    ADD CONSTRAINT analysis_plans_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: analysis_types analysis_types_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.analysis_types
    ADD CONSTRAINT analysis_types_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: indicator_library_versions indicator_library_versions_indicator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_library_versions
    ADD CONSTRAINT indicator_library_versions_indicator_id_fkey FOREIGN KEY (indicator_id) REFERENCES public.indicator_library(id) ON DELETE CASCADE;


--
-- Name: indicator_values indicator_values_indicator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_values
    ADD CONSTRAINT indicator_values_indicator_id_fkey FOREIGN KEY (indicator_id) REFERENCES public.indicator_library(id);


--
-- Name: indicator_values indicator_values_process_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicator_values
    ADD CONSTRAINT indicator_values_process_log_id_fkey FOREIGN KEY (process_log_id) REFERENCES public.process_logs(id);


--
-- Name: indicators indicators_analysis_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.indicators
    ADD CONSTRAINT indicators_analysis_type_id_fkey FOREIGN KEY (analysis_type_id) REFERENCES public.analysis_types(id);


--
-- Name: plan_items plan_items_completed_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.plan_items
    ADD CONSTRAINT plan_items_completed_report_id_fkey FOREIGN KEY (completed_report_id) REFERENCES public.process_logs(id);


--
-- Name: plan_items plan_items_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.plan_items
    ADD CONSTRAINT plan_items_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.analysis_plans(id) ON DELETE CASCADE;


--
-- Name: plan_items plan_items_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.plan_items
    ADD CONSTRAINT plan_items_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.analysis_types(id);


--
-- Name: preset_indicators preset_indicators_indicator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.preset_indicators
    ADD CONSTRAINT preset_indicators_indicator_id_fkey FOREIGN KEY (indicator_id) REFERENCES public.indicator_library(id) ON DELETE CASCADE;


--
-- Name: preset_indicators preset_indicators_preset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.preset_indicators
    ADD CONSTRAINT preset_indicators_preset_id_fkey FOREIGN KEY (preset_id) REFERENCES public.presets(id) ON DELETE CASCADE;


--
-- Name: presets presets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.presets
    ADD CONSTRAINT presets_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: process_logs process_logs_analysis_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.process_logs
    ADD CONSTRAINT process_logs_analysis_type_id_fkey FOREIGN KEY (analysis_type_id) REFERENCES public.analysis_types(id);


--
-- Name: process_logs process_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.process_logs
    ADD CONSTRAINT process_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: template_indicators template_indicators_indicator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.template_indicators
    ADD CONSTRAINT template_indicators_indicator_id_fkey FOREIGN KEY (indicator_id) REFERENCES public.indicator_library(id) ON DELETE CASCADE;


--
-- Name: template_indicators template_indicators_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wwwanalys_user
--

ALTER TABLE ONLY public.template_indicators
    ADD CONSTRAINT template_indicators_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.analysis_types(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict zgWVnihFR23IhkgV5iUFnvaJmSwEFWka5LWaG3PDdNEbl8ug20ajM7xEMLlsUnv

