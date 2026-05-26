-- =============================================================================
-- Seed Data for Mini Data Warehouse
-- =============================================================================

-- Dimensions
INSERT INTO dim_product VALUES (1, 'P001', 'Widget A',   'Widgets',     9.99);
INSERT INTO dim_product VALUES (2, 'P002', 'Widget B',   'Widgets',    14.99);
INSERT INTO dim_product VALUES (3, 'P003', 'Gadget X',   'Gadgets',    29.99);
INSERT INTO dim_product VALUES (4, 'P004', 'Gadget Y',   'Gadgets',    49.99);
INSERT INTO dim_product VALUES (5, 'P005', 'Doohickey',  'Accessories', 4.99);

INSERT INTO dim_customer VALUES (1, 'C0001', 'Alice Johnson', 'Premium');
INSERT INTO dim_customer VALUES (2, 'C0002', 'Bob Smith',     'Standard');
INSERT INTO dim_customer VALUES (3, 'C0003', 'Carol Williams', 'Premium');

INSERT INTO dim_date VALUES (20250101, '2025-01-01', 1, 1, 2025);
INSERT INTO dim_date VALUES (20250115, '2025-01-15', 1, 1, 2025);
INSERT INTO dim_date VALUES (20250201, '2025-02-01', 2, 1, 2025);
INSERT INTO dim_date VALUES (20250315, '2025-03-15', 3, 1, 2025);

-- Facts
INSERT INTO fact_sales VALUES (1, 1, 1, 20250101, 5,  49.95,  53.95);
INSERT INTO fact_sales VALUES (2, 1, 3, 20250101, 2,  59.98,  64.78);
INSERT INTO fact_sales VALUES (3, 2, 2, 20250115, 3,  44.97,  48.57);
INSERT INTO fact_sales VALUES (4, 3, 4, 20250201, 1,  49.99,  53.99);
INSERT INTO fact_sales VALUES (5, 2, 5, 20250315, 10, 49.90,  53.89);
