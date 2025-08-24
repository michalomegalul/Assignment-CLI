CREATE TABLE domain (
    id SERIAL PRIMARY KEY,
    fqdn VARCHAR(255) NOT NULL,
    registered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    unregistered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT domain_fqdn_not_empty CHECK (LENGTH(TRIM(fqdn)) > 0),
    CONSTRAINT domain_registration_order CHECK (
        unregistered_at IS NULL OR unregistered_at > registered_at
    )
);

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Prevent overlapping domain registrations
ALTER TABLE domain ADD CONSTRAINT no_overlap_for_fqdn
EXCLUDE USING gist (
    fqdn WITH =,
    tstzrange(registered_at, COALESCE(unregistered_at, 'infinity')) WITH &&
);

CREATE TABLE domain_flag (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domain(id) ON DELETE CASCADE,
    flag VARCHAR(32) NOT NULL,
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMP WITH TIME ZONE,

    CONSTRAINT domain_flag_flag_not_empty CHECK (LENGTH(TRIM(flag)) > 0),
    CONSTRAINT domain_flag_validity_order CHECK (
        valid_to IS NULL OR valid_to > valid_from
    ),
    CONSTRAINT domain_flag_valid_types CHECK (
        flag IN ('EXPIRED', 'OUTZONE', 'DELETE_CANDIDATE')
    )

);

-- Indexes for performance
CREATE INDEX idx_domain_fqdn ON domain(fqdn);
CREATE INDEX idx_domain_unregistered ON domain(unregistered_at);
CREATE INDEX idx_flag_domain_id ON domain_flag(domain_id);
CREATE INDEX idx_flag_type ON domain_flag(flag);
CREATE INDEX idx_flag_validity ON domain_flag(valid_from, valid_to);