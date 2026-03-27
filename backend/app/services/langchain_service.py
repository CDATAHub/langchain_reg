import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document as LCDocument
from langchain_core.tools import tool
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import JsonOutputParser

from core.config import settings


class LangChainService:
    def __init__(self):
        self.llm: Optional[ChatTongyi] = None
        self.qa_chain = None
        self.report_chain = None

    async def setup(self):
        """Initialize LangChain with LLM"""
        print("[LangChain] Initializing...")
        self.llm = ChatTongyi(
            model_name=settings.LLM_MODEL,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            temperature=settings.TEMPERATURE,
        )
        self.qa_chain = await self._create_qa_chain()
        self.report_chain = await self._create_report_chain()
        print("[LangChain] Initialized successfully")
        return self.llm

    async def _create_qa_chain(self):
        """Create QA chain for answering questions"""
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的保险产品顾问。
根据以下检索到的文档内容回答用户的问题。
如果文档中没有相关信息，请如实说明。请用中文回复。

检索到的文档内容:
{context}"""),
            ("human", "{question}")
        ])
        return qa_prompt | self.llm | StrOutputParser()

    async def _create_report_chain(self):
        """Create report generation chain"""
        report_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的保险产品分析师。
根据以下问答记录,生成一份结构化的分析报告。
报告需包含:概述、核心要点、适用场景、注意事项。
请用中文撰写,语言简洁专业。

问答记录:
问题: {question}
回答: {answer}

相关文档来源: {sources}"""),
            ("human", "请生成分析报告")
        ])
        return report_prompt | self.llm | StrOutputParser()

    async def answer_question(
        self,
        question: str,
        context: str,
        stream: bool = False
    ) -> str:
        """Answer a question with the given context"""
        if not self.qa_chain:
            await self.setup()

        try:
            if stream:
                # For streaming, we'll use a streaming callback
                result = await asyncio.to_thread(
                    self.qa_chain.invoke,
                    {"context": context, "question": question}
                )
                return result
            else:
                result = await asyncio.to_thread(
                    self.qa_chain.invoke,
                    {"context": context, "question": question}
                )
                return result
        except Exception as e:
            print(f"[LangChain] Error answering question: {e}")
            return f"抱歉,回答问题时出错: {str(e)}"

    async def stream_answer(
        self,
        question: str,
        context: str
    ) -> AsyncGenerator[str, None]:
        """Stream answer to a question with the given context"""
        if not self.qa_chain:
            await self.setup()

        try:
            # Use streaming with invoke_async
            async for chunk in self.qa_chain.astream(
                {"context": context, "question": question}
            ):
                if isinstance(chunk, str):
                    yield chunk
        except Exception as e:
            print(f"[LangChain] Error streaming answer: {e}")
            yield f"抱歉,流式回答时出错: {str(e)}"

    async def generate_report(
        self,
        question: str,
        answer: str,
        sources: List[str],
        report_type: str = "structured"
    ) -> str:
        """Generate a report from Q&A and sources"""
        if not self.report_chain:
            await self.setup()

        try:
            sources_str = ", ".join(sources)

            result = await asyncio.to_thread(
                self.report_chain.invoke,
                {
                    "question": question,
                    "answer": answer,
                    "sources": sources_str
                }
            )

            return result
        except Exception as e:
            print(f"[LangChain] Error generating report: {e}")
            return f"抱歉,生成报告时出错: {str(e)}"

    @tool
    async def save_report(self, filename: str, content: str) -> str:
        """Save report to local file"""
        try:
            output_dir = settings.REPORTS_DIR
            os.makedirs(output_dir, exist_ok=True)

            filepath = os.path.join(output_dir, filename)

            # Write file asynchronously
            def write_file():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            await asyncio.to_thread(write_file)

            print(f"[LangChain] Report saved to {filepath}")
            return f"报告已保存到 {filepath}"
        except Exception as e:
            print(f"[LangChain] Error saving report: {e}")
            return f"保存报告失败: {str(e)}"

    @tool
    async def send_email(
        self,
        recipient: str,
        subject: str,
        content: str
    ) -> str:
        """Send email with report content"""
        try:
            # Simulate email sending (in production, integrate with SMTP or email API)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Log the email details
            print(f"\n--- 模拟发送邮件 ---")
            print(f"  收件人: {recipient}")
            print(f"  主题:   {subject}")
            print(f"  时间:   {timestamp}")
            print(f"  正文长度: {len(content)} 字")
            print(f"--- 邮件发送成功 ---\n")

            return f"邮件已于 {timestamp} 成功发送至 {recipient},主题: {subject}"

        except Exception as e:
            print(f"[LangChain] Error sending email: {e}")
            return f"发送邮件失败: {str(e)}"

    async def process_report_workflow(
        self,
        question: str,
        answer: str,
        sources: List[str],
        send_email: bool = False,
        email_recipient: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete workflow for report generation and optional email delivery"""
        try:
            # Generate report
            report = await self.generate_report(question, answer, sources)

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"保险分析报告_{timestamp}.txt"

            save_result = await self.save_report(filename, report)

            # Send email if requested
            email_result = None
            if send_email and email_recipient:
                email_result = await self.send_email(
                    email_recipient,
                    f"保险产品分析报告 - {timestamp}",
                    report
                )

            return {
                "report": report,
                "file_path": os.path.join(settings.REPORTS_DIR, filename),
                "save_result": save_result,
                "email_result": email_result,
                "timestamp": timestamp
            }

        except Exception as e:
            print(f"[LangChain] Error in report workflow: {e}")
            return {"error": str(e)}


# Global service instance
langchain_service = LangChainService()