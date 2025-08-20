# HappyRobot FDE Database Schema

## Overview
This document defines the complete PostgreSQL database schema for the HappyRobot FDE platform. The schema is designed to support high-volume carrier interactions, load matching, negotiation tracking, and comprehensive analytics.

## Database Configuration

### Connection Pool Settings
```yaml
max_connections: 200
pool_size: 20
max_overflow: 10
pool_timeout: 30
pool_recycle: 3600
echo: false
```

### Performance Optimizations
- Connection pooling via SQLAlchemy
- Prepared statements for frequent queries
- Batch operations for bulk inserts
- Read replicas for analytics (future)

## Schema Design Principles

1. **UUID Primary Keys**: All tables use UUID v4 for distributed ID generation
2. **Soft Deletes**: Critical records use `deleted_at` timestamps instead of hard deletes
3. **Audit Fields**: All tables include `created_at`, `updated_at`, and `created_by`
4. **JSONB for Flexibility**: Semi-structured data stored in JSONB columns
5. **Optimistic Locking**: Version columns for concurrent update handling
6. **Partitioning Ready**: Large tables designed for future date-based partitioning

---

## Core Tables

### 1. carriers
Stores carrier information.

```sql
CREATE TABLE carriers (
    -- Primary Key
    carrier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Carrier Identification
    mc_number VARCHAR(20) UNIQUE NOT NULL,
    dot_number VARCHAR(20),

    -- Company Information
    legal_name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255),

    -- Status Information
    entity_type VARCHAR(50) NOT NULL, -- CARRIER, BROKER, BOTH
    operating_status VARCHAR(50) NOT NULL, -- AUTHORIZED, NOT_AUTHORIZED, OUT_OF_SERVICE
    status VARCHAR(20) NOT NULL, -- ACTIVE, INACTIVE

    -- Insurance Information
    insurance_on_file BOOLEAN DEFAULT FALSE,
    bipd_required NUMERIC(12, 2),
    bipd_on_file NUMERIC(12, 2),
    cargo_required NUMERIC(12, 2),
    cargo_on_file NUMERIC(12, 2),
    bond_required NUMERIC(12, 2),
    bond_on_file NUMERIC(12, 2),

    -- Safety Information
    safety_rating VARCHAR(20), -- SATISFACTORY, CONDITIONAL, UNSATISFACTORY
    safety_rating_date DATE,
    safety_scores JSONB, -- Stores BASICS scores

    -- Contact Information
    primary_contact JSONB, -- {name, phone, email, title}
    address JSONB, -- {street, city, state, zip, country}

    -- Eligibility
    is_eligible BOOLEAN GENERATED ALWAYS AS (
        operating_status = 'AUTHORIZED_FOR_HIRE'
        AND status = 'ACTIVE'
        AND insurance_on_file = TRUE
    ) STORED,
    eligibility_notes TEXT,

    -- Verification
    last_verified_at TIMESTAMPTZ,
    verification_source VARCHAR(50), -- EXTERNAL_API, MANUAL, THIRD_PARTY

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_carriers_mc_number ON carriers(mc_number);
CREATE INDEX idx_carriers_dot_number ON carriers(dot_number);
CREATE INDEX idx_carriers_eligible ON carriers(is_eligible) WHERE is_eligible = TRUE;
CREATE INDEX idx_carriers_status ON carriers(operating_status, status);
CREATE INDEX idx_carriers_verified ON carriers(last_verified_at);

-- Triggers
CREATE TRIGGER update_carriers_updated_at
    BEFORE UPDATE ON carriers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 2. loads
Stores available freight loads.

```sql
CREATE TABLE loads (
    -- Primary Key
    load_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Load Reference
    reference_number VARCHAR(50) UNIQUE,
    external_id VARCHAR(100), -- ID from external system

    -- Origin Information
    origin_city VARCHAR(100) NOT NULL,
    origin_state CHAR(2) NOT NULL,
    origin_zip VARCHAR(10),
    origin_coordinates JSONB, -- {lat, lng}
    origin_facility JSONB, -- {name, address, contact, hours}

    -- Destination Information
    destination_city VARCHAR(100) NOT NULL,
    destination_state CHAR(2) NOT NULL,
    destination_zip VARCHAR(10),
    destination_coordinates JSONB, -- {lat, lng}
    destination_facility JSONB, -- {name, address, contact, hours}

    -- Schedule
    pickup_date DATE NOT NULL,
    pickup_time_start TIME,
    pickup_time_end TIME,
    pickup_appointment_required BOOLEAN DEFAULT FALSE,

    delivery_date DATE NOT NULL,
    delivery_time_start TIME,
    delivery_time_end TIME,
    delivery_appointment_required BOOLEAN DEFAULT FALSE,

    -- Equipment Requirements
    equipment_type VARCHAR(50) NOT NULL, -- 53-foot van, Reefer, Flatbed, etc.
    equipment_requirements JSONB, -- {tarps, straps, temp_control, etc}

    -- Load Details
    weight INTEGER NOT NULL, -- in pounds
    pieces INTEGER,
    commodity_type VARCHAR(100),
    commodity_description TEXT,
    dimensions VARCHAR(100), -- LxWxH
    hazmat BOOLEAN DEFAULT FALSE,
    hazmat_class VARCHAR(20),

    -- Distance and Route
    miles INTEGER NOT NULL,
    estimated_transit_hours INTEGER,
    route_notes TEXT,

    -- Pricing
    loadboard_rate NUMERIC(10, 2) NOT NULL,
    fuel_surcharge NUMERIC(10, 2) DEFAULT 0,
    accessorials JSONB, -- [{type, amount, description}]
    total_rate NUMERIC(10, 2) GENERATED ALWAYS AS (
        loadboard_rate + COALESCE(fuel_surcharge, 0)
    ) STORED,
    rate_per_mile NUMERIC(8, 4) GENERATED ALWAYS AS (
        CASE WHEN miles > 0
        THEN (loadboard_rate + COALESCE(fuel_surcharge, 0)) / miles
        ELSE 0 END
    ) STORED,

    -- Negotiation Parameters
    minimum_rate NUMERIC(10, 2),
    maximum_rate NUMERIC(10, 2),
    target_rate NUMERIC(10, 2),
    auto_accept_threshold NUMERIC(10, 2),

    -- Broker/Customer Information
    broker_company VARCHAR(255),
    broker_contact JSONB, -- {name, phone, email}
    customer_name VARCHAR(255),

    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'AVAILABLE',
    -- AVAILABLE, PENDING, BOOKED, IN_TRANSIT, DELIVERED, CANCELLED
    status_changed_at TIMESTAMPTZ DEFAULT NOW(),
    booked_by_carrier_id UUID REFERENCES carriers(carrier_id),
    booked_at TIMESTAMPTZ,

    -- Special Instructions
    special_requirements TEXT[],
    notes TEXT,
    internal_notes TEXT, -- Not shown to carriers

    -- Urgency and Priority
    urgency VARCHAR(20) DEFAULT 'NORMAL', -- LOW, NORMAL, HIGH, CRITICAL
    priority_score INTEGER DEFAULT 50, -- 0-100

    -- Visibility
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,

    -- Metadata
    source VARCHAR(50), -- DAT, MANUAL, API, etc.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    deleted_at TIMESTAMPTZ,
    version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_loads_reference ON loads(reference_number);
CREATE INDEX idx_loads_status ON loads(status) WHERE status = 'AVAILABLE';
CREATE INDEX idx_loads_equipment ON loads(equipment_type);
CREATE INDEX idx_loads_origin ON loads(origin_state, origin_city);
CREATE INDEX idx_loads_destination ON loads(destination_state, destination_city);
CREATE INDEX idx_loads_pickup_date ON loads(pickup_date);
CREATE INDEX idx_loads_miles ON loads(miles);
CREATE INDEX idx_loads_rate ON loads(loadboard_rate);
CREATE INDEX idx_loads_rpm ON loads(rate_per_mile);
CREATE INDEX idx_loads_active ON loads(is_active, expires_at)
    WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_loads_booked ON loads(booked_by_carrier_id, booked_at);

-- Triggers
CREATE TRIGGER update_loads_updated_at
    BEFORE UPDATE ON loads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 3. calls
Stores call interaction data.

```sql
CREATE TABLE calls (
    -- Primary Key
    call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Call Identification
    external_call_id VARCHAR(100), -- From HappyRobot or phone system
    session_id VARCHAR(100),

    -- Carrier Information
    mc_number VARCHAR(20),
    carrier_id UUID REFERENCES carriers(carrier_id),
    caller_phone VARCHAR(20),
    caller_name VARCHAR(100),

    -- Load Association
    load_id UUID REFERENCES loads(load_id),
    multiple_loads_discussed UUID[], -- Array of load IDs discussed

    -- Call Metadata
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- Call Type and Channel
    call_type VARCHAR(30) NOT NULL, -- INBOUND, OUTBOUND, CALLBACK
    channel VARCHAR(30), -- VOICE, WEB_CALL, API_TRIGGERED
    agent_type VARCHAR(30), -- AI, HUMAN, HYBRID
    agent_id VARCHAR(50),

    -- Outcome Classification
    outcome VARCHAR(50) NOT NULL,
    -- ACCEPTED, DECLINED, NEGOTIATION_FAILED, NO_EQUIPMENT,
    -- CALLBACK_REQUESTED, NOT_ELIGIBLE, WRONG_LANE, INFORMATION_ONLY
    outcome_confidence NUMERIC(3, 2), -- 0.00 to 1.00

    -- Sentiment Analysis
    sentiment VARCHAR(20),
    -- POSITIVE, NEUTRAL, NEGATIVE
    sentiment_score NUMERIC(3, 2), -- -1.00 to 1.00
    sentiment_breakdown JSONB, -- {frustration: 0.2, satisfaction: 0.8}

    -- Financial
    initial_offer NUMERIC(10, 2),
    final_rate NUMERIC(10, 2),
    rate_accepted BOOLEAN,

    -- Extracted Data
    extracted_data JSONB,
    /* Structure:
    {
        carrier_info: {
            name, equipment_count, equipment_types,
            current_location, team_drivers
        },
        requirements: {
            quick_pay, fuel_advance, special_requests
        },
        availability: {
            date, location, hours_available
        },
        competitive_data: {
            dat_rate, other_quotes
        }
    }
    */

    -- Conversation
    transcript TEXT,
    transcript_summary TEXT,
    key_points TEXT[],

    -- Handoff Information
    transferred_to_human BOOLEAN DEFAULT FALSE,
    transfer_reason VARCHAR(100),
    transferred_at TIMESTAMPTZ,
    assigned_rep_id VARCHAR(50),

    -- Follow-up
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_reason TEXT,
    follow_up_deadline TIMESTAMPTZ,
    follow_up_completed BOOLEAN DEFAULT FALSE,

    -- Recording
    recording_url TEXT,
    recording_duration_seconds INTEGER,

    -- Quality
    quality_score INTEGER, -- 0-100
    quality_issues TEXT[],

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_calls_external_id ON calls(external_call_id);
CREATE INDEX idx_calls_mc_number ON calls(mc_number);
CREATE INDEX idx_calls_carrier ON calls(carrier_id);
CREATE INDEX idx_calls_load ON calls(load_id);
CREATE INDEX idx_calls_phone ON calls(caller_phone);
CREATE INDEX idx_calls_time ON calls(start_time, end_time);
CREATE INDEX idx_calls_outcome ON calls(outcome);
CREATE INDEX idx_calls_sentiment ON calls(sentiment);
CREATE INDEX idx_calls_transferred ON calls(transferred_to_human) WHERE transferred_to_human = TRUE;
CREATE INDEX idx_calls_followup ON calls(follow_up_required, follow_up_deadline)
    WHERE follow_up_required = TRUE AND follow_up_completed = FALSE;

-- Triggers
CREATE TRIGGER update_calls_updated_at
    BEFORE UPDATE ON calls
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 4. negotiations
Tracks negotiation history and state.

```sql
CREATE TABLE negotiations (
    -- Primary Key
    negotiation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Association
    call_id UUID REFERENCES calls(call_id),
    load_id UUID NOT NULL REFERENCES loads(load_id),
    carrier_id UUID REFERENCES carriers(carrier_id),
    mc_number VARCHAR(20),

    -- Session Management
    session_id VARCHAR(100) NOT NULL,
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,

    -- Negotiation Rounds
    round_number INTEGER NOT NULL,
    max_rounds INTEGER DEFAULT 3,

    -- Offer Details
    carrier_offer NUMERIC(10, 2) NOT NULL,
    system_response VARCHAR(50) NOT NULL,
    -- ACCEPTED, COUNTER_OFFER, REJECTED
    counter_offer NUMERIC(10, 2),

    -- Context
    loadboard_rate NUMERIC(10, 2) NOT NULL,
    minimum_acceptable NUMERIC(10, 2),
    maximum_acceptable NUMERIC(10, 2),

    -- Calculations
    offer_difference NUMERIC(10, 2) GENERATED ALWAYS AS (
        carrier_offer - loadboard_rate
    ) STORED,
    percentage_over NUMERIC(5, 2) GENERATED ALWAYS AS (
        CASE WHEN loadboard_rate > 0
        THEN ((carrier_offer - loadboard_rate) / loadboard_rate) * 100
        ELSE 0 END
    ) STORED,

    -- Decision Logic
    decision_factors JSONB,
    /* Structure:
    {
        urgency_level, carrier_history, market_conditions,
        competitor_rates, special_requirements
    }
    */

    -- Communication
    message_to_carrier TEXT,
    justification TEXT,

    -- Result
    final_status VARCHAR(30),
    -- DEAL_ACCEPTED, DEAL_REJECTED, ABANDONED, TIMEOUT
    agreed_rate NUMERIC(10, 2),

    -- Timing
    response_time_seconds INTEGER,
    total_duration_seconds INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_negotiations_session ON negotiations(session_id);
CREATE INDEX idx_negotiations_call ON negotiations(call_id);
CREATE INDEX idx_negotiations_load ON negotiations(load_id);
CREATE INDEX idx_negotiations_carrier ON negotiations(carrier_id);
CREATE INDEX idx_negotiations_active ON negotiations(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_negotiations_status ON negotiations(final_status);
CREATE INDEX idx_negotiations_round ON negotiations(round_number);

-- Triggers
CREATE TRIGGER update_negotiations_updated_at
    BEFORE UPDATE ON negotiations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 5. api_keys
Manages API authentication.

```sql
CREATE TABLE api_keys (
    -- Primary Key
    api_key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Key Information
    key_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed API key
    key_prefix VARCHAR(10) NOT NULL, -- First 8 chars for identification

    -- Identity
    name VARCHAR(100) NOT NULL,
    description TEXT,
    client_type VARCHAR(50), -- HAPPYROBOT, INTERNAL, PARTNER

    -- Permissions
    scopes TEXT[], -- Array of allowed scopes
    ip_whitelist INET[], -- Allowed IP addresses

    -- Rate Limiting
    rate_limit_per_minute INTEGER DEFAULT 100,
    rate_limit_per_day INTEGER DEFAULT 10000,

    -- Usage Tracking
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,
    total_requests BIGINT DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoked_reason TEXT,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    version INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_active ON api_keys(is_active, expires_at)
    WHERE is_active = TRUE;

-- Triggers
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Supporting Tables

### 6. equipment_types
Reference table for equipment types.

```sql
CREATE TABLE equipment_types (
    equipment_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(30), -- VAN, FLATBED, SPECIALIZED, POWER_ONLY
    typical_capacity INTEGER, -- in pounds
    dimensions VARCHAR(50),
    requires_cdl BOOLEAN DEFAULT TRUE,
    special_endorsements TEXT[],
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert reference data
INSERT INTO equipment_types (name, category, typical_capacity, dimensions) VALUES
('53-foot van', 'VAN', 45000, '53ft x 8.5ft x 9ft'),
('48-foot van', 'VAN', 43000, '48ft x 8.5ft x 9ft'),
('Reefer', 'VAN', 43000, '53ft x 8.5ft x 9ft'),
('Flatbed', 'FLATBED', 48000, '48ft x 8.5ft'),
('Step Deck', 'FLATBED', 48000, '48ft x 8.5ft'),
('Double Drop', 'FLATBED', 45000, '29ft well'),
('RGN', 'SPECIALIZED', 70000, 'Variable'),
('Power Only', 'POWER_ONLY', NULL, NULL),
('Hotshot', 'SPECIALIZED', 20000, '40ft'),
('Box Truck', 'VAN', 12000, '26ft x 8ft x 8ft');
```

### 7. rate_history
Tracks historical rate data for analytics.

```sql
CREATE TABLE rate_history (
    rate_history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    load_id UUID REFERENCES loads(load_id),
    lane_key VARCHAR(100), -- e.g., "TX-CA"
    origin_state CHAR(2),
    destination_state CHAR(2),
    miles INTEGER,
    equipment_type VARCHAR(50),
    quoted_rate NUMERIC(10, 2),
    accepted_rate NUMERIC(10, 2),
    rate_per_mile NUMERIC(8, 4),
    carrier_id UUID REFERENCES carriers(carrier_id),
    quote_date DATE NOT NULL,
    market_conditions JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rate_history_lane ON rate_history(lane_key);
CREATE INDEX idx_rate_history_date ON rate_history(quote_date);
CREATE INDEX idx_rate_history_equipment ON rate_history(equipment_type);
```

### 8. audit_log
Comprehensive audit trail.

```sql
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(50) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    changed_fields JSONB,
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(100),
    api_key_id UUID REFERENCES api_keys(api_key_id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
CREATE INDEX idx_audit_user ON audit_log(user_id);
```

---

## Views

### 1. v_active_loads
View of available loads with calculated fields.

```sql
CREATE VIEW v_active_loads AS
SELECT
    l.*,
    EXTRACT(HOURS FROM (l.pickup_date + l.pickup_time_start - NOW())) AS hours_until_pickup,
    CASE
        WHEN l.pickup_date <= CURRENT_DATE + INTERVAL '1 day' THEN 'URGENT'
        WHEN l.pickup_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'SOON'
        ELSE 'NORMAL'
    END AS time_sensitivity,
    COALESCE(nc.negotiation_count, 0) AS times_negotiated,
    COALESCE(nc.last_offer, l.loadboard_rate) AS last_offered_rate
FROM loads l
LEFT JOIN (
    SELECT
        load_id,
        COUNT(*) AS negotiation_count,
        MAX(carrier_offer) AS last_offer
    FROM negotiations
    GROUP BY load_id
) nc ON l.load_id = nc.load_id
WHERE l.status = 'AVAILABLE'
    AND l.is_active = TRUE
    AND l.deleted_at IS NULL
    AND (l.expires_at IS NULL OR l.expires_at > NOW());
```

### 2. v_carrier_performance
Carrier metrics and performance view.

```sql
CREATE VIEW v_carrier_performance AS
SELECT
    c.carrier_id,
    c.mc_number,
    c.legal_name,
    COUNT(DISTINCT ca.call_id) AS total_calls,
    COUNT(DISTINCT l.load_id) FILTER (WHERE l.status = 'BOOKED') AS loads_booked,
    AVG(n.round_number) AS avg_negotiation_rounds,
    AVG(ca.sentiment_score) AS avg_sentiment_score,
    COUNT(DISTINCT ca.call_id) FILTER (WHERE ca.outcome = 'ACCEPTED') AS accepted_count,
    COUNT(DISTINCT ca.call_id) FILTER (WHERE ca.outcome = 'DECLINED') AS declined_count,
    MAX(ca.start_time) AS last_contact_date,
    ARRAY_AGG(DISTINCT l.equipment_type) AS equipment_types_used
FROM carriers c
LEFT JOIN calls ca ON c.carrier_id = ca.carrier_id
LEFT JOIN loads l ON ca.load_id = l.load_id
LEFT JOIN negotiations n ON ca.call_id = n.call_id
GROUP BY c.carrier_id, c.mc_number, c.legal_name;
```

### 3. v_daily_metrics
Daily aggregated metrics for dashboard.

```sql
CREATE VIEW v_daily_metrics AS
SELECT
    DATE(ca.start_time) AS date,
    COUNT(DISTINCT ca.call_id) AS total_calls,
    COUNT(DISTINCT ca.carrier_id) AS unique_carriers,
    COUNT(DISTINCT ca.call_id) FILTER (WHERE ca.outcome = 'ACCEPTED') AS deals_closed,
    AVG(ca.duration_seconds) AS avg_call_duration,
    AVG(CASE WHEN ca.sentiment = 'POSITIVE' THEN 1
             WHEN ca.sentiment = 'NEUTRAL' THEN 0
             ELSE -1 END) AS avg_sentiment,
    SUM(l.agreed_rate) FILTER (WHERE ca.outcome = 'ACCEPTED') AS total_revenue,
    AVG(n.round_number) AS avg_negotiation_rounds,
    COUNT(DISTINCT ca.call_id) FILTER (WHERE ca.transferred_to_human = TRUE) AS human_handoffs
FROM calls ca
LEFT JOIN (
    SELECT call_id, load_id, MAX(agreed_rate) AS agreed_rate
    FROM negotiations
    WHERE final_status = 'DEAL_ACCEPTED'
    GROUP BY call_id, load_id
) l ON ca.call_id = l.call_id
LEFT JOIN negotiations n ON ca.call_id = n.call_id
WHERE ca.start_time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(ca.start_time)
ORDER BY date DESC;
```

---

## Functions and Triggers

### 1. Update Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 2. Audit Log Trigger
```sql
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_row audit_log;
    changed_fields JSONB = '{}';
    old_data JSONB;
    new_data JSONB;
BEGIN
    audit_row.table_name = TG_TABLE_NAME;
    audit_row.action = TG_OP;
    audit_row.user_id = current_setting('app.current_user_id', TRUE);
    audit_row.api_key_id = current_setting('app.current_api_key_id', TRUE)::UUID;

    IF TG_OP = 'DELETE' THEN
        audit_row.record_id = OLD.id;
        old_data = to_jsonb(OLD);
        INSERT INTO audit_log(table_name, record_id, action, old_values, user_id, api_key_id)
        VALUES (audit_row.table_name, audit_row.record_id, audit_row.action, old_data,
                audit_row.user_id, audit_row.api_key_id);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        audit_row.record_id = NEW.id;
        old_data = to_jsonb(OLD);
        new_data = to_jsonb(NEW);

        SELECT jsonb_object_agg(key, new_data->key)
        INTO changed_fields
        FROM jsonb_each(new_data)
        WHERE old_data->key IS DISTINCT FROM new_data->key;

        INSERT INTO audit_log(table_name, record_id, action, changed_fields,
                             old_values, new_values, user_id, api_key_id)
        VALUES (audit_row.table_name, audit_row.record_id, audit_row.action,
                changed_fields, old_data, new_data, audit_row.user_id, audit_row.api_key_id);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        audit_row.record_id = NEW.id;
        new_data = to_jsonb(NEW);
        INSERT INTO audit_log(table_name, record_id, action, new_values, user_id, api_key_id)
        VALUES (audit_row.table_name, audit_row.record_id, audit_row.action,
                new_data, audit_row.user_id, audit_row.api_key_id);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

### 3. Calculate Negotiation Threshold
```sql
CREATE OR REPLACE FUNCTION calculate_negotiation_threshold(
    p_loadboard_rate NUMERIC,
    p_urgency VARCHAR,
    p_carrier_history JSONB
) RETURNS JSONB AS $$
DECLARE
    v_min_rate NUMERIC;
    v_max_rate NUMERIC;
    v_auto_accept NUMERIC;
    v_urgency_factor NUMERIC := 1.0;
    v_history_factor NUMERIC := 1.0;
BEGIN
    -- Adjust for urgency
    CASE p_urgency
        WHEN 'CRITICAL' THEN v_urgency_factor := 1.15;
        WHEN 'HIGH' THEN v_urgency_factor := 1.10;
        WHEN 'NORMAL' THEN v_urgency_factor := 1.05;
        ELSE v_urgency_factor := 1.0;
    END CASE;

    -- Adjust for carrier history
    IF p_carrier_history IS NOT NULL THEN
        IF (p_carrier_history->>'total_loads')::INTEGER > 10 THEN
            v_history_factor := 1.05;
        END IF;
        IF (p_carrier_history->>'avg_rating')::NUMERIC > 4.5 THEN
            v_history_factor := v_history_factor + 0.02;
        END IF;
    END IF;

    -- Calculate thresholds
    v_min_rate := p_loadboard_rate * 0.95; -- 5% below
    v_max_rate := p_loadboard_rate * v_urgency_factor * v_history_factor;
    v_auto_accept := p_loadboard_rate * 1.02; -- 2% above

    RETURN jsonb_build_object(
        'minimum_rate', ROUND(v_min_rate, 2),
        'maximum_rate', ROUND(v_max_rate, 2),
        'auto_accept_threshold', ROUND(v_auto_accept, 2),
        'loadboard_rate', p_loadboard_rate,
        'factors_applied', jsonb_build_object(
            'urgency_factor', v_urgency_factor,
            'history_factor', v_history_factor
        )
    );
END;
$$ LANGUAGE plpgsql;
```

---

## Indexes Strategy

### Performance Indexes
1. **Primary lookups**: MC number, load ID, call ID
2. **Time-based queries**: Created/updated timestamps
3. **Status filtering**: Active records, available loads
4. **Geographic queries**: Origin/destination states
5. **Rate searches**: Rate ranges, rate per mile

### Composite Indexes
```sql
-- Frequently used load search
CREATE INDEX idx_loads_search ON loads(
    equipment_type,
    origin_state,
    pickup_date,
    status
) WHERE status = 'AVAILABLE' AND is_active = TRUE;

-- Call analytics
CREATE INDEX idx_calls_analytics ON calls(
    start_time,
    outcome,
    sentiment
);

-- Carrier lookup with eligibility
CREATE INDEX idx_carriers_lookup ON carriers(
    mc_number,
    is_eligible
) WHERE is_eligible = TRUE;
```

---

## Sample Data

### Test Carriers
```sql
INSERT INTO carriers (mc_number, dot_number, legal_name, dba_name, entity_type,
                      operating_status, status, insurance_on_file) VALUES
('123456', '789012', 'ACME TRUCKING LLC', 'ACME EXPRESS', 'CARRIER',
 'AUTHORIZED_FOR_HIRE', 'ACTIVE', TRUE),
('234567', '890123', 'BEST LOGISTICS INC', NULL, 'CARRIER',
 'AUTHORIZED_FOR_HIRE', 'ACTIVE', TRUE),
('345678', '901234', 'CARGO MASTERS LLC', 'CARGO PROS', 'CARRIER',
 'NOT_AUTHORIZED', 'ACTIVE', FALSE),
('456789', '012345', 'DELTA FREIGHT CORP', NULL, 'CARRIER',
 'AUTHORIZED_FOR_HIRE', 'ACTIVE', TRUE),
('567890', '123456', 'EXPRESS CARRIERS INC', 'EXPRESS LINE', 'CARRIER',
 'AUTHORIZED_FOR_HIRE', 'ACTIVE', TRUE);
```

### Test Loads
```sql
INSERT INTO loads (
    reference_number, origin_city, origin_state, destination_city, destination_state,
    pickup_date, delivery_date, equipment_type, weight, miles, loadboard_rate,
    commodity_type, urgency, status
) VALUES
('REF-001', 'Dallas', 'TX', 'Los Angeles', 'CA',
 CURRENT_DATE + 1, CURRENT_DATE + 4, '53-foot van', 42000, 1400, 2800.00,
 'General Merchandise', 'HIGH', 'AVAILABLE'),

('REF-002', 'Chicago', 'IL', 'Atlanta', 'GA',
 CURRENT_DATE + 2, CURRENT_DATE + 3, 'Reefer', 38000, 720, 2200.00,
 'Produce', 'NORMAL', 'AVAILABLE'),

('REF-003', 'Phoenix', 'AZ', 'Denver', 'CO',
 CURRENT_DATE + 1, CURRENT_DATE + 2, 'Flatbed', 45000, 850, 2550.00,
 'Steel Coils', 'CRITICAL', 'AVAILABLE'),

('REF-004', 'Seattle', 'WA', 'San Francisco', 'CA',
 CURRENT_DATE + 3, CURRENT_DATE + 4, '48-foot van', 35000, 810, 2100.00,
 'Electronics', 'NORMAL', 'AVAILABLE'),

('REF-005', 'Miami', 'FL', 'New York', 'NY',
 CURRENT_DATE + 2, CURRENT_DATE + 5, 'Reefer', 40000, 1280, 3200.00,
 'Pharmaceuticals', 'HIGH', 'AVAILABLE');
```

---

## Migration Scripts

### Initial Schema Creation (Alembic)
```python
"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2024-08-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create tables in dependency order
    # 1. Create carriers table
    op.create_table('carriers',
        sa.Column('carrier_id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('mc_number', sa.String(20), nullable=False),
        # ... rest of columns
        sa.PrimaryKeyConstraint('carrier_id'),
        sa.UniqueConstraint('mc_number')
    )

    # 2. Create loads table
    op.create_table('loads',
        sa.Column('load_id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        # ... rest of columns
        sa.PrimaryKeyConstraint('load_id')
    )

    # ... create remaining tables

    # Create indexes
    op.create_index('idx_carriers_mc_number', 'carriers', ['mc_number'])
    op.create_index('idx_loads_status', 'loads', ['status'])
    # ... create remaining indexes

def downgrade():
    # Drop tables in reverse dependency order
    op.drop_table('audit_log')
    op.drop_table('negotiations')
    op.drop_table('calls')
    op.drop_table('loads')
    op.drop_table('carriers')
    # ... drop remaining tables
```

---

## Maintenance and Optimization

### 1. Vacuum Strategy
```sql
-- Weekly vacuum analyze for active tables
VACUUM ANALYZE loads, calls, negotiations;

-- Monthly full vacuum for all tables
VACUUM FULL carriers, loads, calls, negotiations;
```

### 2. Statistics Update
```sql
-- Update statistics after bulk operations
ANALYZE carriers, loads, calls, negotiations;
```

### 3. Partitioning (Future)
For high-volume tables, implement date-based partitioning:
```sql
-- Example: Partition calls table by month
CREATE TABLE calls_2024_08 PARTITION OF calls
FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');
```

### 4. Archival Strategy
```sql
-- Archive old calls after 90 days
INSERT INTO calls_archive
SELECT * FROM calls
WHERE start_time < CURRENT_DATE - INTERVAL '90 days';

DELETE FROM calls
WHERE start_time < CURRENT_DATE - INTERVAL '90 days';
```

---

## Security Considerations

1. **Row-Level Security**: Implement RLS for multi-tenant scenarios
2. **Column Encryption**: Sensitive data encrypted at rest
3. **Audit Logging**: All data modifications tracked
4. **API Key Rotation**: Regular key rotation policy
5. **Connection Encryption**: SSL/TLS for all connections
6. **Backup Encryption**: Encrypted backups with KMS keys

---

## Performance Benchmarks

### Expected Query Performance
| Query Type | Target Response Time |
|------------|---------------------|
| Load search by equipment | < 100ms |
| Carrier lookup | < 50ms |
| Negotiation state check | < 50ms |
| Dashboard metrics aggregation | < 500ms |
| Call history retrieval | < 200ms |

### Capacity Planning
- **Connections**: 200 max (20 pool + 10 overflow per service)
- **Storage**: ~1GB per 10,000 loads + calls
- **IOPS**: 3000 baseline, 10000 burst
- **CPU**: 4 vCPU minimum for production
- **Memory**: 16GB minimum for production
