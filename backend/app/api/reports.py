from fastapi import APIRouter, HTTPException
from typing import List, Optional
import uuid
from datetime import datetime

from schemas.schemas import ReportRequest, ReportResponse, SourceDocument
from services.llamaindex_service import llamaindex_service
from services.langchain_service import langchain_service
from core.config import settings

router = APIRouter()


@router.post("/", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate an analysis report based on Q&A and sources"""
    try:
        # Step 1: Retrieve relevant documents for the question
        sources_data = await llamaindex_service.query(
            query_text=request.question,
            top_k=5  # Use default top_k for reports
        )

        if not sources_data:
            raise HTTPException(status_code=404, detail="没有找到相关文档来生成报告")

        # Convert sources to SourceDocument format
        source_docs = []
        source_names = []
        for source in sources_data:
            source_docs.append(SourceDocument(
                content=source["content"],
                file_name=source["metadata"]["file_name"],
                score=source["score"],
                page_number=source["metadata"].get("page_label")
            ))
            source_names.append(source["metadata"]["file_name"])

        # Step 2: Generate answer for the question
        context = "\n\n".join(
            f"[来源: {source['metadata']['file_name']}]\n{source['content']}"
            for source in sources_data
        )

        answer = await langchain_service.answer_question(
            question=request.question,
            context=context,
            stream=False
        )

        # Step 3: Generate report
        report = await langchain_service.generate_report(
            question=request.question,
            answer=answer,
            sources=source_names,
            report_type=request.report_type
        )

        # Step 4: Handle email delivery if requested
        email_sent = False
        if request.send_email and request.email_recipient:
            email_result = await langchain_service.send_email(
                recipient=request.email_recipient,
                subject=f"保险产品分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                content=report
            )
            email_sent = True

        # Step 5: Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"保险分析报告_{timestamp}.txt"
        save_result = await langchain_service.save_report(filename, report)

        return ReportResponse(
            report_id=str(uuid.uuid4()),
            report_content=report,
            timestamp=datetime.now(),
            file_path=save_result.replace("报告已保存到 ", ""),
            email_sent=email_sent
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告时出错: {str(e)}")


@router.get("/list")
async def list_reports():
    """List all generated reports"""
    try:
        import os

        reports_dir = settings.REPORTS_DIR
        if not os.path.exists(reports_dir):
            return {"reports": [], "total_count": 0}

        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith(".txt") and filename.startswith("保险分析报告_"):
                filepath = os.path.join(reports_dir, filename)
                file_stats = os.stat(filepath)

                reports.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "created_at": datetime.fromtimestamp(file_stats.st_mtime),
                    "filepath": filepath
                })

        return {
            "reports": sorted(reports, key=lambda x: x["created_at"], reverse=True),
            "total_count": len(reports)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表时出错: {str(e)}")


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Download a specific report"""
    try:
        import os

        reports_dir = settings.REPORTS_DIR
        if not os.path.exists(reports_dir):
            raise HTTPException(status_code=404, detail="报告目录不存在")

        # Find the report file
        report_file = None
        for filename in os.listdir(reports_dir):
            if filename.endswith(".txt") and filename.startswith("保险分析报告_"):
                if filename.replace("保险分析报告_", "").replace(".txt", "") == report_id:
                    report_file = os.path.join(reports_dir, filename)
                    break

        if not report_file:
            raise HTTPException(status_code=404, detail="报告不存在")

        # Read the report content
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Return file content for download
        from fastapi.responses import FileResponse
        return FileResponse(
            path=report_file,
            filename=os.path.basename(report_file),
            media_type='text/plain'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告时出错: {str(e)}")


@router.delete("/delete/{report_id}")
async def delete_report(report_id: str):
    """Delete a specific report"""
    try:
        import os

        reports_dir = settings.REPORTS_DIR
        if not os.path.exists(reports_dir):
            raise HTTPException(status_code=404, detail="报告目录不存在")

        # Find and delete the report file
        filename = f"保险分析报告_{report_id}.txt"
        file_path = os.path.join(reports_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="报告不存在")

        os.remove(file_path)
        return {"message": f"报告 {filename} 已删除成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除报告时出错: {str(e)}")