-- 1. 社保监管数据库（SBDB）
CREATE DATABASE IF NOT EXISTS SBDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 2. 税务监管数据库（TAXDB）
CREATE DATABASE IF NOT EXISTS TAXDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 3. 市场监督管理数据库（MTDB）
CREATE DATABASE IF NOT EXISTS MTDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 4. 民政补贴发放数据库（CABDB）
CREATE DATABASE IF NOT EXISTS CABDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 5. 统计数据申报数据库（STDDB）
CREATE DATABASE IF NOT EXISTS STDDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;





-- ===================================================================
-- 二、社保监管数据库（SBDB）表创建
-- ===================================================================
USE SBDB;

CREATE TABLE IF NOT EXISTS sbdb_person_base (
    id_card CHAR(18) NOT NULL,
    name VARCHAR(50) NOT NULL,
    gender CHAR(2) NOT NULL CHECK (gender IN ('男', '女')),
    birth_date DATE NOT NULL,
    household_address VARCHAR(200),
    insurance_status CHAR(10) NOT NULL CHECK (insurance_status IN ('正常', '停保', '注销')),
    first_insurance_date DATE,
    PRIMARY KEY (id_card),
    INDEX idx_id_card_status (id_card, insurance_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sbdb_employment_reg (
    reg_id INT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    employment_status CHAR(10) NOT NULL CHECK (employment_status IN ('在职', '失业', '灵活就业')),
    company_credit_code CHAR(18) NOT NULL,
    hire_date DATE NOT NULL,
    leave_date DATE,
    reg_agency VARCHAR(100) NOT NULL,
    PRIMARY KEY (reg_id),
    INDEX idx_id_card_status (id_card, employment_status),
    INDEX idx_company_hire_date (company_credit_code, hire_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sbdb_enterprise_insure (
    insure_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    insured_count INT NOT NULL DEFAULT 0,
    insure_start_date DATE NOT NULL,
    insure_type CHAR(10) NOT NULL CHECK (insure_type IN ('五险', '单险', '灵活就业参保')),
    social_security_dept VARCHAR(100) NOT NULL,
    PRIMARY KEY (insure_id),
    UNIQUE INDEX uk_company_credit_code (company_credit_code),
    INDEX idx_insured_count_start_date (insured_count, insure_start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sbdb_payment_detail (
    payment_id BIGINT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    payment_period CHAR(6) NOT NULL,
    contribution_base DECIMAL(10,2) NOT NULL,
    personal_payment DECIMAL(10,2) NOT NULL,
    employer_payment DECIMAL(10,2) NOT NULL,
    payment_status CHAR(10) NOT NULL CHECK (payment_status IN ('已缴', '欠缴', '补缴')),
    PRIMARY KEY (payment_id),
    INDEX idx_id_card_period (id_card, payment_period),
    INDEX idx_company_status (company_credit_code, payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sbdb_benefit_apply (
    apply_id INT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    benefit_type CHAR(15) NOT NULL CHECK (benefit_type IN ('养老金', '失业金', '医保报销', '工伤补贴', '生育津贴')),
    apply_date DATE NOT NULL,
    benefit_amount DECIMAL(10,2) NOT NULL,
    disbursement_status CHAR(10) NOT NULL CHECK (disbursement_status IN ('待发放', '发放中', '已停发')),
    bank_account VARCHAR(30) NOT NULL,
    PRIMARY KEY (apply_id),
    INDEX idx_id_card_type (id_card, benefit_type),
    INDEX idx_status_date (disbursement_status, apply_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sbdb_violation_rec (
    violation_id INT AUTO_INCREMENT NOT NULL,
    ref_id CHAR(18) NOT NULL,
    subject_type CHAR(5) NOT NULL CHECK (subject_type IN ('个人', '企业')),
    violation_type CHAR(15) NOT NULL CHECK (violation_type IN ('骗保', '欠缴', '重复申领', '资格造假')),
    violation_amount DECIMAL(12,2) NOT NULL,
    handling_result CHAR(15) NOT NULL CHECK (handling_result IN ('已追回', '待追回', '已处罚', '整改中')),
    handling_date DATE NOT NULL,
    handling_agency VARCHAR(100) NOT NULL,
    PRIMARY KEY (violation_id),
    INDEX idx_ref_violation (ref_id, violation_type),
    INDEX idx_result_date (handling_result, handling_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- 三、税务监管数据库（TAXDB）表创建
-- ===================================================================
USE TAXDB;

CREATE TABLE IF NOT EXISTS taxdb_enterprise_reg (
    reg_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    taxpayer_type CHAR(10) NOT NULL CHECK (taxpayer_type IN ('一般纳税人', '小规模纳税人')),
    tax_reg_address VARCHAR(200) NOT NULL,
    tax_bureau VARCHAR(100) NOT NULL,
    reg_date DATE NOT NULL,
    cancel_date DATE,
    PRIMARY KEY (reg_id),
    UNIQUE INDEX uk_company_credit_code (company_credit_code),
    INDEX idx_taxpayer_address (taxpayer_type, tax_reg_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS taxdb_enterprise_vat (
    vat_id BIGINT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    reporting_period CHAR(6) NOT NULL,
    revenue DECIMAL(15,2) NOT NULL,
    output_tax DECIMAL(12,2) NOT NULL,
    input_tax DECIMAL(12,2) NOT NULL,
    payable_tax DECIMAL(12,2) NOT NULL,
    filing_status CHAR(10) NOT NULL CHECK (filing_status IN ('已申报', '未申报', '逾期申报')),
    filing_date DATE NOT NULL,
    PRIMARY KEY (vat_id),
    INDEX idx_company_period (company_credit_code, reporting_period),
    INDEX idx_status_revenue (filing_status, revenue)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS taxdb_person_income (
    income_id BIGINT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    reporting_period CHAR(6) NOT NULL,
    pre_tax_income DECIMAL(10,2) NOT NULL,
    special_deductions DECIMAL(8,2) NOT NULL DEFAULT 0,
    taxable_income DECIMAL(10,2) NOT NULL,
    tax_paid DECIMAL(10,2) NOT NULL,
    employer_credit_code CHAR(18) NOT NULL,
    filing_status CHAR(10) NOT NULL CHECK (filing_status IN ('已申报', '未申报', '补申报')),
    PRIMARY KEY (income_id),
    INDEX idx_id_card_period (id_card, reporting_period),
    INDEX idx_employer_income (employer_credit_code, pre_tax_income)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS taxdb_invoice_detail (
    invoice_id BIGINT AUTO_INCREMENT NOT NULL,
    invoice_no VARCHAR(20) NOT NULL,
    seller_credit_code CHAR(18) NOT NULL,
    buyer_id VARCHAR(20) NOT NULL,
    issue_date DATE NOT NULL,
    invoice_amount DECIMAL(15,2) NOT NULL,
    invoice_type CHAR(10) NOT NULL CHECK (invoice_type IN ('增值税专票', '增值税普票', '电子发票')),
    goods_service_name VARCHAR(100) NOT NULL,
    invoice_status CHAR(10) NOT NULL CHECK (invoice_status IN ('正常', '作废', '红冲')),
    PRIMARY KEY (invoice_id),
    UNIQUE INDEX uk_invoice_no (invoice_no),
    INDEX idx_seller_date (seller_credit_code, issue_date),
    INDEX idx_status_amount (invoice_status, invoice_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS taxdb_enterprise_income (
    income_report_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    report_year INT NOT NULL,
    total_profit DECIMAL(15,2) NOT NULL,
    taxable_profit DECIMAL(15,2) NOT NULL,
    income_tax DECIMAL(12,2) NOT NULL,
    total_assets DECIMAL(18,2) NOT NULL,
    employee_count INT NOT NULL,
    filing_date DATE NOT NULL,
    PRIMARY KEY (income_report_id),
    INDEX idx_company_year (company_credit_code, report_year),
    INDEX idx_employee_profit (employee_count, total_profit)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS taxdb_punishment_rec (
    punishment_id INT AUTO_INCREMENT NOT NULL,
    ref_id CHAR(18) NOT NULL,
    subject_type CHAR(5) NOT NULL CHECK (subject_type IN ('个人', '企业')),
    violation_type CHAR(15) NOT NULL CHECK (violation_type IN ('偷税', '虚开发票', '欠缴税款', '申报造假')),
    penalty_amount DECIMAL(12,2) NOT NULL,
    penalty_date DATE NOT NULL,
    rectification_status CHAR(10) NOT NULL CHECK (rectification_status IN ('已整改', '待整改', '未整改')),
    penalty_doc_no VARCHAR(50) NOT NULL,
    PRIMARY KEY (punishment_id),
    INDEX idx_ref_violation (ref_id, violation_type),
    INDEX idx_date_status (penalty_date, rectification_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- 四、市场监督管理数据库（MTDB）表创建
-- ===================================================================
USE MTDB;

CREATE TABLE IF NOT EXISTS mtdb_enterprise_reg (
    company_credit_code CHAR(18) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    legal_rep_id_card CHAR(18) NOT NULL,
    reg_address VARCHAR(200) NOT NULL,
    establish_date DATE NOT NULL,
    registered_capital DECIMAL(15,2) NOT NULL,
    business_status CHAR(10) NOT NULL CHECK (business_status IN ('在营', '注销', '吊销', '异常')),
    registration_authority VARCHAR(100) NOT NULL,
    business_scope VARCHAR(500) NOT NULL,
    PRIMARY KEY (company_credit_code),
    INDEX idx_legal_rep (legal_rep_id_card),
    INDEX idx_address_status (reg_address, business_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mtdb_enterprise_license (
    license_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    license_type VARCHAR(50) NOT NULL,
    license_no VARCHAR(50) NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    issuing_authority VARCHAR(100) NOT NULL,
    annual_inspection_status CHAR(10) NOT NULL CHECK (annual_inspection_status IN ('合格', '不合格', '未年检')),
    PRIMARY KEY (license_id),
    INDEX idx_company_type (company_credit_code, license_type),
    INDEX idx_valid_status (valid_to, annual_inspection_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mtdb_addr_change (
    change_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    old_address VARCHAR(200) NOT NULL,
    new_address VARCHAR(200) NOT NULL,
    change_date DATE NOT NULL,
    change_reason VARCHAR(100),
    approval_status CHAR(10) NOT NULL CHECK (approval_status IN ('已审批', '待审批', '驳回')),
    approval_authority VARCHAR(100) NOT NULL,
    PRIMARY KEY (change_id),
    INDEX idx_company_date (company_credit_code, change_date),
    INDEX idx_new_address (new_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mtdb_abnormal_list (
    abnormal_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    abnormal_type CHAR(15) NOT NULL CHECK (abnormal_type IN ('地址失联', '未年报', '公示信息造假', '列入经营异常')),
    listing_date DATE NOT NULL,
    removal_date DATE,
    listing_reason VARCHAR(200) NOT NULL,
    removal_reason VARCHAR(200),
    authority VARCHAR(100) NOT NULL,
    PRIMARY KEY (abnormal_id),
    INDEX idx_company_type (company_credit_code, abnormal_type),
    INDEX idx_listing_removal (listing_date, removal_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mtdb_individual_reg (
    credit_code CHAR(18) NOT NULL,
    operator_id_card CHAR(18) NOT NULL,
    business_address VARCHAR(200) NOT NULL,
    business_scope VARCHAR(300) NOT NULL,
    establish_date DATE NOT NULL,
    business_status CHAR(10) NOT NULL CHECK (business_status IN ('在营', '注销', '异常')),
    registration_authority VARCHAR(100) NOT NULL,
    employee_count INT NOT NULL DEFAULT 1,
    PRIMARY KEY (credit_code),
    INDEX idx_operator (operator_id_card),
    INDEX idx_status_date (business_status, establish_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mtdb_equity_change (
    change_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    old_shareholder_id VARCHAR(20) NOT NULL,
    new_shareholder_id VARCHAR(20) NOT NULL,
    change_date DATE NOT NULL,
    share_ratio DECIMAL(5,2) NOT NULL,
    transfer_amount DECIMAL(15,2),
    filing_status CHAR(10) NOT NULL CHECK (filing_status IN ('已备案', '未备案')),
    PRIMARY KEY (change_id),
    INDEX idx_company_date (company_credit_code, change_date),
    INDEX idx_old_new_shareholder (old_shareholder_id, new_shareholder_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- 五、民政补贴发放数据库（CABDB）表创建
-- ===================================================================
USE CABDB;

CREATE TABLE IF NOT EXISTS cabdb_unemployment_benefit (
    disbursement_id BIGINT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    benefit_period CHAR(6) NOT NULL,
    benefit_amount DECIMAL(8,2) NOT NULL,
    bank_account VARCHAR(30) NOT NULL,
    disbursement_status CHAR(10) NOT NULL CHECK (disbursement_status IN ('已发放', '待发放', '停发')),
    declared_employment_status CHAR(10) NOT NULL CHECK (declared_employment_status IN ('失业', '灵活就业')),
    applying_agency VARCHAR(100) NOT NULL,
    PRIMARY KEY (disbursement_id),
    INDEX idx_id_card_period (id_card, benefit_period),
    INDEX idx_status_account (disbursement_status, bank_account)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cabdb_subsistence_benefit (
    disbursement_id BIGINT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    benefit_type CHAR(10) NOT NULL CHECK (benefit_type IN ('城市低保', '农村低保')),
    household_size INT NOT NULL,
    monthly_amount DECIMAL(8,2) NOT NULL,
    disbursement_date DATE NOT NULL,
    declared_household_income DECIMAL(8,2) NOT NULL,
    household_address VARCHAR(200) NOT NULL,
    disbursement_status CHAR(10) NOT NULL CHECK (disbursement_status IN ('发放中', '已停发')),
    PRIMARY KEY (disbursement_id),
    INDEX idx_id_card_status (id_card, disbursement_status),
    INDEX idx_declared_income (declared_household_income)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cabdb_enterprise_startup (
    application_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    legal_rep_id_card CHAR(18) NOT NULL,
    subsidy_type CHAR(15) NOT NULL CHECK (subsidy_type IN ('首次创业补贴', '小微企业补贴', '科技创业补贴')),
    subsidy_amount DECIMAL(12,2) NOT NULL,
    apply_date DATE NOT NULL,
    approval_status CHAR(10) NOT NULL CHECK (approval_status IN ('已审批', '待审批', '驳回')),
    approval_date DATE,
    min_insured_count INT NOT NULL,
    PRIMARY KEY (application_id),
    INDEX idx_company_type (company_credit_code, subsidy_type),
    INDEX idx_approval_insured (approval_status, min_insured_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cabdb_temporary_aid (
    aid_id INT AUTO_INCREMENT NOT NULL,
    id_card CHAR(18) NOT NULL,
    aid_reason VARCHAR(100) NOT NULL,
    aid_amount DECIMAL(8,2) NOT NULL,
    disbursement_date DATE NOT NULL,
    declared_household_assets DECIMAL(15,2) NOT NULL,
    applying_agency VARCHAR(100) NOT NULL,
    PRIMARY KEY (aid_id),
    INDEX idx_id_card_date (id_card, disbursement_date),
    INDEX idx_declared_assets (declared_household_assets)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cabdb_qualification_check (
    check_id INT AUTO_INCREMENT NOT NULL,
    ref_id CHAR(18) NOT NULL,
    subject_type CHAR(5) NOT NULL CHECK (subject_type IN ('个人', '企业')),
    subsidy_type CHAR(15) NOT NULL,
    check_date DATE NOT NULL,
    check_result CHAR(10) NOT NULL CHECK (check_result IN ('通过', '驳回')),
    rejection_reason VARCHAR(200),
    check_basis VARCHAR(500) NOT NULL,
    PRIMARY KEY (check_id),
    INDEX idx_ref_subsidy (ref_id, subsidy_type),
    INDEX idx_result_date (check_result, check_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cabdb_benefit_recovery (
    recovery_id INT AUTO_INCREMENT NOT NULL,
    ref_id CHAR(18) NOT NULL,
    subject_type CHAR(5) NOT NULL CHECK (subject_type IN ('个人', '企业')),
    subsidy_type CHAR(15) NOT NULL,
    recovery_amount DECIMAL(12,2) NOT NULL,
    recovery_reason VARCHAR(200) NOT NULL,
    recovery_date DATE,
    handling_result CHAR(15) NOT NULL CHECK (handling_result IN ('已追回', '待追回', '无法追回')),
    PRIMARY KEY (recovery_id),
    INDEX idx_ref_subsidy (ref_id, subsidy_type),
    INDEX idx_result_amount (handling_result, recovery_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- 六、统计数据申报数据库（STDDB）表创建
-- ===================================================================
USE STDDB;

CREATE TABLE IF NOT EXISTS stddb_enterprise_revenue (
    report_id BIGINT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    reporting_month CHAR(6) NOT NULL,
    main_revenue DECIMAL(15,2) NOT NULL,
    other_revenue DECIMAL(15,2) NOT NULL DEFAULT 0,
    total_revenue DECIMAL(15,2) NOT NULL,
    reporting_status CHAR(10) NOT NULL CHECK (reporting_status IN ('已申报', '未申报', '补申报')),
    reporter VARCHAR(50) NOT NULL,
    contact_info VARCHAR(20) NOT NULL,
    PRIMARY KEY (report_id),
    INDEX idx_company_month (company_credit_code, reporting_month),
    INDEX idx_total_status (total_revenue, reporting_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stddb_industrial_output (
    report_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    reporting_period CHAR(7) NOT NULL,
    industrial_output_value DECIMAL(18,2) NOT NULL,
    industrial_added_value DECIMAL(18,2) NOT NULL,
    product_sales DECIMAL(12,2) NOT NULL,
    product_output DECIMAL(12,2) NOT NULL,
    report_status CHAR(10) NOT NULL CHECK (report_status IN ('已审核', '待审核', '退回')),
    PRIMARY KEY (report_id),
    INDEX idx_company_period (company_credit_code, reporting_period),
    INDEX idx_output_added (industrial_output_value, industrial_added_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stddb_region_gdp (
    data_id INT AUTO_INCREMENT NOT NULL,
    region_code CHAR(6) NOT NULL,
    reporting_month CHAR(6) NOT NULL,
    industrial_added_value DECIMAL(20,2) NOT NULL,
    service_added_value DECIMAL(20,2) NOT NULL,
    fixed_asset_investment DECIMAL(20,2) NOT NULL,
    retail_sales DECIMAL(20,2) NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    audit_status CHAR(10) NOT NULL CHECK (audit_status IN ('已通过', '待审核', '存疑')),
    PRIMARY KEY (data_id),
    UNIQUE INDEX uk_region_month (region_code, reporting_month),
    INDEX idx_region_status (region_code, audit_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stddb_enterprise_employees (
    stat_id INT AUTO_INCREMENT NOT NULL,
    company_credit_code CHAR(18) NOT NULL,
    reporting_month CHAR(6) NOT NULL,
    total_employees INT NOT NULL,
    full_time_employees INT NOT NULL,
    temporary_employees INT NOT NULL DEFAULT 0,
    avg_salary DECIMAL(10,2) NOT NULL,
    stat_status CHAR(10) NOT NULL CHECK (stat_status IN ('已确认', '待确认')),
    PRIMARY KEY (stat_id),
    INDEX idx_company_month (company_credit_code, reporting_month),
    INDEX idx_total_employees (total_employees)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stddb_investment_project (
    project_id INT AUTO_INCREMENT NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    builder_credit_code CHAR(18) NOT NULL,
    planned_investment DECIMAL(20,2) NOT NULL,
    actual_investment DECIMAL(20,2) NOT NULL,
    start_date DATE NOT NULL,
    project_status CHAR(15) NOT NULL CHECK (project_status IN ('在建', '已完工', '停工')),
    investment_sector VARCHAR(50) NOT NULL,
    PRIMARY KEY (project_id),
    INDEX idx_builder_status (builder_credit_code, project_status),
    INDEX idx_actual_start (actual_investment, start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stddb_abnormal_data (
    anomaly_id INT AUTO_INCREMENT NOT NULL,
    ref_id VARCHAR(20) NOT NULL,
    data_type CHAR(15) NOT NULL CHECK (data_type IN ('营收', '产值', 'GDP', '从业人员', '投资')),
    anomaly_reason VARCHAR(200) NOT NULL,
    discovery_date DATE NOT NULL,
    rectification_status CHAR(10) NOT NULL CHECK (rectification_status IN ('已整改', '待整改', '无法整改')),
    rectification_measures VARCHAR(200),
    inspector VARCHAR(50) NOT NULL,
    PRIMARY KEY (anomaly_id),
    INDEX idx_ref_type (ref_id, data_type),
    INDEX idx_status_date (rectification_status, discovery_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
