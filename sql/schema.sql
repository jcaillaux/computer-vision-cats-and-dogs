CREATE TABLE imagemetadata (
	hash varchar NOT NULL,
	filename varchar NOT NULL,
	ext_type varchar NOT NULL,
	size_w int4 NOT NULL,
	size_h int4 NOT NULL,
	color_mode varchar NOT NULL,
	CONSTRAINT imagemetadata_pkey PRIMARY KEY (hash)
);

CREATE TABLE predictionlog (
	"uuid" varchar NOT NULL,
	"timestamp" timestamp NOT NULL,
	prob_cat float8 NULL,
	prob_dog float8 NULL,
	inference_time_ms float8 NOT NULL,
	success bool NOT NULL,
	model_version varchar NOT NULL,
	image_id varchar NOT NULL,
	CONSTRAINT predictionlog_pkey PRIMARY KEY (uuid),
	CONSTRAINT predictionlog_image_id_fkey FOREIGN KEY (image_id) REFERENCES imagemetadata(hash)
);

CREATE TABLE feedback (
	"uuid" varchar NOT NULL,
	"timestamp" timestamp NOT NULL,
	grade varchar NOT NULL,
	CONSTRAINT feedback_pkey PRIMARY KEY (uuid),
	CONSTRAINT feedback_uuid_fkey FOREIGN KEY ("uuid") REFERENCES predictionlog("uuid")
);