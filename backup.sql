--
-- PostgreSQL database dump
--

\restrict dxgnieub6LO87s0zGCq8QgbEYvFj30UOXG4ITizIDCWWMsC02Odr9U7VBAwrxFf

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cities (
    id integer NOT NULL,
    name_ar text NOT NULL,
    name_en text NOT NULL,
    lat double precision NOT NULL,
    lon double precision NOT NULL
);


ALTER TABLE public.cities OWNER TO postgres;

--
-- Name: weather_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.weather_history (
    id integer NOT NULL,
    city_id integer NOT NULL,
    temperature real,
    humidity integer,
    description text,
    wind_speed real,
    last_update timestamp without time zone DEFAULT now()
);


ALTER TABLE public.weather_history OWNER TO postgres;

--
-- Name: weather_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.weather_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weather_history_id_seq OWNER TO postgres;

--
-- Name: weather_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.weather_history_id_seq OWNED BY public.weather_history.id;


--
-- Name: weather_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weather_history ALTER COLUMN id SET DEFAULT nextval('public.weather_history_id_seq'::regclass);


--
-- Data for Name: cities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cities (id, name_ar, name_en, lat, lon) FROM stdin;
1	دمشق	Damascus	33.5138	36.2765
2	ريف دمشق	Rif Dimashq	33.5167	36.4316
3	حلب	Aleppo	36.2021	37.1612
4	حمص	Homs	34.7324	36.7234
5	حماة	Hama	35.1318	36.7578
6	اللاذقية	Latakia	35.5317	35.7796
7	طرطوس	Tartus	34.8959	35.8866
8	إدلب	Idlib	35.9306	36.6339
9	درعا	Daraa	32.6189	36.1021
10	السويداء	As-Suwayda	32.709	36.5695
11	القنيطرة	Quneitra	33.1259	35.8246
12	دير الزور	Deir ez-Zor	35.3359	40.1408
13	الحسكة	Al-Hasakah	36.5079	40.7477
14	الرقة	Raqqa	35.9528	39.0193
\.


--
-- Data for Name: weather_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.weather_history (id, city_id, temperature, humidity, description, wind_speed, last_update) FROM stdin;
1	13	23.45	42	سماء صافية	2.94	2026-04-30 18:38:06.946642
2	8	20.49	57	سماء صافية	2.66	2026-04-30 18:38:37.298359
3	6	20.49	70	سماء صافية	1.28	2026-04-30 18:38:48.604875
4	3	21.77	49	سماء صافية	4.84	2026-04-30 18:38:58.300304
5	2	24.4	27	سماء صافية	2.57	2026-04-30 18:40:01.039022
6	1	24.52	26	سماء صافية	0.45	2026-04-30 18:40:04.789627
7	11	16.56	61	سماء صافية	2.62	2026-04-30 18:40:08.145788
8	9	21.39	48	سماء صافية	5.8	2026-04-30 18:40:15.847595
9	10	19.63	36	غائم جزئي	4.6	2026-04-30 18:40:18.874113
10	5	22.43	49	سماء صافية	4.37	2026-04-30 18:47:05.318408
11	13	22.33	44	سماء صافية	3.03	2026-04-30 20:26:46.020155
12	12	24.75	30	سماء صافية	2.9	2026-04-30 20:36:23.66425
13	14	21.91	41	سماء صافية	1.68	2026-04-30 23:15:43.16922
14	4	17.58	51	سماء صافية	1.44	2026-04-30 23:21:14.813653
15	8	16.69	67	سماء صافية	2.15	2026-04-30 23:21:22.381651
16	6	18.54	80	سماء صافية	2.3	2026-04-30 23:21:31.083458
\.


--
-- Name: weather_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.weather_history_id_seq', 16, true);


--
-- Name: cities cities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cities
    ADD CONSTRAINT cities_pkey PRIMARY KEY (id);


--
-- Name: weather_history weather_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weather_history
    ADD CONSTRAINT weather_history_pkey PRIMARY KEY (id);


--
-- Name: weather_history weather_history_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.weather_history
    ADD CONSTRAINT weather_history_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.cities(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict dxgnieub6LO87s0zGCq8QgbEYvFj30UOXG4ITizIDCWWMsC02Odr9U7VBAwrxFf

