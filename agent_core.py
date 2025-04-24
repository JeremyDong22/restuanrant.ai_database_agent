import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from datetime import datetime, timedelta

# 初始化数据库（固定）
db = SQLDatabase.from_uri(os.getenv("SUPABASE_DB_URI"))

# Store conversation memories with session IDs
# The structure is: {session_id: {'memory': memory_object, 'last_access': timestamp}}
conversation_memories = {}

# Time-to-live for each memory object (in seconds)
MEMORY_TTL = 3600  # 1 hour

# Prompt
react_prompt_str_with_history = """
Answer the following questions as best you can, do not make up any information. 
**Your final answer must always be in Chinese.** 
You have access to the following tools:
{tools}

背景知识：关于Jeremy的数据库
你将要交互的 Supabase (PostgreSQL) 数据库主要包含了从大众点评每个城市主榜单中爬取的Top30家餐饮店铺，以及榜单（也叫菜系）中的Top10家店铺，并从小红书爬取这些店铺的笔记。关键表包括：
- `posts`: 存储小红书帖子的详细信息，包括note_id，likes（点赞数），title（帖子标题），author（作者），publish_date（发布日期），content（正文内容），collections（收藏），comments（评论），images（图片）。
- `dzdpdata`: 存储了大众点评每个城市餐厅的详细信息，包括榜单（一般以菜系或者食物种类命名），店铺名称（全称），品牌（人们通常怎么叫这个餐厅，一般用这个称呼），城市，排名（同一家餐厅会根据不同日期和榜单而变动），create_date（创建日期），评分，comments，价格，位置（区或街道）
- `brand`: 存储了帖子中提及的品牌信息。
- 'brand_posts': 存储了品牌和帖子之间的关系。

1.  首先调用tools获取数据库schema，并结合背景知识判断用户问题是否与Jeremy的数据库schema相关。如果不相关，请直接返回 "Final Answer" 中给出自然、友好的中文回应。
2.  如果与Jeremy的数据库相关：
    a.  结合Jeremy数据库背景知识，进一步询问用户需要查询细节，必要时把数据库的column展示给用户。
    b.  如果用户已经提供了足够的信息，则判断自己是否能完成任务，比如你不能用语义分析，但是你能列举小红书帖子内容和图片。
    c.  你可以提供图片的url，就在posts表的images字段中。如果你要把图片返回给用户，请把每个 url 写成 Markdown 图片语法`![图{{i}}]({{url}})`，一行一张，不要输出 Python 列表或引号。
    d.  如果你上一轮的 Final Answer 是要求补齐问题，而用户的当前输入 (Question:) 看起来是在回答你的问题，请结合用户的回答，继续尝试完成用户最初的请求，而不是重复提问澄清问题！例如，如果你问了"您想查询哪个城市？"，用户回答"北京"，那么你的下一步应该是去查询北京的数据。


Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do, follow the IMPORTANT INSTRUCTIONS above. Identify the user's intent first.
Action: the action to take, should be one of [{tool_names}]. If you are just chatting or asking a clarifying question based on the instructions, the action should be 'Final Answer' directly, and you put your chat response or clarifying question in the Final Answer section.
Action Input: the input to the action. If the action is 'Final Answer', this is not needed.
Observation: the result of the action. This is only present if an action other than 'Final Answer' was taken.
... (this Thought/Action/Action Input/Observation can repeat N times if using tools)
Thought: I now know the final answer or the question I need to ask for clarification.
Final Answer: (The final answer to the original input question in Chinese, OR a clarifying question in Chinese if information was insufficient for a database query based on the instructions)

Begin! Remember to consider the previous conversation history if relevant and follow the IMPORTANT INSTRUCTIONS above.

Previous conversation history:
{chat_history}

Question: {input}
Thought:{agent_scratchpad}
"""


# Function to clean up old memories
def cleanup_old_memories():
    """Remove memory objects that haven't been accessed in a while"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in conversation_memories.items():
        last_access = session_data.get('last_access')
        if current_time - last_access > timedelta(seconds=MEMORY_TTL):
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_memories[session_id]

# --- 运行 Agent 的主函数 ---
def run_agent_with_key(user_input: str, google_api_key: str, session_id: str = None) -> str:
    try:
        # Clean up old memories periodically
        cleanup_old_memories()
        
        # 1. 创建 LLM
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash-lite",
            google_api_key=google_api_key
        )

        # 2. 工具加载
        tools_basic = load_tools(["llm-math"], llm=llm)
        sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = tools_basic + sql_toolkit.get_tools()

        # 3. Get or create memory for this session
        if session_id and session_id in conversation_memories:
            # Use existing memory
            memory = conversation_memories[session_id]['memory']
            # Update last access time
            conversation_memories[session_id]['last_access'] = datetime.now()
        else:
            # Create new memory
            memory = ConversationBufferWindowMemory(k=7, memory_key="chat_history", return_messages=False)
            if session_id:
                conversation_memories[session_id] = {
                    'memory': memory,
                    'last_access': datetime.now()
                }

        # 4. Prompt 初始化
        prompt = PromptTemplate(
            template=react_prompt_str_with_history,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "chat_history"]
        )

        # 5. Agent & 执行器
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True
        )

        # 6. 执行请求
        result = agent_executor.invoke({"input": user_input})
        return result['output']

    except Exception as e:
        return f"❌ 出错了：{e}"