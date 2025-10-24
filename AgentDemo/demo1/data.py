from faker import Faker
import pymysql
import random
from datetime import datetime, timedelta
import os

# 加载环境变量
fake = Faker("zh_CN")
Faker.seed(42)  # 固定随机种子，保证数据可复现

# 数据库连接配置
DB_CONFIG = {
    "host": os.getenv(""),
    "port": int(os.getenv("3306")),
    "user": os.getenv("root"),
    "password": os.getenv("root"),
    "charset": "utf8mb4"
}


# -------------------------- 工具函数 --------------------------
def get_db_connection(db_name=None):
    """创建数据库连接（支持指定数据库）"""
    conn = pymysql.connect(
        **DB_CONFIG,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


def generate_id_card():
    """生成符合规则的18位身份证号（含出生日期逻辑）"""
    # 前6位：随机真实地区代码（示例：浙江杭州、江苏南京、广东深圳）
    area_codes = ["330106", "330108", "320102", "320104", "440305", "440306"]
    area_code = random.choice(area_codes)
    # 中间8位：1950-2005年随机出生日期（YYYYMMDD）
    birth_date = fake.date_between(start_date="-75y", end_date="-19y").strftime("%Y%m%d")
    # 后4位：随机序列+校验位（简化生成，实际需校验算法，此处用固定后缀保证格式）
    seq = random.randint(100, 999)
    check_bit = random.choice("0123456789X")
    return f"{area_code}{birth_date}{seq}{check_bit}"


def generate_company_credit_code():
    """生成符合规则的18位企业社会信用代码（前2位固定为91，代表企业）"""
    prefix = "91"
    area_code = random.choice(["330106", "330108", "320102", "320104", "440305", "440306"])
    org_code = fake.random_int(min=10000000, max=99999999)  # 8位组织机构代码
    check_bit = random.choice("0123456789ABCDEFGHJKLMNPQRTUWXY")  # 信用代码校验位允许字符
    return f"{prefix}{area_code}{org_code}{check_bit}"


def generate_date_between(start, end):
    """生成指定时间范围内的日期"""
    return fake.date_between(start_date=start, end_date=end)


def generate_char6_date(date_obj):
    """将日期转换为YYYYMM格式（如202405）"""
    return date_obj.strftime("%Y%m")


# -------------------------- 1. 社保监管数据库（SBDB）数据生成 --------------------------
def generate_sbdb_data():
    conn = get_db_connection("SBDB")
    cursor = conn.cursor()

    # -------------------------- 1.1 sbdb_person_base（500行） --------------------------
    person_ids = []  # 存储生成的身份证号，用于后续表关联
    for _ in range(500):
        id_card = generate_id_card()
        person_ids.append(id_card)
        name = fake.name()
        gender = random.choice(["男", "女"])
        # 从身份证号提取出生日期（第7-14位）
        birth_date = datetime.strptime(id_card[6:14], "%Y%m%d").date()
        household_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        insurance_status = random.choices(["正常", "停保", "注销"], weights=[7, 2, 1])[0]
        # 首次参保日期：年满16岁后，早于当前日期
        first_insurance_year = birth_date.year + 16 + random.randint(0, 30)
        first_insurance_date = generate_date_between(
            start=f"{first_insurance_year}-01-01",
            end=datetime.now().date() - timedelta(days=30)
        )

        sql = """
              INSERT INTO sbdb_person_base
              (id_card, name, gender, birth_date, household_address, insurance_status, first_insurance_date)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (id_card, name, gender, birth_date, household_address, insurance_status, first_insurance_date))
    conn.commit()
    print("sbdb_person_base 数据生成完成（500行）")

    # -------------------------- 1.2 sbdb_employment_reg（500行） --------------------------
    company_codes = generate_company_credit_code()  # 先生成1个企业代码，后续可扩展
    for _ in range(500):
        reg_id = None  # 自增主键，无需手动生成
        id_card = random.choice(person_ids)
        employment_status = random.choices(["在职", "失业", "灵活就业"], weights=[6, 3, 1])[0]
        company_credit_code = generate_company_credit_code()
        # 入职日期：在职/灵活就业→早于当前；失业→早于离职日期
        hire_date = generate_date_between(start="-10y", end=datetime.now().date() - timedelta(days=1))
        leave_date = None
        if employment_status == "失业":
            leave_date = generate_date_between(start=hire_date, end=datetime.now().date() - timedelta(days=1))
        reg_agency = f"{fake.city()}人社局/{fake.district()}就业服务中心"

        sql = """
              INSERT INTO sbdb_employment_reg
              (id_card, employment_status, company_credit_code, hire_date, leave_date, reg_agency)
              VALUES (%s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, employment_status, company_credit_code, hire_date, leave_date, reg_agency))
    conn.commit()
    print("sbdb_employment_reg 数据生成完成（500行）")

    # -------------------------- 1.3 sbdb_enterprise_insure（500行） --------------------------
    enterprise_codes = []  # 存储企业代码，用于后续表关联
    for _ in range(500):
        insure_id = None
        company_credit_code = generate_company_credit_code()
        enterprise_codes.append(company_credit_code)
        insured_count = random.randint(1, 200)  # 参保人数1-200人
        # 参保起始日期：早于当前，且晚于企业成立日期（简化：假设成立日期=参保起始日期-30天）
        insure_start_date = generate_date_between(start="-15y", end=datetime.now().date() - timedelta(days=30))
        insure_type = random.choice(["五险", "单险", "灵活就业参保"])
        social_security_dept = f"{fake.city()}社保中心/{fake.district()}分中心"

        sql = """
              INSERT INTO sbdb_enterprise_insure
              (company_credit_code, insured_count, insure_start_date, insure_type, social_security_dept)
              VALUES (%s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, insured_count, insure_start_date, insure_type, social_security_dept))
    conn.commit()
    print("sbdb_enterprise_insure 数据生成完成（500行）")

    # -------------------------- 1.4 sbdb_payment_detail（600行，含多期缴费） --------------------------
    for _ in range(600):
        payment_id = None
        id_card = random.choice(person_ids)
        company_credit_code = random.choice(enterprise_codes)
        # 缴费所属期：近24个月内随机
        payment_period_date = generate_date_between(start="-24m", end=datetime.now().date())
        payment_period = generate_char6_date(payment_period_date)
        # 社保缴费基数：当地上下限（假设3800-24000）
        contribution_base = round(random.uniform(3800, 24000), 2)
        # 个人缴费：养老8%+医疗2%+失业0.5% = 10.5%
        personal_payment = round(contribution_base * 0.105, 2)
        # 企业缴费：养老16%+医疗8%+失业0.5%+工伤0.5%+生育0.8% = 25.8%
        employer_payment = round(contribution_base * 0.258, 2)
        payment_status = random.choices(["已缴", "欠缴", "补缴"], weights=[8, 1, 1])[0]

        sql = """
              INSERT INTO sbdb_payment_detail
              (id_card, company_credit_code, payment_period, contribution_base, personal_payment, employer_payment, \
               payment_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, company_credit_code, payment_period, contribution_base, personal_payment,
                             employer_payment, payment_status))
    conn.commit()
    print("sbdb_payment_detail 数据生成完成（600行）")

    # -------------------------- 1.5 sbdb_benefit_apply（500行） --------------------------
    for _ in range(500):
        apply_id = None
        id_card = random.choice(person_ids)
        benefit_type = random.choice(["养老金", "失业金", "医保报销", "工伤补贴", "生育津贴"])
        apply_date = generate_date_between(start="-5y", end=datetime.now().date())
        # 待遇金额：按类型区分
        if benefit_type == "养老金":
            benefit_amount = round(random.uniform(2000, 8000), 2)
        elif benefit_type == "失业金":
            benefit_amount = round(random.uniform(1500, 3000), 2)
        elif benefit_type == "医保报销":
            benefit_amount = round(random.uniform(500, 50000), 2)
        elif benefit_type == "工伤补贴":
            benefit_amount = round(random.uniform(3000, 20000), 2)
        else:  # 生育津贴
            benefit_amount = round(random.uniform(5000, 30000), 2)
        disbursement_status = random.choice(["待发放", "发放中", "已停发"])
        bank_account = fake.credit_card_number(card_type="visa").replace("-", "")[:20]  # 简化银行卡号

        sql = """
              INSERT INTO sbdb_benefit_apply
              (id_card, benefit_type, apply_date, benefit_amount, disbursement_status, bank_account)
              VALUES (%s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, benefit_type, apply_date, benefit_amount, disbursement_status, bank_account))
    conn.commit()
    print("sbdb_benefit_apply 数据生成完成（500行）")

    # -------------------------- 1.6 sbdb_violation_rec（300行，违规记录少于正常记录） --------------------------
    for _ in range(300):
        violation_id = None
        subject_type = random.choice(["个人", "企业"])
        if subject_type == "个人":
            ref_id = random.choice(person_ids)
        else:
            ref_id = random.choice(enterprise_codes)
        violation_type = random.choice(["骗保", "欠缴", "重复申领", "资格造假"])
        violation_amount = round(random.uniform(1000, 50000), 2)
        handling_result = random.choices(["已追回", "待追回", "已处罚", "整改中"], weights=[4, 3, 2, 1])[0]
        handling_date = generate_date_between(start="-3y", end=datetime.now().date())
        handling_agency = f"{fake.city()}社保稽查局/{fake.district()}执法大队"

        sql = """
              INSERT INTO sbdb_violation_rec
              (ref_id, subject_type, violation_type, violation_amount, handling_result, handling_date, handling_agency)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (ref_id, subject_type, violation_type, violation_amount, handling_result, handling_date,
                             handling_agency))
    conn.commit()
    print("sbdb_violation_rec 数据生成完成（300行）")

    cursor.close()
    conn.close()


# -------------------------- 2. 税务监管数据库（TAXDB）数据生成 --------------------------
def generate_taxdb_data():
    conn = get_db_connection("TAXDB")
    cursor = conn.cursor()

    # 关联SBDB的人员和企业数据（从SBDB查询已生成的ID）
    sbdb_conn = get_db_connection("SBDB")
    sbdb_cursor = sbdb_conn.cursor()
    sbdb_cursor.execute("SELECT id_card FROM sbdb_person_base LIMIT 500")
    person_ids = [row["id_card"] for row in sbdb_cursor.fetchall()]
    sbdb_cursor.execute("SELECT company_credit_code FROM sbdb_enterprise_insure LIMIT 500")
    enterprise_codes = [row["company_credit_code"] for row in sbdb_cursor.fetchall()]
    sbdb_cursor.close()
    sbdb_conn.close()

    # -------------------------- 2.1 taxdb_enterprise_reg（500行） --------------------------
    for _ in range(500):
        reg_id = None
        company_credit_code = random.choice(enterprise_codes)
        taxpayer_type = random.choice(["一般纳税人", "小规模纳税人"])
        tax_reg_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        tax_bureau = f"{fake.city()}税务局/{fake.district()}分局"
        reg_date = generate_date_between(start="-15y", end=datetime.now().date() - timedelta(days=30))
        cancel_date = None
        if random.random() < 0.1:  # 10%概率已注销
            cancel_date = generate_date_between(start=reg_date, end=datetime.now().date() - timedelta(days=1))

        sql = """
              INSERT INTO taxdb_enterprise_reg
              (company_credit_code, taxpayer_type, tax_reg_address, tax_bureau, reg_date, cancel_date)
              VALUES (%s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, taxpayer_type, tax_reg_address, tax_bureau, reg_date, cancel_date))
    conn.commit()
    print("taxdb_enterprise_reg 数据生成完成（500行）")

    # -------------------------- 2.2 taxdb_enterprise_vat（600行，月度申报） --------------------------
    for _ in range(600):
        vat_id = None
        company_credit_code = random.choice(enterprise_codes)
        reporting_period_date = generate_date_between(start="-24m", end=datetime.now().date())
        reporting_period = generate_char6_date(reporting_period_date)
        # 营业收入：小规模→10万以内，一般纳税人→10万-500万
        taxpayer_type = random.choice(["一般纳税人", "小规模纳税人"])
        if taxpayer_type == "小规模纳税人":
            revenue = round(random.uniform(10000, 100000), 2)
        else:
            revenue = round(random.uniform(100000, 5000000), 2)
        output_tax = round(revenue * 0.13, 2)  # 增值税率13%（简化）
        input_tax = round(output_tax * random.uniform(0.2, 0.8), 2)  # 进项税为销项的20%-80%
        payable_tax = round(max(0, output_tax - input_tax), 2)
        filing_status = random.choices(["已申报", "未申报", "逾期申报"], weights=[8, 1, 1])[0]
        filing_date = generate_date_between(start=reporting_period_date,
                                            end=reporting_period_date + timedelta(days=15))  # 申报期15天内

        sql = """
              INSERT INTO taxdb_enterprise_vat
              (company_credit_code, reporting_period, revenue, output_tax, input_tax, payable_tax, filing_status, \
               filing_date)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, reporting_period, revenue, output_tax, input_tax, payable_tax,
                             filing_status, filing_date))
    conn.commit()
    print("taxdb_enterprise_vat 数据生成完成（600行）")

    # -------------------------- 2.3 taxdb_person_income（600行，月度申报） --------------------------
    for _ in range(600):
        income_id = None
        id_card = random.choice(person_ids)
        reporting_period_date = generate_date_between(start="-24m", end=datetime.now().date())
        reporting_period = generate_char6_date(reporting_period_date)
        # 税前收入：高于社保基数（社保基数3800-24000，此处5000-30000）
        pre_tax_income = round(random.uniform(5000, 30000), 2)
        # 专项附加扣除：0-5000（子女教育、房贷等）
        special_deductions = round(random.uniform(0, 5000), 2)
        # 应纳税所得额：税前收入-5000起征点-专项扣除
        taxable_income = max(0, round(pre_tax_income - 5000 - special_deductions, 2))
        # 个税计算（简化：超额累进税率→10%税率）
        tax_paid = round(taxable_income * 0.1, 2)
        employer_credit_code = random.choice(enterprise_codes)
        filing_status = random.choices(["已申报", "未申报", "补申报"], weights=[8, 1, 1])[0]

        sql = """
              INSERT INTO taxdb_person_income
              (id_card, reporting_period, pre_tax_income, special_deductions, taxable_income, tax_paid, \
               employer_credit_code, filing_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, reporting_period, pre_tax_income, special_deductions, taxable_income, tax_paid,
                             employer_credit_code, filing_status))
    conn.commit()
    print("taxdb_person_income 数据生成完成（600行）")

    # -------------------------- 2.4 taxdb_invoice_detail（800行，发票数量多于申报） --------------------------
    for _ in range(800):
        invoice_id = None
        invoice_no = f"Invoice{random.randint(10000000, 99999999)}"  # 唯一发票号
        seller_credit_code = random.choice(enterprise_codes)
        buyer_id = random.choice(person_ids) if random.random() < 0.3 else generate_company_credit_code()  # 30%个人买家
        issue_date = generate_date_between(start="-24m", end=datetime.now().date())
        invoice_amount = round(random.uniform(1000, 100000), 2)
        invoice_type = random.choice(["增值税专票", "增值税普票", "电子发票"])
        goods_service_name = random.choice(["办公用品", "电子产品", "咨询服务", "建筑服务", "货物运输"])
        invoice_status = random.choices(["正常", "作废", "红冲"], weights=[9, 0.5, 0.5])[0]

        sql = """
              INSERT INTO taxdb_invoice_detail
              (invoice_no, seller_credit_code, buyer_id, issue_date, invoice_amount, invoice_type, goods_service_name, \
               invoice_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (invoice_no, seller_credit_code, buyer_id, issue_date, invoice_amount, invoice_type,
                             goods_service_name, invoice_status))
    conn.commit()
    print("taxdb_invoice_detail 数据生成完成（800行）")

    # -------------------------- 2.5 taxdb_enterprise_income（500行，年度申报） --------------------------
    for _ in range(500):
        income_report_id = None
        company_credit_code = random.choice(enterprise_codes)
        report_year = random.randint(2020, datetime.now().year - 1)  # 前3年数据
        # 利润总额：营业收入的5%-20%（假设年营收100万-1亿）
        annual_revenue = random.uniform(1000000, 100000000)
        total_profit = round(annual_revenue * random.uniform(0.05, 0.2), 2)
        taxable_profit = round(total_profit * random.uniform(0.9, 1.1), 2)  # 纳税调整±10%
        income_tax = round(taxable_profit * 0.25, 2)  # 企业所得税率25%
        total_assets = round(annual_revenue * random.uniform(1.5, 3), 2)  # 资产为营收1.5-3倍
        employee_count = random.randint(1, 200)  # 从业人数1-200
        filing_date = generate_date_between(start=f"{report_year + 1}-01-01",
                                            end=f"{report_year + 1}-05-31")  # 次年5月31日前申报

        sql = """
              INSERT INTO taxdb_enterprise_income
              (company_credit_code, report_year, total_profit, taxable_profit, income_tax, total_assets, employee_count, \
               filing_date)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, report_year, total_profit, taxable_profit, income_tax, total_assets,
                             employee_count, filing_date))
    conn.commit()
    print("taxdb_enterprise_income 数据生成完成（500行）")

    # -------------------------- 2.6 taxdb_punishment_rec（200行，处罚记录较少） --------------------------
    for _ in range(200):
        punishment_id = None
        subject_type = random.choice(["个人", "企业"])
        if subject_type == "个人":
            ref_id = random.choice(person_ids)
        else:
            ref_id = random.choice(enterprise_codes)
        violation_type = random.choice(["偷税", "虚开发票", "欠缴税款", "申报造假"])
        penalty_amount = round(random.uniform(5000, 100000), 2)
        penalty_date = generate_date_between(start="-3y", end=datetime.now().date())
        rectification_status = random.choices(["已整改", "待整改", "未整改"], weights=[5, 3, 2])[0]
        penalty_doc_no = f"TaxPenalty{random.randint(10000, 99999)}"

        sql = """
              INSERT INTO taxdb_punishment_rec
              (ref_id, subject_type, violation_type, penalty_amount, penalty_date, rectification_status, penalty_doc_no)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (ref_id, subject_type, violation_type, penalty_amount, penalty_date, rectification_status,
                             penalty_doc_no))
    conn.commit()
    print("taxdb_punishment_rec 数据生成完成（200行）")

    cursor.close()
    conn.close()


# -------------------------- 3. 市场监督管理数据库（MTDB）数据生成 --------------------------
def generate_mtdb_data():
    conn = get_db_connection("MTDB")
    cursor = conn.cursor()

    # 关联SBDB的人员数据
    sbdb_conn = get_db_connection("SBDB")
    sbdb_cursor = sbdb_conn.cursor()
    sbdb_cursor.execute("SELECT id_card FROM sbdb_person_base LIMIT 500")
    person_ids = [row["id_card"] for row in sbdb_cursor.fetchall()]
    sbdb_cursor.close()
    sbdb_conn.close()

    # 生成企业和个体户代码（500企业+300个体户）
    enterprise_codes = [generate_company_credit_code() for _ in range(500)]
    individual_codes = [generate_company_credit_code().replace("91", "92") for _ in range(300)]  # 个体户信用代码前缀92

    # -------------------------- 3.1 mtdb_enterprise_reg（500行） --------------------------
    for _ in range(500):
        company_credit_code = enterprise_codes[_]
        company_name = fake.company()
        legal_rep_id_card = random.choice(person_ids)
        reg_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        establish_date = generate_date_between(start="-15y", end=datetime.now().date() - timedelta(days=30))
        registered_capital = round(random.uniform(100000, 10000000), 2)  # 注册资本10万-1000万
        business_status = random.choices(["在营", "注销", "吊销", "异常"], weights=[7, 1, 0.5, 1.5])[0]
        registration_authority = f"{fake.city()}市场监管局/{fake.district()}分局"
        business_scope = random.choice([
            "计算机软硬件销售；技术服务",
            "食品销售；餐饮服务",
            "建筑工程施工；装饰装修",
            "医疗器械销售；健康咨询",
            "汽车销售；维修服务"
        ])

        sql = """
              INSERT INTO mtdb_enterprise_reg
              (company_credit_code, company_name, legal_rep_id_card, reg_address, establish_date, registered_capital, \
               business_status, registration_authority, business_scope)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, company_name, legal_rep_id_card, reg_address, establish_date,
                             registered_capital, business_status, registration_authority, business_scope))
    conn.commit()
    print("mtdb_enterprise_reg 数据生成完成（500行）")

    # -------------------------- 3.2 mtdb_enterprise_license（500行） --------------------------
    for _ in range(500):
        license_id = None
        company_credit_code = random.choice(enterprise_codes)
        license_type = random.choice([
            "食品经营许可", "医疗器械经营许可", "建筑工程施工许可",
            "道路运输经营许可", "餐饮服务许可"
        ])
        license_no = f"License{random.randint(10000000, 99999999)}"
        valid_from = generate_date_between(start="-10y", end=datetime.now().date() - timedelta(days=30))
        valid_to = valid_from + timedelta(days=365 * random.randint(3, 5))  # 有效期3-5年
        issuing_authority = f"{fake.city()}卫健委/{fake.city()}住建局/{fake.city()}交通局"
        annual_inspection_status = random.choices(["合格", "不合格", "未年检"], weights=[8, 1, 1])[0]

        sql = """
              INSERT INTO mtdb_enterprise_license
              (company_credit_code, license_type, license_no, valid_from, valid_to, issuing_authority, \
               annual_inspection_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, license_type, license_no, valid_from, valid_to, issuing_authority,
                             annual_inspection_status))
    conn.commit()
    print("mtdb_enterprise_license 数据生成完成（500行）")

    # -------------------------- 3.3 mtdb_addr_change（300行，部分企业有地址变更） --------------------------
    for _ in range(300):
        change_id = None
        company_credit_code = random.choice(enterprise_codes)
        old_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        new_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        while new_address == old_address:  # 确保新地址不同
            new_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        change_date = generate_date_between(start="-5y", end=datetime.now().date() - timedelta(days=1))
        change_reason = random.choice(["经营规模扩大", "原地址拆迁", "区域政策调整", "地址异常整改"])
        approval_status = random.choices(["已审批", "待审批", "驳回"], weights=[9, 0.5, 0.5])[0]
        approval_authority = f"{fake.city()}市场监管局"

        sql = """
              INSERT INTO mtdb_addr_change
              (company_credit_code, old_address, new_address, change_date, change_reason, approval_status, \
               approval_authority)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, old_address, new_address, change_date, change_reason, approval_status,
                             approval_authority))
    conn.commit()
    print("mtdb_addr_change 数据生成完成（300行）")

    # -------------------------- 3.4 mtdb_abnormal_list（200行，经营异常企业） --------------------------
    for _ in range(200):
        abnormal_id = None
        company_credit_code = random.choice(enterprise_codes)
        abnormal_type = random.choice(["地址失联", "未年报", "公示信息造假", "列入经营异常"])
        listing_date = generate_date_between(start="-3y", end=datetime.now().date() - timedelta(days=1))
        removal_date = None
        if random.random() < 0.4:  # 40%概率已移出异常
            removal_date = generate_date_between(start=listing_date, end=datetime.now().date() - timedelta(days=1))
        listing_reason = random.choice([
            "通过登记的住所或者经营场所无法联系",
            "未按规定期限公示年度报告",
            "公示企业信息隐瞒真实情况、弄虚作假",
            "未按规定履行即时信息公示义务"
        ])
        removal_reason = "已完成地址变更并公示" if removal_date else None
        authority = f"{fake.city()}市场监管局"

        sql = """
              INSERT INTO mtdb_abnormal_list
              (company_credit_code, abnormal_type, listing_date, removal_date, listing_reason, removal_reason, \
               authority)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (company_credit_code, abnormal_type, listing_date, removal_date, listing_reason, removal_reason,
                        authority))
    conn.commit()
    print("mtdb_abnormal_list 数据生成完成（200行）")

    # -------------------------- 3.5 mtdb_individual_reg（300行，个体户） --------------------------
    for _ in range(300):
        credit_code = individual_codes[_]
        operator_id_card = random.choice(person_ids)
        business_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        business_scope = random.choice([
            "日用百货零售", "餐饮服务（小吃店）", "水果销售",
            "家电维修", "服装零售"
        ])
        establish_date = generate_date_between(start="-10y", end=datetime.now().date() - timedelta(days=30))
        business_status = random.choices(["在营", "注销", "异常"], weights=[8, 1, 1])[0]
        registration_authority = f"{fake.district()}市场监管所"
        employee_count = random.randint(1, 5)  # 个体户从业人员1-5人

        sql = """
              INSERT INTO mtdb_individual_reg
              (credit_code, operator_id_card, business_address, business_scope, establish_date, business_status, \
               registration_authority, employee_count)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (credit_code, operator_id_card, business_address, business_scope, establish_date,
                             business_status, registration_authority, employee_count))
    conn.commit()
    print("mtdb_individual_reg 数据生成完成（300行）")

    # -------------------------- 3.6 mtdb_equity_change（200行，股权变更） --------------------------
    for _ in range(200):
        change_id = None
        company_credit_code = random.choice(enterprise_codes)
        # 原股东：50%个人，50%企业
        old_shareholder_id = random.choice(person_ids) if random.random() < 0.5 else generate_company_credit_code()
        new_shareholder_id = random.choice(person_ids) if random.random() < 0.5 else generate_company_credit_code()
        while new_shareholder_id == old_shareholder_id:  # 确保新老股东不同
            new_shareholder_id = random.choice(person_ids) if random.random() < 0.5 else generate_company_credit_code()
        change_date = generate_date_between(start="-5y", end=datetime.now().date() - timedelta(days=1))
        share_ratio = round(random.uniform(5, 100), 2)  # 变更持股比例5%-100%
        transfer_amount = round(random.uniform(10000, 1000000), 2)  # 转让金额1万-100万
        filing_status = random.choices(["已备案", "未备案"], weights=[8, 2])[0]

        sql = """
              INSERT INTO mtdb_equity_change
              (company_credit_code, old_shareholder_id, new_shareholder_id, change_date, share_ratio, transfer_amount, \
               filing_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, old_shareholder_id, new_shareholder_id, change_date, share_ratio,
                             transfer_amount, filing_status))
    conn.commit()
    print("mtdb_equity_change 数据生成完成（200行）")

    cursor.close()
    conn.close()


# -------------------------- 4. 民政补贴发放数据库（CABDB）数据生成 --------------------------
def generate_cabdb_data():
    conn = get_db_connection("CABDB")
    cursor = conn.cursor()

    # 关联SBDB和MTDB的数据
    sbdb_conn = get_db_connection("SBDB")
    sbdb_cursor = sbdb_conn.cursor()
    sbdb_cursor.execute("SELECT id_card FROM sbdb_person_base LIMIT 500")
    person_ids = [row["id_card"] for row in sbdb_cursor.fetchall()]
    sbdb_cursor.execute("SELECT company_credit_code FROM sbdb_enterprise_insure LIMIT 500")
    enterprise_codes = [row["company_credit_code"] for row in sbdb_cursor.fetchall()]
    sbdb_cursor.close()
    sbdb_conn.close()

    mtdb_conn = get_db_connection("MTDB")
    mtdb_cursor = mtdb_conn.cursor()
    mtdb_cursor.execute("SELECT credit_code FROM mtdb_individual_reg LIMIT 300")
    individual_codes = [row["credit_code"] for row in mtdb_cursor.fetchall()]
    mtdb_cursor.close()
    mtdb_conn.close()

    # -------------------------- 4.1 cabdb_unemployment_benefit（500行） --------------------------
    for _ in range(500):
        disbursement_id = None
        id_card = random.choice(person_ids)
        benefit_period_date = generate_date_between(start="-24m", end=datetime.now().date())
        benefit_period = generate_char6_date(benefit_period_date)
        benefit_amount = round(random.uniform(1500, 3000), 2)  # 失业补贴1500-3000/月
        bank_account = fake.credit_card_number(card_type="mastercard").replace("-", "")[:20]
        disbursement_status = random.choices(["已发放", "待发放", "停发"], weights=[8, 1, 1])[0]
        declared_employment_status = random.choice(["失业", "灵活就业"])
        applying_agency = f"{fake.city()}民政局/{fake.district()}社保所"

        sql = """
              INSERT INTO cabdb_unemployment_benefit
              (id_card, benefit_period, benefit_amount, bank_account, disbursement_status, declared_employment_status, \
               applying_agency)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, benefit_period, benefit_amount, bank_account, disbursement_status,
                             declared_employment_status, applying_agency))
    conn.commit()
    print("cabdb_unemployment_benefit 数据生成完成（500行）")

    # -------------------------- 4.2 cabdb_subsistence_benefit（500行） --------------------------
    for _ in range(500):
        disbursement_id = None
        id_card = random.choice(person_ids)
        benefit_type = random.choice(["城市低保", "农村低保"])
        household_size = random.randint(1, 5)  # 家庭人口1-5人
        # 低保金额：城市800-1500/人/月，农村500-1000/人/月
        if benefit_type == "城市低保":
            per_person_amount = random.uniform(800, 1500)
        else:
            per_person_amount = random.uniform(500, 1000)
        monthly_amount = round(household_size * per_person_amount, 2)
        disbursement_date = generate_date_between(start="-24m", end=datetime.now().date())
        # 申报家庭收入：低于低保标准（城市＜800/人，农村＜500/人）
        declared_household_income = round(household_size * random.uniform(300, 700), 2)
        household_address = f"{fake.province()}{fake.city()}{fake.street_address()}"
        disbursement_status = random.choice(["发放中", "已停发"])

        sql = """
              INSERT INTO cabdb_subsistence_benefit
              (id_card, benefit_type, household_size, monthly_amount, disbursement_date, declared_household_income, \
               household_address, disbursement_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (id_card, benefit_type, household_size, monthly_amount, disbursement_date,
                             declared_household_income, household_address, disbursement_status))
    conn.commit()
    print("cabdb_subsistence_benefit 数据生成完成（500行）")

    # -------------------------- 4.3 cabdb_enterprise_startup（300行，创业补贴） --------------------------
    for _ in range(300):
        application_id = None
        company_credit_code = random.choice(enterprise_codes)
        legal_rep_id_card = random.choice(person_ids)
        subsidy_type = random.choice(["首次创业补贴", "小微企业补贴", "科技创业补贴"])
        # 补贴金额：首次5-10万，小微10-30万，科技20-50万
        if subsidy_type == "首次创业补贴":
            subsidy_amount = round(random.uniform(50000, 100000), 2)
        elif subsidy_type == "小微企业补贴":
            subsidy_amount = round(random.uniform(100000, 300000), 2)
        else:
            subsidy_amount = round(random.uniform(200000, 500000), 2)
        apply_date = generate_date_between(start="-2y", end=datetime.now().date())
        approval_status = random.choices(["已审批", "待审批", "驳回"], weights=[6, 2, 2])[0]
        approval_date = generate_date_between(start=apply_date, end=apply_date + timedelta(
            days=30)) if approval_status == "已审批" else None
        min_insured_count = random.randint(3, 10)  # 最低参保人数3-10人

        sql = """
              INSERT INTO cabdb_enterprise_startup
              (company_credit_code, legal_rep_id_card, subsidy_type, subsidy_amount, apply_date, approval_status, \
               approval_date, min_insured_count)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, legal_rep_id_card, subsidy_type, subsidy_amount, apply_date,
                             approval_status, approval_date, min_insured_count))
    conn.commit()
    print("cabdb_enterprise_startup 数据生成完成（300行）")

    # -------------------------- 4.4 cabdb_temporary_aid（400行，临时救助） --------------------------
    for _ in range(400):
        aid_id = None
        id_card = random.choice(person_ids)
        aid_reason = random.choice(["医疗困难", "自然灾害", "意外事故", "家庭突发困难"])
        # 救助金额：医疗5000-50000，其他1000-10000
        if aid_reason == "医疗困难":
            aid_amount = round(random.uniform(5000, 50000), 2)
        else:
            aid_amount = round(random.uniform(1000, 10000), 2)
        disbursement_date = generate_date_between(start="-3y", end=datetime.now().date())
        # 申报家庭财产：低于50万
        declared_household_assets = round(random.uniform(50000, 500000), 2)
        applying_agency = f"{fake.district()}民政局救助科"

        sql = """
              INSERT INTO cabdb_temporary_aid
              (id_card, aid_reason, aid_amount, disbursement_date, declared_household_assets, applying_agency)
              VALUES (%s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (id_card, aid_reason, aid_amount, disbursement_date, declared_household_assets, applying_agency))
    conn.commit()
    print("cabdb_temporary_aid 数据生成完成（400行）")

    # -------------------------- 4.5 cabdb_qualification_check（500行，资格审核） --------------------------
    for _ in range(500):
        check_id = None
        subject_type = random.choice(["个人", "企业"])
        if subject_type == "个人":
            ref_id = random.choice(person_ids)
            subsidy_type = random.choice(["失业补贴", "低保", "临时救助"])
        else:
            ref_id = random.choice(enterprise_codes)
            subsidy_type = random.choice(["创业补贴", "稳岗补贴"])
        check_date = generate_date_between(start="-24m", end=datetime.now().date())
        check_result = random.choices(["通过", "驳回"], weights=[7, 3])[0]
        rejection_reason = random.choice([
            "非失业状态", "家庭收入超标", "企业经营异常", "参保人数未达标"
        ]) if check_result == "驳回" else None
        check_basis = random.choice([
            "SBDB就业状态=失业", "TAXDB家庭收入＜低保标准", "MTDB经营状态=在营", "SBDB参保人数≥10人"
        ])

        sql = """
              INSERT INTO cabdb_qualification_check
              (ref_id, subject_type, subsidy_type, check_date, check_result, rejection_reason, check_basis)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (ref_id, subject_type, subsidy_type, check_date, check_result, rejection_reason, check_basis))
    conn.commit()
    print("cabdb_qualification_check 数据生成完成（500行）")

    # -------------------------- 4.6 cabdb_benefit_recovery（200行，补贴追回） --------------------------
    for _ in range(200):
        recovery_id = None
        subject_type = random.choice(["个人", "企业"])
        if subject_type == "个人":
            ref_id = random.choice(person_ids)
            subsidy_type = random.choice(["失业补贴", "低保"])
        else:
            ref_id = random.choice(enterprise_codes)
            subsidy_type = random.choice(["创业补贴", "稳岗补贴"])
        recovery_amount = round(random.uniform(3000, 50000), 2)
        recovery_reason = random.choice([
            "SBDB核查发现同期在职", "TAXDB核查发现家庭收入超标", "MTDB核查发现企业经营异常", "SBDB核查发现参保人数造假"
        ])
        recovery_date = generate_date_between(start=check_date,
                                              end=datetime.now().date()) if random.random() < 0.5 else None
        handling_result = random.choices(["已追回", "待追回", "无法追回"], weights=[4, 4, 2])[0]

        sql = """
              INSERT INTO cabdb_benefit_recovery
              (ref_id, subject_type, subsidy_type, recovery_amount, recovery_reason, recovery_date, handling_result)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (ref_id, subject_type, subsidy_type, recovery_amount, recovery_reason, recovery_date,
                             handling_result))
    conn.commit()
    print("cabdb_benefit_recovery 数据生成完成（200行）")

    cursor.close()
    conn.close()


# -------------------------- 5. 统计数据申报数据库（STDDB）数据生成 --------------------------
def generate_stddb_data():
    conn = get_db_connection("STDDB")
    cursor = conn.cursor()

    # 关联MTDB的企业数据
    mtdb_conn = get_db_connection("MTDB")
    mtdb_cursor = mtdb_conn.cursor()
    mtdb_cursor.execute("SELECT company_credit_code FROM mtdb_enterprise_reg LIMIT 500")
    enterprise_codes = [row["company_credit_code"] for row in mtdb_cursor.fetchall()]
    mtdb_cursor.close()
    mtdb_conn.close()

    # 区域代码（示例：6位行政代码）
    region_codes = ["330106", "330108", "320102", "320104", "440305", "440306", "110101", "110102"]

    # -------------------------- 5.1 stddb_enterprise_revenue（600行，月度营收） --------------------------
    for _ in range(600):
        report_id = None
        company_credit_code = random.choice(enterprise_codes)
        reporting_month_date = generate_date_between(start="-24m", end=datetime.now().date())
        reporting_month = generate_char6_date(reporting_month_date)
        main_revenue = round(random.uniform(100000, 5000000), 2)  # 主营业务收入10万-500万
        other_revenue = round(main_revenue * random.uniform(0.05, 0.2), 2)  # 其他收入5%-20%
        total_revenue = round(main_revenue + other_revenue, 2)
        reporting_status = random.choices(["已申报", "未申报", "补申报"], weights=[8, 1, 1])[0]
        reporter = fake.name()
        contact_info = fake.phone_number()

        sql = """
              INSERT INTO stddb_enterprise_revenue
              (company_credit_code, reporting_month, main_revenue, other_revenue, total_revenue, reporting_status, \
               reporter, contact_info)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, reporting_month, main_revenue, other_revenue, total_revenue,
                             reporting_status, reporter, contact_info))
    conn.commit()
    print("stddb_enterprise_revenue 数据生成完成（600行）")

    # -------------------------- 5.2 stddb_industrial_output（400行，工业产值） --------------------------
    for _ in range(400):
        report_id = None
        company_credit_code = random.choice(enterprise_codes)
        # 统计周期：50%年度（YYYY），50%季度（YYYYQ1-Q4）
        if random.random() < 0.5:
            report_year = random.randint(2020, datetime.now().year - 1)
            reporting_period = str(report_year)
        else:
            report_year = random.randint(2020, datetime.now().year - 1)
            quarter = random.randint(1, 4)
            reporting_period = f"{report_year}Q{quarter}"
        # 工业总产值：100万-1亿
        industrial_output_value = round(random.uniform(1000000, 100000000), 2)
        industrial_added_value = round(industrial_output_value * random.uniform(0.2, 0.4), 2)  # 增加值20%-40%
        product_sales = round(random.uniform(100, 10000), 2)  # 产品销量100-10000单位
        product_output = round(product_sales * random.uniform(1.05, 1.2), 2)  # 产量略高于销量
        report_status = random.choices(["已审核", "待审核", "退回"], weights=[7, 2, 1])[0]

        sql = """
              INSERT INTO stddb_industrial_output
              (company_credit_code, reporting_period, industrial_output_value, industrial_added_value, product_sales, \
               product_output, report_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (company_credit_code, reporting_period, industrial_output_value, industrial_added_value,
                             product_sales, product_output, report_status))
    conn.commit()
    print("stddb_industrial_output 数据生成完成（400行）")

    # -------------------------- 5.3 stddb_region_gdp（200行，区域GDP） --------------------------
    for _ in range(200):
        data_id = None
        region_code = random.choice(region_codes)
        reporting_month_date = generate_date_between(start="-24m", end=datetime.now().date())
        reporting_month = generate_char6_date(reporting_month_date)
        # 区域工业增加值：1亿-100亿
        industrial_added_value = round(random.uniform(100000000, 10000000000), 2)
        service_added_value = round(industrial_added_value * random.uniform(1.2, 2), 2)  # 服务业增加值高于工业
        fixed_asset_investment = round(random.uniform(50000000, 5000000000), 2)  # 固定资产投资5000万-50亿
        retail_sales = round(random.uniform(80000000, 8000000000), 2)  # 社零总额8000万-80亿
        data_source = random.choice(["企业直报+部门推数", "抽样调查+统计推算", "全面调查"])
        audit_status = random.choices(["已通过", "待审核", "存疑"], weights=[8, 1, 1])[0]

        sql = """
              INSERT INTO stddb_region_gdp
              (region_code, reporting_month, industrial_added_value, service_added_value, fixed_asset_investment, \
               retail_sales, data_source, audit_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (region_code, reporting_month, industrial_added_value, service_added_value,
                             fixed_asset_investment, retail_sales, data_source, audit_status))
    conn.commit()
    print("stddb_region_gdp 数据生成完成（200行）")

    # -------------------------- 5.4 stddb_enterprise_employees（500行，从业人员） --------------------------
    for _ in range(500):
        stat_id = None
        company_credit_code = random.choice(enterprise_codes)
        reporting_month_date = generate_date_between(start="-24m", end=datetime.now().date())
        reporting_month = generate_char6_date(reporting_month_date)
        total_employees = random.randint(1, 200)  # 总从业人员1-200人
        full_time_employees = round(total_employees * random.uniform(0.7, 1), 0)  # 正式工70%-100%
        temporary_employees = total_employees - full_time_employees  # 临时工=总人数-正式工
        avg_salary = round(random.uniform(5000, 20000), 2)  # 平均工资5000-20000
        stat_status = random.choice(["已确认", "待确认"])

        sql = """
              INSERT INTO stddb_enterprise_employees
              (company_credit_code, reporting_month, total_employees, full_time_employees, temporary_employees, \
               avg_salary, stat_status)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (company_credit_code, reporting_month, total_employees, full_time_employees, temporary_employees,
                        avg_salary, stat_status))
    conn.commit()
    print("stddb_enterprise_employees 数据生成完成（500行）")

    # -------------------------- 5.5 stddb_investment_project（300行，投资项目） --------------------------
    for _ in range(300):
        project_id = None
        project_name = random.choice([
            "XX产业园建设项目", "XX厂房扩建项目", "XX道路改造项目",
            "XX污水处理项目", "XX商业综合体项目"
        ])
        builder_credit_code = random.choice(enterprise_codes)
        planned_investment = round(random.uniform(10000000, 1000000000), 2)  # 计划投资1000万-10亿
        actual_investment = round(planned_investment * random.uniform(0.3, 1.1), 2)  # 实际投资30%-110%
        start_date = generate_date_between(start="-5y", end=datetime.now().date() - timedelta(days=30))
        project_status = random.choices(["在建", "已完工", "停工"], weights=[6, 3, 1])[0]
        investment_sector = random.choice(["工业制造", "基础设施", "房地产", "生态环保", "社会事业"])

        sql = """
              INSERT INTO stddb_investment_project
              (project_name, builder_credit_code, planned_investment, actual_investment, start_date, project_status, \
               investment_sector)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql, (project_name, builder_credit_code, planned_investment, actual_investment, start_date,
                             project_status, investment_sector))
    conn.commit()
    print("stddb_investment_project 数据生成完成（300行）")

    # -------------------------- 5.6 stddb_abnormal_data（200行，统计异常） --------------------------
    for _ in range(200):
        anomaly_id = None
        data_type = random.choice(["营收", "产值", "GDP", "从业人员", "投资"])
        if data_type in ["营收", "产值", "从业人员", "投资"]:
            ref_id = random.choice(enterprise_codes)
        else:
            ref_id = random.choice(region_codes)
        # 异常原因：贴合业务冲突
        anomaly_reason = random.choice([
            "统计营收高于税务营收20%", "工业产值与发票金额不匹配", "区域GDP超企业汇总15%",
            "从业人员数与社保参保人数差异50%", "实际投资无进项税额抵扣"
        ])
        discovery_date = generate_date_between(start="-1y", end=datetime.now().date())
        rectification_status = random.choices(["已整改", "待整改", "无法整改"], weights=[5, 3, 2])[0]
        rectification_measures = "重新申报数据并核实" if rectification_status == "已整改" else None
        inspector = fake.name()

        sql = """
              INSERT INTO stddb_abnormal_data
              (ref_id, data_type, anomaly_reason, discovery_date, rectification_status, rectification_measures, \
               inspector)
              VALUES (%s, %s, %s, %s, %s, %s, %s) \
              """
        cursor.execute(sql,
                       (ref_id, data_type, anomaly_reason, discovery_date, rectification_status, rectification_measures,
                        inspector))
    conn.commit()
    print("stddb_abnormal_data 数据生成完成（200行）")

    cursor.close()
    conn.close()


# -------------------------- 主函数：执行全量数据生成 --------------------------
if __name__ == "__main__":
    # 需确保5个数据库已提前创建（文档中CREATE DATABASE语句）
    print("开始生成SBDB（社保监管数据库）数据...")
    generate_sbdb_data()

    print("\n开始生成TAXDB（税务监管数据库）数据...")
    generate_taxdb_data()

    print("\n开始生成MTDB（市场监督管理数据库）数据...")
    generate_mtdb_data()

    print("\n开始生成CABDB（民政补贴发放数据库）数据...")
    generate_cabdb_data()

    print("\n开始生成STDDB（统计数据申报数据库）数据...")
    generate_stddb_data()

    print("\n所有数据库表的模拟数据生成完成！")