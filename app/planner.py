from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.models import ResearchPlan

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
SYSTEM_TEXT = """You are a research planner. Break the user's research question into 3-5 specific sub-questions that together cover it.
Rules:
- Include at least one sub-question with stance "opposing" that looks for evidence against the question's premise, or for exceptions.
- Give each sub-question 1-2 short keyword-style search queries suited to arXiv and Semantic Scholar.
- Do not answer the question. Only plan the research."""

prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_TEXT), ("human", "{question}")]
)

planner = prompt | llm.with_structured_output(ResearchPlan)


def make_plan(question: str) -> ResearchPlan:
    result = planner.invoke({"question": question})
    return result
