CREATE TABLE "shop" (
  "id" SERIAL PRIMARY KEY,
  "name" varchar,
  "address" varchar,
  "postcode" int,
  "city" varchar,
  "siret" varchar,
  "phone" varchar,
  "created_at" timestamp DEFAULT 'now()'
);

CREATE TABLE "receipt" (
  "id" SERIAL PRIMARY KEY,
  "shop_id" int,
  "total_price" float,
  "file" varchar,
  "date" timestamp DEFAULT 'now()',
  "prices_pos_top" integer,
  "prices_pos_left" integer,
  "prices_pos_width" integer,
  "prices_pos_height" integer,
  "img_width" integer,
  "img_height" integer,
  "pos_y_total_price" integer
);

CREATE TABLE "paid_product" (
  "id" SERIAL PRIMARY KEY,
  "receipt_id" int,
  "product_group_id" int,
  "quantity" float,
  "price" float,
  "unit_price" float,
  "pos_top" float,
  "pos_left" float,
  "pos_width" float,
  "pos_height" float
);

CREATE TABLE "product_group" (
  "id" SERIAL PRIMARY KEY,
  "name" varchar,
  "created_at" timestamp DEFAULT 'now()'
);

CREATE TABLE "product" (
  "id" SERIAL PRIMARY KEY,
  "name" varchar,
  "created_at" timestamp DEFAULT 'now()',
  "product_group_id" int
);

ALTER TABLE "receipt" ADD FOREIGN KEY ("shop_id") REFERENCES "shop" ("id");

ALTER TABLE "paid_product" ADD FOREIGN KEY ("receipt_id") REFERENCES "receipt" ("id");

ALTER TABLE "paid_product" ADD FOREIGN KEY ("product_group_id") REFERENCES "product_group" ("id");

ALTER TABLE "product" ADD FOREIGN KEY ("product_group_id") REFERENCES "product_group" ("id");

CREATE UNIQUE INDEX ON "receipt" ("file");

CREATE UNIQUE INDEX ON "product_group" ("name");

CREATE UNIQUE INDEX ON "product" ("name");
