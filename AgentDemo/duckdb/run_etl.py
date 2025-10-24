# --- 第1部分：导入必要的库 ---

# 导入 pandas 库，它主要用来处理数据，我们将用它来读取和写入数据库
# 'pd' 是 pandas 的标准简写，后面我们都用 pd 来调用它
import pandas as pd

# 导入 duckdb 库，这是一个高性能的分析数据库，我们将用它来处理 Pandas DataFrame
import duckdb

# 导入 sqlalchemy 库中的 create_engine 函数
# SQLAlchemy 是一个数据库工具包，Pandas 使用它来与 PostgreSQL 和 MySQL "对话"
# create_engine 的作用是建立一个连接“引擎”（或连接池）
from sqlalchemy import create_engine

# 导入 sys 库，它允许我们与 Python 解释器交互
# 我们将用它来在出错时打印更清晰的错误信息
import sys


# --- 第2部分：定义主函数 ---

# 定义一个名为 'main' 的主函数
# 把所有代码放进一个函数里是一个好习惯，这让代码更整洁
def main():
    print("--- ETL 流程开始 ---")

    # 'try...except' 是一个错误处理结构
    # Python 会尝试执行 'try' 块里的所有代码
    try:
        # --- 3. 建立数据库连接 ---

        # === PostgreSQL (我们的数据源) ===
        # 建立一个 PostgreSQL 连接字符串
        # 格式: '数据库类型+驱动://用户名:密码@主机地址:端口号/数据库名'
        pg_conn_str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/test'

        # 使用 SQLAlchemy 的 create_engine 函数，根据连接字符串创建一个连接引擎
        # 'pg_engine' 就是我们通向 PostgreSQL 数据库的“管道”
        pg_engine = create_engine(pg_conn_str)
        print("PostgreSQL 连接引擎创建成功！")

        # === MySQL (我们的目标) ===
        # 建立一个 MySQL 连接字符串
        # 注意驱动变成了 'mysql+mysqlconnector'
        mysql_db = 'test'
        mysql_conn_str = f'mysql+mysqlconnector://root:root@localhost:3306/{mysql_db}'

        # 为 MySQL 创建连接引擎
        # 'mysql_engine' 是我们通向 MySQL 数据库的“管道”
        mysql_engine = create_engine(mysql_conn_str)
        print("MySQL 连接引擎创建成功！")

        # --- 4. 提取 (Extract) ---

        # 定义我们要从 PostgreSQL 中查询数据的 SQL 语句
        sql_query = "SELECT * FROM sales_data"
        print(f"\n[步骤 1/3] 正在从 PostgreSQL 提取数据...")

        # 这是关键一步：使用 Pandas 的 read_sql 函数
        # 它会使用 'pg_engine'（我们的管道）去执行 'sql_query'（我们的命令）
        # 然后把所有查询结果自动打包成一个 Pandas DataFrame（一种内存中的表格）
        # 我们把这个内存中的表格命名为 'df_raw' (raw = 原始的)
        df_raw = pd.read_sql(sql_query, pg_engine)

        # 检查一下我们是否真的拿到了数据
        if df_raw.empty:
            print("警告: 未从 PostgreSQL 中读取到数据。程序终止。")
            return  # 如果没数据，就提前结束函数

        print(f"成功 [提取] {len(df_raw)} 行原始数据到 Pandas。")
        print("--- 原始数据 (前5行) ---")
        # .head() 会显示 DataFrame 的前5行，让我们能快速预览一下数据
        print(df_raw.head())

        # --- 5. 转换 (Transform) ---

        print("\n[步骤 2/3] 开始使用 DuckDB 进行内存中 [转换]...")

        # 这是你学习这个技术栈的“核心”
        # 我们要编写一个 SQL 查询来分析数据
        # 这个查询将按产品ID(product_id)和月份(sales_month)分组
        # 并计算总收入(total_revenue)、总销量(total_quantity)等
        # 我们还过滤掉非 'completed' 状态的订单
        duckdb_sql = """
        SELECT
            product_id,
            strftime(order_date, '%Y-%m') AS sales_month, -- strftime 是一个格式化日期的函数
            SUM(quantity * price) AS total_revenue,      -- 计算总收入
            SUM(quantity) AS total_quantity,
            COUNT(order_id) AS completed_orders_count
        FROM
            df_raw  -- 魔法发生的地方：DuckDB 可以直接查询我们内存中的 'df_raw' 变量！
        WHERE
            status = 'completed' -- 只统计 'completed' 状态的订单
        GROUP BY
            product_id, sales_month -- 按产品和月份聚合
        ORDER BY
            sales_month DESC, total_revenue DESC -- 按月份和收入排序
        """

        # 执行 DuckDB 查询
        # duckdb.sql(duckdb_sql) 会执行查询
        # .to_df() 会把 DuckDB 的查询结果“转换回”一个新的 Pandas DataFrame
        # 我们把这个处理过的、干净的 DataFrame 命名为 'df_processed'
        df_processed = duckdb.sql(duckdb_sql).to_df()

        print(f"DuckDB [转换] 完成。生成了 {len(df_processed)} 行聚合结果。")
        print("--- 处理后数据 (前5行) ---")
        print(df_processed.head())

        # --- 6. 加载 (Load) ---

        print("\n[步骤 3/3] 正在 [加载] 处理结果到 MySQL...")

        # 给我们在 MySQL 中要创建的表起个名字
        target_table_name = 'product_monthly_summary'

        # 这是最后一步：使用 Pandas 的 to_sql 函数
        # 它会把 'df_processed' (我们处理好的 DataFrame) 写入到 MySQL
        df_processed.to_sql(
            name=target_table_name,  # 1. 写入 MySQL 时的表名
            con=mysql_engine,  # 2. 使用我们之前创建的 MySQL 引擎（管道）
            if_exists='replace',  # 3. 如果表已存在：'replace'=删除旧表,重建新表
            #    (其他选项: 'append'=追加, 'fail'=报错)
            index=False  # 4. 非常重要：不要把 Pandas 的行索引(0,1,2...)写成一列
        )

        print(f"\n--- ETL 流程成功 ---")
        print(f"数据已加载到 MySQL 数据库 '{mysql_db}' 的 '{target_table_name}' 表中。")

    # 'except' 块：如果 'try' 块中的任何代码失败（比如密码错误、SQL语法错）
    # Python 会立即跳到这里
    except Exception as e:
        print(f"\n--- ETL 流程失败 ---", file=sys.stderr)
        # 打印详细的错误信息 'e' 到标准错误流 (stderr)
        print(f"错误详情: {e}", file=sys.stderr)

        # 提供一些常见的错误提示
        if "Access denied" in str(e):
            print("提示：请检查你的 MySQL/PostgreSQL 用户名和密码。", file=sys.stderr)
        if "could not connect" in str(e) or "failed" in str(e):
            print("提示：请检查你的数据库主机、端口以及服务是否正在运行。", file=sys.stderr)


# --- 第7部分：运行脚本 ---

# 这是 Python 脚本的标准“入口点”
# 当你直接运行这个 .py 文件时 (而不是导入它时)
# 下面的代码块才会被执行
if __name__ == "__main__":
    main()  # 调用我们上面定义的 'main' 函数