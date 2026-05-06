from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import json
import uuid
from datetime import datetime

from app.auth.models import UserContext
from app.core.config import settings
from app.services.rag_pipeline_service import run_rag_pipeline

router = APIRouter()


# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_context: UserContext):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.connection_metadata[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "query_count": 0,
            "user_id": user_context.user_id,
            "tenant_id": user_context.tenant_id,
            "channel": user_context.channel,
        }

        # Send welcome message
        await self.send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connection established"
        })

    def disconnect(self, session_id: str):
        """Remove a connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_metadata:
            del self.connection_metadata[session_id]

    async def send_message(self, session_id: str, message: Dict):
        """Send a message to a specific connection"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
                # Update last activity
                if session_id in self.connection_metadata:
                    self.connection_metadata[session_id]["last_activity"] = datetime.now().isoformat()
            except:
                # Connection might be closed
                self.disconnect(session_id)

    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(session_id)

        # Clean up disconnected clients
        for session_id in disconnected:
            self.disconnect(session_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a specific connection"""
        return self.connection_metadata.get(session_id)

    def get_all_connections(self) -> Dict[str, Dict]:
        """Get information about all connections"""
        return self.connection_metadata.copy()


manager = ConnectionManager()


@router.get("/status")
async def websocket_status():
    """Get WebSocket status information"""
    return {
        "active_connections": manager.get_connection_count(),
        "connections": manager.get_all_connections(),
        "timestamp": datetime.now().isoformat()
    }


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    await handle_websocket_connection(websocket)


@router.websocket("")
async def websocket_endpoint_no_slash(websocket: WebSocket):
    """WebSocket endpoint without trailing slash"""
    await handle_websocket_connection(websocket)


async def handle_websocket_connection(websocket: WebSocket):
    """Common WebSocket connection handler"""
    session_id = websocket.headers.get("x-session-id") or websocket.query_params.get("session_id") or str(uuid.uuid4())
    user_context = UserContext(
        user_id=settings.DEFAULT_USER_ID,
        tenant_id=settings.DEFAULT_TENANT_ID,
        session_id=session_id,
        ip=websocket.client.host if websocket.client else "unknown",
        channel=websocket.headers.get("x-channel", "web"),
    )

    # Accept connection
    await manager.connect(websocket, session_id, user_context)

    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            request = json.loads(data)

            # Handle different message types
            if request.get("type") == "query":
                await handle_query_request(session_id, request)

            elif request.get("type") == "report":
                await handle_report_request(session_id, request)

            elif request.get("type") == "status":
                await handle_status_request(session_id, request)

            elif request.get("type") == "ping":
                # Respond with pong
                await manager.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                await manager.send_message(session_id, {
                    "type": "error",
                    "message": f"Unknown message type: {request.get('type')}"
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)


async def handle_query_request(session_id: str, request: Dict):
    """Handle query requests via WebSocket"""
    try:
        query_data = request.get("data", {})
        question = query_data.get("question", "")
        top_k = query_data.get("top_k", 5)
        stream = query_data.get("stream", True)
        request_session_id = query_data.get("session_id") or session_id
        connection_info = manager.get_connection_info(session_id) or {}
        user_context = UserContext(
            user_id=connection_info.get("user_id", settings.DEFAULT_USER_ID),
            tenant_id=connection_info.get("tenant_id", settings.DEFAULT_TENANT_ID),
            session_id=request_session_id,
            ip="websocket",
            channel=connection_info.get("channel", "web"),
        )

        # Update query count
        if session_id in manager.connection_metadata:
            manager.connection_metadata[session_id]["query_count"] += 1

        # Send status
        await manager.send_message(session_id, {
            "type": "status",
            "message": "正在检索文档..."
        })

        result = await run_rag_pipeline(
            question=question,
            user_context=user_context,
            top_k=top_k,
        )
        sources = result["sources"]

        if not sources:
            await manager.send_message(session_id, {
                "type": "error",
                "message": "没有找到相关文档"
            })
            return

        # Send sources
        from app.schemas.schemas import SourceDocument
        source_docs = []
        for source in sources:
            source_docs.append(SourceDocument(
                content=source["content"],
                file_name=source["metadata"]["file_name"],
                score=source["score"],
                page_number=source["metadata"].get("page_label")
            ))

        await manager.send_message(session_id, {
            "type": "sources",
            "data": [doc.dict() for doc in source_docs]
        })

        # Generate answer
        await manager.send_message(session_id, {
            "type": "status",
            "message": "正在生成答案..."
        })

        context = "\n\n".join(
            f"[来源: {source['metadata']['file_name']}]\n{source['content']}"
            for source in sources
        )

        if stream:
            await manager.send_message(session_id, {
                "type": "answer",
                "content": result["answer"],
                "trace_id": result.get("trace_id"),
                "session_id": user_context.session_id,
            })
        else:
            await manager.send_message(session_id, {
                "type": "answer",
                "content": result["answer"],
                "trace_id": result.get("trace_id"),
                "session_id": user_context.session_id,
            })

        # Send end signal
        await manager.send_message(session_id, {
            "type": "end",
            "content": "",
            "trace_id": result.get("trace_id"),
            "session_id": user_context.session_id,
        })

    except Exception as e:
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"查询错误: {str(e)}"
        })


async def handle_report_request(session_id: str, request: Dict):
    """Handle report generation requests via WebSocket"""
    try:
        report_data = request.get("data", {})
        question = report_data.get("question", "")
        answer = report_data.get("answer", "")
        sources = report_data.get("sources", [])
        report_type = report_data.get("report_type", "structured")

        # Send status
        await manager.send_message(session_id, {
            "type": "status",
            "message": "正在生成报告..."
        })

        # Generate report
        report = await langchain_service.generate_report(
            question=question,
            answer=answer,
            sources=sources,
            report_type=report_type
        )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"保险分析报告_{timestamp}.txt"
        save_result = await langchain_service.save_report(filename, report)

        # Send report
        await manager.send_message(session_id, {
            "type": "report",
            "data": {
                "content": report,
                "filename": filename,
                "file_path": save_result,
                "timestamp": timestamp
            }
        })

    except Exception as e:
        await manager.send_message(session_id, {
            "type": "error",
            "message": f"报告生成错误: {str(e)}"
        })


async def handle_status_request(session_id: str, request: Dict):
    """Handle status information requests"""
    connection_info = manager.get_connection_info(session_id)
    await manager.send_message(session_id, {
        "type": "status_info",
        "data": {
            "session_id": session_id,
            "connection_info": connection_info,
            "server_time": datetime.now().isoformat()
        }
    })
