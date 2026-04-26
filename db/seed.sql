-- =============================================================
-- Seed data — Asistente de Compromiso de Stock
-- Fuente: mock_articulos.csv, mock_stocks.csv, mock_ordenes_compra.csv
-- =============================================================

INSERT INTO articles (sku, description, is_obsolete) VALUES
    ('ZAP-001', 'Zapato Profesional de Seguridad',     FALSE),
    ('ZAP-002', 'Bota de Agua Industrial',             FALSE),
    ('ZAP-003', 'Zapato Elegante Caballero',           FALSE),
    ('ACC-452', 'Accesorio de Protección Lumbar',      TRUE),
    ('ACC-101', 'Guantes de Nitrilo (Caja 100)',       FALSE),
    ('ACC-202', 'Gafas de Protección UV',              FALSE),
    ('ZAP-999', 'Modelo Antiguo de Prueba',            TRUE),
    ('HER-001', 'Martillo Percutor Pro',               FALSE),
    ('HER-002', 'Taladro Inalámbrico 18V',             FALSE),
    ('HER-003', 'Destornillador Eléctrico',            TRUE),
    ('ROPA-01', 'Chaqueta Reflectante Alta Visibilidad', FALSE),
    ('ROPA-02', 'Pantalón de Trabajo Reforzado',       FALSE),
    ('LIM-01',  'Kit de Limpieza Industrial',          FALSE),
    ('LIM-02',  'Detergente Bio-Degradable',           TRUE),
    ('OFF-01',  'Silla Ergonómica Oficina',            FALSE);

INSERT INTO stocks (sku, warehouse, available_quantity, location) VALUES
    ('ZAP-001', 'ALM-CENTRAL',   120, 'A-12-04'),
    ('ZAP-001', 'ALM-NORTE',      45, 'B-01-02'),
    ('ZAP-001', 'ALM-SUR',        10, 'S-05-01'),
    ('ZAP-001', 'ALM-RESERVADO', 300, 'R-01-01'),
    ('ZAP-002', 'ALM-SUR',       300, 'D-10-10'),
    ('ZAP-002', 'ALM-CENTRAL',    50, 'A-05-02'),
    ('ZAP-003', 'ALM-CENTRAL',    15, 'A-08-01'),
    ('ACC-452', 'ALM-CENTRAL',    10, 'C-05-01'),
    ('ACC-452', 'ALM-NORTE',       5, 'B-02-09'),
    ('ACC-101', 'ALM-SUR',       500, 'S-11-01'),
    ('ACC-101', 'ALM-CENTRAL',   200, 'A-20-03'),
    ('ACC-202', 'ALM-CENTRAL',    80, 'A-20-04'),
    ('ACC-202', 'ALM-NORTE',      15, 'B-02-10'),
    ('ZAP-999', 'ALM-NORTE',       2, 'B-99-99'),
    ('HER-001', 'ALM-CENTRAL',    30, 'H-01-01'),
    ('HER-001', 'ALM-SUR',         8, 'S-05-05'),
    ('HER-002', 'ALM-CENTRAL',    12, 'H-01-02'),
    ('HER-003', 'ALM-NORTE',      25, 'B-05-05'),
    ('ROPA-01', 'ALM-SUR',       150, 'S-01-01'),
    ('ROPA-01', 'ALM-CENTRAL',    40, 'A-30-01'),
    ('ROPA-02', 'ALM-SUR',       200, 'S-01-02'),
    ('LIM-01',  'ALM-CENTRAL',    60, 'L-01-01'),
    ('LIM-02',  'ALM-CENTRAL',   100, 'L-01-02'),
    ('OFF-01',  'ALM-SUR',         5, 'S-90-01'),
    ('OFF-01',  'ALM-CENTRAL',     2, 'A-90-01');

INSERT INTO purchase_orders (sku, pending_quantity, estimated_date, supplier, order_status) VALUES
    ('ZAP-001', 400, '2026-04-15', 'GLOBAL-SUPPLY',   'CONFIRMADO'),
    ('ZAP-001', 100, '2026-04-20', 'FACTOR-X',        'PENDIENTE'),
    ('ZAP-001', 200, '2026-05-20', 'GLOBAL-SUPPLY',   'SOLICITADO'),
    ('ZAP-002', 200, '2026-04-10', 'GLOBAL-SUPPLY',   'TRANSITO'),
    ('ZAP-003',  50, '2026-05-01', 'LUX-FOOT',        'SOLICITADO'),
    ('ACC-101',1000, '2026-04-05', 'PROTECT-ALL',     'CONFIRMADO'),
    ('ACC-202', 300, '2026-04-12', 'PROTECT-ALL',     'PENDIENTE'),
    ('HER-001',  20, '2026-04-18', 'TOOLS-INC',       'CONFIRMADO'),
    ('HER-002',  80, '2026-04-25', 'TOOLS-INC',       'SOLICITADO'),
    ('HER-003', 150, '2026-04-30', 'TOOLS-INC',       'TRANSITO'),
    ('ROPA-01', 100, '2026-04-08', 'TEXTIL-PRO',      'CONFIRMADO'),
    ('ROPA-02',  50, '2026-04-15', 'TEXTIL-PRO',      'PENDIENTE'),
    ('LIM-01',  200, '2026-04-22', 'CHEM-SOLUTIONS',  'CONFIRMADO'),
    ('LIM-02',   50, '2026-05-10', 'CHEM-SOLUTIONS',  'SOLICITADO'),
    ('OFF-01',   10, '2026-05-15', 'OFFICE-DESIGN',   'CONFIRMADO');
