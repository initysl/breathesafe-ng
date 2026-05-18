"""
BreatheSafe NG — Database Schemas
Run the SQL block below directly in Supabase SQL Editor to create all tables.
"""
CREATE_TABLES_SQL = """

-- ─────────────────────────────────────────
-- 1. Raw AQI Readings (from OpenAQ)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_aqi_readings (
    id              BIGSERIAL PRIMARY KEY,
    city            VARCHAR(50) NOT NULL,
    parameter       VARCHAR(20) NOT NULL,   -- pm25, no2, co, etc.
    value           FLOAT NOT NULL,
    unit            VARCHAR(20) NOT NULL,   -- µg/m³, ppm, etc.
    timestamp_utc   TIMESTAMPTZ NOT NULL,
    location_id     VARCHAR(50),            -- OpenAQ location ID
    source          VARCHAR(50) DEFAULT 'openaq',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast city + time queries
CREATE INDEX IF NOT EXISTS idx_aqi_city_time
    ON raw_aqi_readings (city, timestamp_utc DESC);

-- Prevent duplicate readings
CREATE UNIQUE INDEX IF NOT EXISTS idx_aqi_unique
    ON raw_aqi_readings (city, parameter, timestamp_utc, location_id);


-- ─────────────────────────────────────────
-- 2. Raw Weather Readings (from OpenWeatherMap)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_weather (
    id                  BIGSERIAL PRIMARY KEY,
    city                VARCHAR(50) NOT NULL,
    timestamp_utc       TIMESTAMPTZ NOT NULL,
    temperature_c       FLOAT,
    humidity_pct        FLOAT,
    wind_speed_ms       FLOAT,
    wind_direction_deg  FLOAT,
    wind_sin            FLOAT,              -- Encoded wind direction
    wind_cos            FLOAT,              -- Encoded wind direction
    rainfall_1h_mm      FLOAT DEFAULT 0,
    pressure_hpa        FLOAT,
    visibility_m        FLOAT,
    weather_description VARCHAR(100),
    source              VARCHAR(50) DEFAULT 'openweathermap',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_city_time
    ON raw_weather (city, timestamp_utc DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_unique
    ON raw_weather (city, timestamp_utc);


-- ─────────────────────────────────────────
-- 3. Processed Features (ML-ready merged data)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS processed_features (
    id                  BIGSERIAL PRIMARY KEY,
    city                VARCHAR(50) NOT NULL,
    timestamp_utc       TIMESTAMPTZ NOT NULL,

    -- Pollutants
    pm25                FLOAT,
    pm10                FLOAT,
    no2                 FLOAT,
    o3                  FLOAT,
    co                  FLOAT,
    so2                 FLOAT,
    aqi_value           FLOAT,              -- Computed AQI index
    aqi_category        VARCHAR(30),        -- Good, Moderate, Unhealthy, etc.

    -- Weather
    temperature_c       FLOAT,
    humidity_pct        FLOAT,
    wind_speed_ms       FLOAT,
    wind_sin            FLOAT,
    wind_cos            FLOAT,
    rainfall_1h_mm      FLOAT,
    pressure_hpa        FLOAT,

    -- Time features
    hour_of_day         SMALLINT,
    day_of_week         SMALLINT,
    month               SMALLINT,
    is_weekend          BOOLEAN,
    is_harmattan        BOOLEAN,            -- Oct-Feb flag

    -- Lag features (auto-computed during feature engineering)
    pm25_lag_1h         FLOAT,
    pm25_lag_3h         FLOAT,
    pm25_lag_6h         FLOAT,
    pm25_lag_24h        FLOAT,
    pm25_rolling_24h    FLOAT,
    aqi_lag_1h          FLOAT,
    aqi_lag_6h          FLOAT,
    aqi_lag_24h         FLOAT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_features_city_time
    ON processed_features (city, timestamp_utc DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_features_unique
    ON processed_features (city, timestamp_utc);


-- ─────────────────────────────────────────
-- 4. AQI Forecasts (model output)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aqi_forecasts (
    id                  BIGSERIAL PRIMARY KEY,
    city                VARCHAR(50) NOT NULL,
    forecast_made_at    TIMESTAMPTZ NOT NULL,   -- When forecast was made
    forecast_for        TIMESTAMPTZ NOT NULL,   -- What time it's predicting
    horizon_hours       SMALLINT NOT NULL,      -- 1, 6, 12, or 24
    predicted_aqi       FLOAT NOT NULL,
    predicted_category  VARCHAR(30),
    model_version       VARCHAR(50),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forecasts_city_time
    ON aqi_forecasts (city, forecast_for DESC);


-- ─────────────────────────────────────────
-- 5. Alert Subscriptions
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    city            VARCHAR(50) NOT NULL,
    channel         VARCHAR(20) NOT NULL,   -- whatsapp, sms, email
    contact         VARCHAR(100) NOT NULL,  -- phone number or email
    threshold       VARCHAR(30) DEFAULT 'unhealthy',  -- AQI category trigger
    is_active       BOOLEAN DEFAULT TRUE,
    subscribed_at   TIMESTAMPTZ DEFAULT NOW(),
    last_alerted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subscription_unique
    ON alert_subscriptions (city, channel, contact);


-- ─────────────────────────────────────────
-- 6. Alert Log (audit trail of sent alerts)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_log (
    id                  BIGSERIAL PRIMARY KEY,
    subscription_id     BIGINT REFERENCES alert_subscriptions(id),
    city                VARCHAR(50),
    channel             VARCHAR(20),
    contact             VARCHAR(100),
    predicted_aqi       FLOAT,
    aqi_category        VARCHAR(30),
    message_sent        TEXT,
    sent_at             TIMESTAMPTZ DEFAULT NOW(),
    delivery_status     VARCHAR(20) DEFAULT 'sent'  -- sent, delivered, failed
);


-- ─────────────────────────────────────────
-- 7. Pipeline Run Log (monitor data health)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_log (
    id              BIGSERIAL PRIMARY KEY,
    run_type        VARCHAR(50) NOT NULL,   -- openaq_fetch, weather_fetch, preprocess, etc.
    city            VARCHAR(50),
    status          VARCHAR(20) NOT NULL,   -- success, partial, failed
    records_fetched INTEGER DEFAULT 0,
    records_saved   INTEGER DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ DEFAULT NOW()
);

"""
