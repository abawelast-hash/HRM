-- ============================================
-- ShamIn PostgreSQL Database Schema
-- مخطط قاعدة بيانات ShamIn
-- ============================================

-- Drop tables if they exist (for clean install)
-- DROP TABLE IF EXISTS raw_texts CASCADE;
-- DROP TABLE IF EXISTS data_sources CASCADE;

-- ============================================
-- Table: raw_texts
-- وصف: تخزين جميع النصوص الخام المجمعة
-- ============================================

CREATE TABLE IF NOT EXISTS raw_texts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    url VARCHAR(500),
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    hash VARCHAR(32) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_source_not_empty CHECK (source <> ''),
    CONSTRAINT check_text_not_empty CHECK (text <> '')
);

-- Indexes for raw_texts
CREATE INDEX IF NOT EXISTS idx_raw_texts_hash ON raw_texts(hash);
CREATE INDEX IF NOT EXISTS idx_raw_texts_timestamp ON raw_texts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_raw_texts_source ON raw_texts(source);
CREATE INDEX IF NOT EXISTS idx_raw_texts_created_at ON raw_texts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_texts_metadata ON raw_texts USING GIN(metadata);

-- Comments
COMMENT ON TABLE raw_texts IS 'جميع النصوص الخام المجمعة من المصادر المختلفة';
COMMENT ON COLUMN raw_texts.id IS 'المعرف الفريد';
COMMENT ON COLUMN raw_texts.source IS 'اسم المصدر (مثل: enab_baladi_rss)';
COMMENT ON COLUMN raw_texts.text IS 'النص الكامل';
COMMENT ON COLUMN raw_texts.url IS 'رابط المصدر (إن وجد)';
COMMENT ON COLUMN raw_texts.timestamp IS 'وقت النشر الأصلي';
COMMENT ON COLUMN raw_texts.metadata IS 'بيانات إضافية (JSON)';
COMMENT ON COLUMN raw_texts.hash IS 'MD5 hash للنص (منع التكرار)';
COMMENT ON COLUMN raw_texts.created_at IS 'وقت الإضافة لقاعدة البيانات';

-- ============================================
-- Table: data_sources
-- وصف: إدارة مصادر البيانات
-- ============================================

CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT check_type_valid CHECK (type IN ('rss', 'telegram', 'web', 'api')),
    CONSTRAINT check_name_not_empty CHECK (name <> '')
);

-- Indexes for data_sources
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(type);
CREATE INDEX IF NOT EXISTS idx_data_sources_enabled ON data_sources(enabled);
CREATE INDEX IF NOT EXISTS idx_data_sources_config ON data_sources USING GIN(config);

-- Comments
COMMENT ON TABLE data_sources IS 'تكوين وإدارة مصادر البيانات';
COMMENT ON COLUMN data_sources.id IS 'المعرف الفريد';
COMMENT ON COLUMN data_sources.type IS 'نوع المصدر (rss, telegram, web, api)';
COMMENT ON COLUMN data_sources.name IS 'اسم المصدر';
COMMENT ON COLUMN data_sources.config IS 'تكوين المصدر (JSON)';
COMMENT ON COLUMN data_sources.enabled IS 'هل المصدر مفعّل؟';
COMMENT ON COLUMN data_sources.created_at IS 'وقت الإنشاء';
COMMENT ON COLUMN data_sources.updated_at IS 'وقت آخر تحديث';

-- ============================================
-- Insert Default Data Sources
-- ============================================

INSERT INTO data_sources (type, name, config, enabled) VALUES
    ('rss', 'عنب بلدي', 
     '{"url": "https://www.enabbaladi.net/feed/", "category": "news"}', 
     true),
    
    ('rss', 'رويترز بالعربية', 
     '{"url": "https://www.reuters.com/rssFeed/arabicWorldNews", "category": "news"}', 
     true),
    
    ('rss', 'وكالة سانا', 
     '{"url": "https://www.sana.sy/?feed=rss2", "category": "news"}', 
     true),
    
    ('rss', 'العربي الجديد', 
     '{"url": "https://www.alaraby.co.uk/rss.xml", "category": "news"}', 
     true),
    
    ('rss', 'الجزيرة', 
     '{"url": "https://www.aljazeera.net/xml/rss/all.xml", "category": "news"}', 
     true),
    
    ('web', 'SP Today', 
     '{"url": "https://sp-today.com/", "strategy": "api", "category": "prices"}', 
     true),
    
    ('web', 'Investing.com', 
     '{"url": "https://www.investing.com/currencies/usd-syp", "strategy": "html", "category": "prices"}', 
     true),
    
    ('web', 'البنك المركزي السوري', 
     '{"url": "https://cbs.gov.sy/", "strategy": "json", "category": "official_rates"}', 
     true)
    
ON CONFLICT DO NOTHING;

-- ============================================
-- Functions and Triggers
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for data_sources
DROP TRIGGER IF EXISTS update_data_sources_updated_at ON data_sources;
CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Useful Queries (for reference)
-- ============================================

-- Count texts by source
-- SELECT source, COUNT(*) as count 
-- FROM raw_texts 
-- GROUP BY source 
-- ORDER BY count DESC;

-- Recent texts (last 24 hours)
-- SELECT * FROM raw_texts 
-- WHERE timestamp > NOW() - INTERVAL '24 hours' 
-- ORDER BY timestamp DESC 
-- LIMIT 100;

-- Enabled data sources
-- SELECT * FROM data_sources 
-- WHERE enabled = true 
-- ORDER BY type, name;

-- Check for duplicate hashes
-- SELECT hash, COUNT(*) 
-- FROM raw_texts 
-- GROUP BY hash 
-- HAVING COUNT(*) > 1;

-- ============================================
-- Grants (if needed for specific users)
-- ============================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO shamin_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO shamin_user;

-- ============================================
-- Database Information
-- ============================================

SELECT 'PostgreSQL schema initialized successfully!' AS status;
SELECT version() AS postgres_version;
SELECT current_database() AS database_name;
SELECT current_user AS current_user;
SELECT NOW() AS current_time;
