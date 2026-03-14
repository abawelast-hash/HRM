-- ShamIn Database Initialization
-- Creates required tables for the application

-- Raw texts table (for collected news and content)
CREATE TABLE IF NOT EXISTS raw_texts (
  id SERIAL PRIMARY KEY,
  source_type VARCHAR(50) NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  url TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_texts_source_type ON raw_texts(source_type);
CREATE INDEX IF NOT EXISTS idx_raw_texts_created_at ON raw_texts(created_at DESC);

-- Data sources table
CREATE TABLE IF NOT EXISTS data_sources (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  type VARCHAR(50) NOT NULL,
  url TEXT,
  is_active BOOLEAN DEFAULT true,
  config JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default data sources
INSERT INTO data_sources (name, type, url, is_active) VALUES
  ('Syria Economy', 'rss', 'https://www.syria.tv/rss', true),
  ('Al Watan', 'rss', 'https://alwatan.sy/rss', true),
  ('SP Today', 'web', 'https://sp-today.com', true),
  ('Telegram SYP', 'telegram', NULL, true),
  ('Syria Steps', 'rss', 'https://www.syriasteps.com/rss', true),
  ('Lira Today', 'web', 'https://lfraa.com/', true),
  ('Cashy', 'web', 'https://cashy.me/', true),
  ('Gold Price', 'api', 'https://api.gold.org/', true)
ON CONFLICT (name) DO NOTHING;

-- Success message
SELECT 'Tables created successfully!' as status;
