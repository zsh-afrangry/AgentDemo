# import os
# import json
# import dashscope
# from dashscope import Generation
# from http import HTTPStatus
# from dotenv import load_dotenv
# import time
# import uvicorn
# from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import traceback
# from typing import List, Optional
#
# # --- 常量定义 ---
# EXAMPLE_FILE_PREFIX = "examples_"
# OUTPUT_FILENAME_PREFIX = "generated_"
# OUTPUT_FILENAME_SUFFIX = "_questions.json"
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#
# # --- 初始化 FastAPI 应用 ---
# app = FastAPI(
#     title="智能审计问题生成器 API",
#     description="接收 SQL Schema 文件，按需调用 5 个专业 AI 智能体进行分析的后端服务。",
#     version="1.1.0"
# )
#
# # --- CORS ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 开发期放开；生产请按需收紧
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
#
# # --- 工具函数 ---
# def load_local_file_content(filename: str) -> Optional[str]:
#     path = os.path.join(BASE_DIR, filename)
#     try:
#         with open(path, 'r', encoding='utf-8') as f:
#             return f.read()
#     except FileNotFoundError:
#         print(f"[文件缺失] {path}")
#         return None
#     except Exception as e:
#         print(f"[读取异常] {path}: {e}")
#         return None
#
#
# def get_specialized_prompt(conflict_type: str, schema_sql: str, examples_text: str) -> str:
#     """根据冲突类型生成专属的提示词。"""
#
#     agent_definitions = {
#         "binary": {
#             "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【状态矛盾 (Binary Contradiction)】。",
#             "task": "你的任务是**仔细学习**【状态矛盾参考范例】，理解它们是如何通过对比不同表中的状态字段来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于状态的描述），**仅查找并报告**所有潜在的【状态矛盾】问题。\n**请忽略所有其他类型的问题**。",
#             "example_file_suffix": "binary.txt"
#         },
#         "process": {
#             "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【流程/资格矛盾 (Process/Eligibility Conflict)】。",
#             "task": "你的任务是**仔细学习**【流程/资格矛盾参考范例】，理解它们是如何检查必要步骤或资质是否满足的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于流程、资格和条件的描述），**仅查找并报告**所有潜在的【流程或资格矛盾】问题。\n**请忽略所有其他类型的问题**。",
#             "example_file_suffix": "process.txt"
#         },
#         "quantitative": {
#             "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【数值/会计不一致 (Quantitative Conflict)】。",
#             "task": "你的任务是**仔细学习**【数值/会计不一致参考范例】，理解它们是如何通过比较不同表中的数值字段（如金额、数量、基数）来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于数值计算、阈值和对比逻辑的描述），**仅查找并报告**所有潜在的【数值或会计不一致】问题。\n**请忽略所有其他类型的问题**。",
#             "example_file_suffix": "quantitative.txt"
#         },
#         "temporal": {
#             "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【时间/因果矛盾 (Temporal/Causal Conflict)】。",
#             "task": "你的任务是**仔细学习**【时间/因果矛盾参考范例】，理解它们是如何通过检查不同事件的日期字段来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于日期、有效期和先后顺序的描述），**仅查找并报告**所有潜在的【时间或因果矛盾】问题。\n**请忽略所有其他类型的问题**。",
#             "example_file_suffix": "temporal.txt"
#         },
#         "aggregate": {
#             "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【聚合/网络异常 (Aggregate/Network Conflict)】。",
#             "task": "你的任务是**仔细学习**【聚合/网络异常参考范例】，理解它们是如何通过分组、计数、求和等聚合操作来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于聚合逻辑、阈值和宏观对比的描述），**仅查找并报告**所有潜在的【聚合或网络异常】问题。\n**请忽略所有其他类型的问题**。",
#             "example_file_suffix": "aggregate.txt"
#         }
#     }
#     definition = agent_definitions.get(conflict_type)
#     if not definition:
#         raise ValueError(f"未知的冲突类型: {conflict_type}")
#
#     example_filename = f"{EXAMPLE_FILE_PREFIX}{definition['example_file_suffix']}"
#
#     meta_prompt = f"""
#     ### 角色
#     {definition['role']}
#
#     ### 任务
#     {definition['task']}
#
#     ---
#     ### 输入一: AI需要学习的“{conflict_type}类型参考范例”
#     (内容来自服务器本地的 {example_filename})
#     {examples_text}
#     ---
#     ### 输入二: AI可以使用的“数据库 Schema” (包含详细注释)
#     (内容来自用户上传的 SQL 文件)
#     {schema_sql}
#     ---
#
#     ### 输出要求
#     请根据以上【Schema】，**举一反三**，生成一个包含 5-10 个 **与你专业领域相关的、新的、具体的** 核查问题的 JSON 列表。
#     -   **专注领域**: 严格只输出属于你专业领域 ({conflict_type}) 的问题。
#     -   **利用注释**: 你必须充分利用 Schema 中 `COMMENT` 里的业务逻辑和冲突提示。
#     -   **不要重复**: 不要简单重复【参考范例】中已有的问题。
#
#     -   **!!! 核心格式要求**: 必须严格返回一个 JSON 列表。列表中的每个元素**必须**是遵循以下 8 个字段结构的 JSON 对象：
#
#     1.  `"id"`: (Number) 从1开始的连续整数序号。
#     2.  `"title"`: (String) 简洁、易读的核查项标题。
#         * 示例: "在营个体户申领城乡低保"
#     3.  `"logic_description"`: (String) 详细的、人类可读的冲突逻辑描述，必须明确指出涉及的数据库名和表名。
#         * 示例: "检查 CABDB.cabdb_subsistence_benefit 中申领低保的个人，其 id_card 是否在 MTDB.mtdb_individual_reg 中作为 operator_id_card 存在，且 business_status = '在营'。"
#     4.  `"conflict_type"`: (String) 问题的冲突类型。**必须**固定为："{conflict_type}"
#     5.  `"related_entities"`: (Object) 涉及的实体，包含两个键：
#         * `"primary_table"`: (String) 审计线索的“起点”或“主体”所在的表。
#         * `"secondary_tables"`: (Array<String>) 用于交叉验证或关联查询的表。
#         * 示例: {{"primary_table": "CABDB.cabdb_subsistence_benefit", "secondary_tables": ["MTDB.mtdb_individual_reg"]}}
#     6.  `"key_fields"`: (Array<String>) 实现该逻辑所必须依赖的关键字段列表（必须包含表名）。
#         * 示例: ["CABDB.cabdb_subsistence_benefit.id_card", "MTDB.mtdb_individual_reg.operator_id_card", "MTDB.mtdb_individual_reg.business_status"]
#     7.  `"explanation_hint"`: (String) 解释为什么这是一个潜在的问题或风险点。
#         * 示例: "该核查项用于发现以‘在营’状态（作为个体户经营者）同时享受低保待遇的状态矛盾。"
#     8.  `"next_action_hint"`: (String) 为审计人员提供一个具体的下一步人工复核行动建议。
#         * 示例: "建议导出可疑人员名单，核实其低保资格与工商登记状态的真实性。"
#     """
#     return meta_prompt
#
#
# # --- AI 调用函数  ---
# def call_qwen_agent(prompt: str, api_key: str, agent_type: str) -> Optional[str]:
#     dashscope.api_key = api_key
#     print(f"\n>>> 调用 {agent_type} 智能体 (qwen-plus)")
#     try:
#         response = Generation.call(model="qwen-plus", prompt=prompt, result_format="text")
#         time.sleep(1)
#         if response.status_code == HTTPStatus.OK:
#             ai_response_text = response.output.text
#             clean_json = ai_response_text.strip().lstrip("```json").rstrip("```")
#             return clean_json
#         else:
#             print(f"[失败] {agent_type} code={response.code} msg={response.message}")
#             return None
#     except Exception as e:
#         print(f"[异常] {agent_type}: {e}")
#         print(traceback.format_exc())
#         return None
#
#
# # --- 工具函数  ---
# ALLOWED_AGENTS = {"binary", "process", "quantitative", "temporal", "aggregate"}
#
#
# def parse_agents(raw: Optional[str]) -> List[str]:
#     """
#     允许两种传法：
#     1) 逗号分隔字符串：'binary,process'
#     2) JSON 数组字符串：'["binary","process"]'
#     """
#     if not raw:
#         return []
#     raw = raw.strip()
#     try:
#         maybe_list = json.loads(raw)
#         if isinstance(maybe_list, list):
#             agents = [str(x).strip() for x in maybe_list]
#         else:
#             agents = [x.strip() for x in str(raw).split(",")]
#     except Exception:
#         agents = [x.strip() for x in raw.split(",")]
#     # 去重 + 只保留允许值
#     agents = [a for a in dict.fromkeys(agents) if a in ALLOWED_AGENTS]
#     return agents
#
#
# # --- API 端点  ---
# @app.post("/analyze/", tags=["分析接口"], summary="上传 Schema 并选择要运行的智能体")
# async def analyze_schema(
#         schema_file: UploadFile = File(..., description="SQL Schema 文件"),
#         agents: Optional[str] = Form(None,
#                                      description="要运行的智能体，逗号分隔或JSON数组，如 'binary,process' 或 '[\"binary\",\"process\"]'")
# ):
#     print(f"--- 收到文件: {schema_file.filename} ---")
#     try:
#         schema_sql = (await schema_file.read()).decode("utf-8")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"无法读取 Schema: {e}")
#     finally:
#         await schema_file.close()
#
#     # 读取 API Key
#     load_dotenv()
#     MY_API_KEY = os.getenv("DASHSCOPE_API_KEY")
#     if not MY_API_KEY or "REPLACE_ME" in str(MY_API_KEY):
#         raise HTTPException(status_code=500, detail="服务器端 API Key 未正确配置。")
#
#     # 解析前端选择
#     agent_types_to_run = parse_agents(agents)
#     if not agent_types_to_run:
#         raise HTTPException(status_code=400,
#                             detail="请至少选择一个要运行的智能体（binary/process/quantitative/temporal/aggregate）。")
#
#     print(f">>> 将运行的智能体: {agent_types_to_run}")
#
#     # 运行并聚合结果
#     results_summary = {}
#     for agent_type in agent_types_to_run:
#         print("\n" + "-" * 16 + f" {agent_type} " + "-" * 16)
#         example_suffix_map = {
#             "binary": "binary.txt",
#             "process": "process.txt",
#             "quantitative": "quantitative.txt",
#             "temporal": "temporal.txt",
#             "aggregate": "aggregate.txt",
#         }
#         example_filename = f"{EXAMPLE_FILE_PREFIX}{example_suffix_map[agent_type]}"
#         examples = load_local_file_content(example_filename)
#         if examples is None:
#             results_summary[agent_type] = {"status": "failed", "error": f"服务器端范例 '{example_filename}' 未找到",
#                                            "questions": []}
#             continue
#
#         prompt = get_specialized_prompt(agent_type, schema_sql, examples)
#         raw_json = call_qwen_agent(prompt, MY_API_KEY, agent_type)
#
#         if raw_json:
#             try:
#                 parsed = json.loads(raw_json)
#                 if isinstance(parsed, list):
#                     print(f">>> {agent_type} 智能体分析完成！生成了 {len(parsed)} 个结构化问题。")
#                     results_summary[agent_type] = {"status": "success", "questions": parsed}
#                 else:
#                     raise json.JSONDecodeError("返回的不是 JSON 列表", raw_json, 0)
#             except json.JSONDecodeError as je:
#                 print(f"[警告] {agent_type} 智能体返回的不是标准 JSON 列表格式。")
#                 print(f"错误详情: {je}")
#                 print(f"原始输出: {raw_json}")
#                 results_summary[agent_type] = {
#                     "status": "failed",
#                     "error": f"AI 返回无效 JSON: {je}",
#                     "raw_output": raw_json,
#                     "questions": []
#                 }
#         else:
#             results_summary[agent_type] = {"status": "failed", "error": "AI API 调用失败或返回空", "questions": []}
#
#     failed = [k for k, v in results_summary.items() if v.get("status") != "success"]
#     msg = "分析完成。" + (f" 以下智能体失败：{', '.join(failed)}" if failed else "")
#
#     print("\n" + "=" * 50 + "\n所有智能体运行完毕。结果将直接返回给前端。\n" + "=" * 50)
#
#     return {"message": msg, "results_by_agent": results_summary}
#
#
# # --- 根路由  ---
# @app.get("/")
# async def read_root():
#     return {"message": "智能审计后端 API 正在运行。访问 /docs 查看 API 文档。"}
#
# # --- 启动命令  ---
# # --- uvicorn main:app --reload  ---
# # if __name__ == "__main__":
# #     uvicorn.run(app, host="127.0.0.1", port=8000)

# 并行
import os
import json
import dashscope
from dashscope import Generation
from http import HTTPStatus
from dotenv import load_dotenv
import time  # 需要 time 模块
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback
from typing import List, Optional
import asyncio

# --- 常量定义 ---
EXAMPLE_FILE_PREFIX = "examples_"
OUTPUT_FILENAME_PREFIX = "generated_"
OUTPUT_FILENAME_SUFFIX = "_questions.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 初始化 FastAPI 应用 ---
app = FastAPI(
    title="智能审计问题生成器 API",
    description="接收 SQL Schema 文件，按需调用 5 个专业 AI 智能体进行分析的后端服务。",
    version="1.1.0"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 工具函数 ---
def load_local_file_content(filename: str) -> Optional[str]:
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[文件缺失] {path}")
        return None
    except Exception as e:
        print(f"[读取异常] {path}: {e}")
        return None


# --- Prompt 生成函数  ---
def get_specialized_prompt(conflict_type: str, schema_sql: str, examples_text: str) -> str:

    agent_definitions = {
        "binary": {
            "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【状态矛盾 (Binary Contradiction)】。",
            "task": "你的任务是**仔细学习**【状态矛盾参考范例】，理解它们是如何通过对比不同表中的状态字段来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于状态的描述），**仅查找并报告**所有潜在的【状态矛盾】问题。\n**请忽略所有其他类型的问题**。",
            "example_file_suffix": "binary.txt"
        },
        "process": {
            "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【流程/资格矛盾 (Process/Eligibility Conflict)】。",
            "task": "你的任务是**仔细学习**【流程/资格矛盾参考范例】，理解它们是如何检查必要步骤或资质是否满足的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于流程、资格和条件的描述），**仅查找并报告**所有潜在的【流程或资格矛盾】问题。\n**请忽略所有其他类型的问题**。",
            "example_file_suffix": "process.txt"
        },
        "quantitative": {
            "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【数值/会计不一致 (Quantitative Conflict)】。",
            "task": "你的任务是**仔细学习**【数值/会计不一致参考范例】，理解它们是如何通过比较不同表中的数值字段（如金额、数量、基数）来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于数值计算、阈值和对比逻辑的描述），**仅查找并报告**所有潜在的【数值或会计不一致】问题。\n**请忽略所有其他类型的问题**。",
            "example_file_suffix": "quantitative.txt"
        },
        "temporal": {
            "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【时间/因果矛盾 (Temporal/Causal Conflict)】。",
            "task": "你的任务是**仔细学习**【时间/因果矛盾参考范例】，理解它们是如何通过检查不同事件的日期字段来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于日期、有效期和先后顺序的描述），**仅查找并报告**所有潜在的【时间或因果矛盾】问题。\n**请忽略所有其他类型的问题**。",
            "example_file_suffix": "temporal.txt"
        },
        "aggregate": {
            "role": "你是一名高度专业的数据审计专家，你的**唯一专长**是识别【聚合/网络异常 (Aggregate/Network Conflict)】。",
            "task": "你的任务是**仔细学习**【聚合/网络异常参考范例】，理解它们是如何通过分组、计数、求和等聚合操作来发现问题的。\n然后，请你深入分析【数据库 Schema】（特别注意 `COMMENT` 中关于聚合逻辑、阈值和宏观对比的描述），**仅查找并报告**所有潜在的【聚合或网络异常】问题。\n**请忽略所有其他类型的问题**。",
            "example_file_suffix": "aggregate.txt"
        }
    }
    definition = agent_definitions.get(conflict_type)
    if not definition:
        raise ValueError(f"未知的冲突类型: {conflict_type}")

    example_filename = f"{EXAMPLE_FILE_PREFIX}{definition['example_file_suffix']}"

    meta_prompt = f"""
    ### 角色
    {definition['role']}

    ### 任务
    {definition['task']}

    ---
    ### 输入一: AI需要学习的“{conflict_type}类型参考范例”
    (内容来自服务器本地的 {example_filename})
    {examples_text}
    ---
    ### 输入二: AI可以使用的“数据库 Schema” (包含详细注释)
    (内容来自用户上传的 SQL 文件)
    {schema_sql}
    ---

    ### 输出要求
    请根据以上【Schema】，**举一反三**，生成一个包含 5-10 个 **与你专业领域相关的、新的、具体的** 核查问题的 JSON 列表。
    -   **专注领域**: 严格只输出属于你专业领域 ({conflict_type}) 的问题。
    -   **利用注释**: 你必须充分利用 Schema 中 `COMMENT` 里的业务逻辑和冲突提示。
    -   **不要重复**: 不要简单重复【参考范例】中已有的问题。

    -   **!!! 核心格式要求**: 必须严格返回一个 JSON 列表。列表中的每个元素**必须**是遵循以下 8 个字段结构的 JSON 对象：

    1.  `"id"`: (Number) 从1开始的连续整数序号。
    2.  `"title"`: (String) 简洁、易读的核查项标题。
        * 示例: "在营个体户申领城乡低保"
    3.  `"logic_description"`: (String) 详细的、人类可读的冲突逻辑描述，必须明确指出涉及的数据库名和表名。
        * 示例: "检查 CABDB.cabdb_subsistence_benefit 中申领低保的个人，其 id_card 是否在 MTDB.mtdb_individual_reg 中作为 operator_id_card 存在，且 business_status = '在营'。"
    4.  `"conflict_type"`: (String) 问题的冲突类型。**必须**固定为："{conflict_type}"
    5.  `"related_entities"`: (Object) 涉及的实体，包含两个键：
        * `"primary_table"`: (String) 审计线索的“起点”或“主体”所在的表。
        * `"secondary_tables"`: (Array<String>) 用于交叉验证或关联查询的表。
        * 示例: {{"primary_table": "CABDB.cabdb_subsistence_benefit", "secondary_tables": ["MTDB.mtdb_individual_reg"]}}
    6.  `"key_fields"`: (Array<String>) 实现该逻辑所必须依赖的关键字段列表（必须包含表名）。
        * 示例: ["CABDB.cabdb_subsistence_benefit.id_card", "MTDB.mtdb_individual_reg.operator_id_card", "MTDB.mtdb_individual_reg.business_status"]
    7.  `"explanation_hint"`: (String) 解释为什么这是一个潜在的问题或风险点。
        * 示例: "该核查项用于发现以‘在营’状态（作为个体户经营者）同时享受低保待遇的状态矛盾。"
    8.  `"next_action_hint"`: (String) 为审计人员提供一个具体的下一步人工复核行动建议。
        * 示例: "建议导出可疑人员名单，核实其低保资格与工商登记状态的真实性。"
    """
    return meta_prompt


async def call_qwen_agent_async(prompt: str, api_key: str, agent_type: str) -> Optional[str]:
    """
    [异步] 调用千问大模型
    通过 asyncio.to_thread 在单独的线程中运行同步的 SDK 调用
    """
    print(f"\n>>> [ASYNC THREAD] 开始准备 {agent_type} 智能体 (qwen-plus)")

    # 定义将在单独线程中运行的同步函数
    def sync_blocking_call():
        nonlocal api_key, prompt, agent_type  # 确保能访问外部变量
        try:
            # 在线程内设置 API Key
            dashscope.api_key = api_key
            print(f">>> [THREAD] 正在调用 {agent_type} ...")
            # --- 使用正确的、同步的 call 方法 ---
            response = Generation.call(
                model="qwen-plus",
                prompt=prompt,
                result_format="text"
            )
            # 在线程内短暂 sleep
            time.sleep(1)
            return response
        except Exception as thread_e:
            print(f"[线程内异常] {agent_type}: {thread_e}")
            print(traceback.format_exc())
            return None  # 返回 None 表示线程内发生错误

    try:
        # 使用 asyncio.to_thread 运行同步函数
        response = await asyncio.to_thread(sync_blocking_call)

        # 处理线程返回的结果
        if response and response.status_code == HTTPStatus.OK:
            ai_response_text = response.output.text
            clean_json = ai_response_text.strip().lstrip("```json").rstrip("```")
            print(f">>> [ASYNC THREAD] {agent_type} 调用成功")
            return clean_json
        elif response:  # API 返回了错误状态码
            print(f"[API失败] {agent_type} code={response.code} msg={response.message}")
            return None
        else:  # 线程内发生异常 (sync_blocking_call 返回了 None)
            print(f"[线程失败] {agent_type} 调用在线程中遇到异常")
            return None

    except Exception as e:
        # 捕获 asyncio.to_thread 本身可能抛出的异常
        print(f"[ASYNC 异常] {agent_type}: {e}")
        print(traceback.format_exc())
        return None


# --- 工具函数  ---
ALLOWED_AGENTS = {"binary", "process", "quantitative", "temporal", "aggregate"}


def parse_agents(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    raw = raw.strip()
    try:
        maybe_list = json.loads(raw)
        if isinstance(maybe_list, list):
            agents = [str(x).strip() for x in maybe_list]
        else:
            agents = [x.strip() for x in str(raw).split(",")]
    except Exception:
        agents = [x.strip() for x in raw.split(",")]
    # 去重 + 只保留允许值
    agents = [a for a in dict.fromkeys(agents) if a in ALLOWED_AGENTS]
    return agents


# 3. 异步任务封装函数
async def run_agent_analysis(agent_type: str, schema_sql: str, api_key: str) -> (str, dict):
    print("\n" + "-" * 16 + f" 准备 {agent_type} 任务 " + "-" * 16)
    example_suffix_map = {
        "binary": "binary.txt",
        "process": "process.txt",
        "quantitative": "quantitative.txt",
        "temporal": "temporal.txt",
        "aggregate": "aggregate.txt",
    }
    example_filename = f"{EXAMPLE_FILE_PREFIX}{example_suffix_map[agent_type]}"

    # 1. 加载文件
    examples = load_local_file_content(example_filename)
    if examples is None:
        return (agent_type, {"status": "failed", "error": f"服务器端范例 '{example_filename}' 未找到", "questions": []})

    # 2. 准备 Prompt
    prompt = get_specialized_prompt(agent_type, schema_sql, examples)

    # 3. 调用 AI
    raw_json = await call_qwen_agent_async(prompt, api_key, agent_type)

    # 4. 解析结果
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                print(f">>> {agent_type} 任务分析完成！生成了 {len(parsed)} 个结构化问题。")
                return (agent_type, {"status": "success", "questions": parsed})
            else:
                raise json.JSONDecodeError("返回的不是 JSON 列表", raw_json, 0)
        except json.JSONDecodeError as je:
            print(f"[警告] {agent_type} 任务返回的不是标准 JSON 列表格式。")
            print(f"错误详情: {je}")
            print(f"原始输出: {raw_json}")
            return (agent_type, {
                "status": "failed",
                "error": f"AI 返回无效 JSON: {je}",
                "raw_output": raw_json,
                "questions": []
            })
    else:
        print(f"--- {agent_type} 任务分析失败 (API调用问题) ---")
        return (agent_type, {"status": "failed", "error": "AI API 调用失败或返回空", "questions": []})


#  4. API 端点
@app.post("/analyze/", tags=["分析接口"], summary="上传 Schema 并选择要运行的智能体")
async def analyze_schema(
        schema_file: UploadFile = File(..., description="SQL Schema 文件"),
        agents: Optional[str] = Form(None,
                                     description="要运行的智能体，逗号分隔或JSON数组，如 'binary,process' 或 '[\"binary\",\"process\"]'")
):
    print(f"--- 收到文件: {schema_file.filename} ---")
    try:
        schema_sql = (await schema_file.read()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法读取 Schema: {e}")
    finally:
        await schema_file.close()

    # 读取 API Key
    load_dotenv()
    MY_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    if not MY_API_KEY or "REPLACE_ME" in str(MY_API_KEY):
        raise HTTPException(status_code=500, detail="服务器端 API Key 未正确配置。")

    # 解析前端选择
    agent_types_to_run = parse_agents(agents)
    if not agent_types_to_run:
        raise HTTPException(status_code=400,
                            detail="请至少选择一个要运行的智能体（binary/process/quantitative/temporal/aggregate）。")

    print(f">>> 将运行的智能体: {agent_types_to_run}")

    # 1. 创建所有异步任务
    print(f">>> 准备并发执行 {len(agent_types_to_run)} 个智能体任务...")
    tasks = []
    for agent_type in agent_types_to_run:
        tasks.append(run_agent_analysis(agent_type, schema_sql, MY_API_KEY))

    # 2. 使用 asyncio.gather 并发运行所有任务
    all_results = await asyncio.gather(*tasks)

    # 3. 将结果列表转换回原来的字典结构
    results_summary = {agent_type: result for agent_type, result in all_results}

    failed = [k for k, v in results_summary.items() if v.get("status") != "success"]
    msg = "分析完成。" + (f" 以下智能体失败：{', '.join(failed)}" if failed else "")

    print("\n" + "=" * 50 + "\n所有智能体运行完毕。结果将直接返回给前端。\n" + "=" * 50)

    return {"message": msg, "results_by_agent": results_summary}


# --- 根路由  ---
@app.get("/")
async def read_root():
    return {"message": "智能审计后端 API 正在运行。访问 /docs 查看 API 文档。"}

# --- 启动命令  ---
# --- uvicorn main:app --reload  ---
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

