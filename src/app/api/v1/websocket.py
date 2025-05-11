"""WebSocket API endpoints."""

import logging
from typing import Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import Response

from src.app.core.config import settings
from src.app.core.session_storage import session_storage
from src.app.schemas.websocket_session import (
    CreateSessionResponse,
    FilesListResponse,
    FileUploadResponse,
    JoinSessionResponse,
    MealType,
    SessionStatusResponse,
)
from src.app.services.websocket_service import websocket_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/session", tags=["websocket"])


@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    request: Request, expiry_seconds: Optional[int] = Form(300, ge=60, le=3600)
):
    """Create a new WebSocket session.

    Args:
        request: FastAPI request object
        expiry_seconds: Time in seconds before the session expires (60-3600 seconds)

    Returns:
        CreateSessionResponse containing session ID, join URL, and QR code

    Raises:
        HTTPException: If session creation fails
    """
    try:
        # Use the base URL from settings
        base_url = settings.QR_CODE_BASE_URL

        session_id, join_url, qrcode_base64 = websocket_service.generate_session_qr(
            base_url, expiry_seconds=expiry_seconds
        )

        return CreateSessionResponse(
            session_id=session_id,
            join_url=join_url,
            qrcode_base64=qrcode_base64,
            expires_in_seconds=expiry_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        )


@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str = Path(..., description="Session ID")):
    """Get the status of a session.

    Args:
        session_id: Session ID

    Returns:
        SessionStatusResponse containing session status information

    Raises:
        HTTPException: If session not found
    """
    session_info = websocket_service.get_session_status(session_id)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return SessionStatusResponse(
        session_id=session_info["session_id"],
        status=session_info["status"],
        connected_clients=session_info["connected_clients"],
        created_at=session_info["created_at"],
        expires_at=session_info["expires_at"],
        error=session_info.get("error"),
    )


@router.post("/join", response_model=JoinSessionResponse)
async def join_session(session_id: str = Query(..., description="Session ID")):
    """Join a session.

    Args:
        session_id: Session ID

    Returns:
        JoinSessionResponse containing session status

    Raises:
        HTTPException: If session not found or cannot be joined
    """
    success, message, session_status = websocket_service.join_session(session_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return JoinSessionResponse(
        session_id=session_id,
        status=session_status,
        message=message,
    )


@router.post("/upload/{session_id}", response_model=FileUploadResponse)
async def upload_file(
    session_id: str = Path(..., description="Session ID"),
    file: UploadFile = File(...),
    meal_type: Optional[MealType] = Form(
        None, description="Type of meal (breakfast, lunch, dinner)"
    ),
):
    """Upload a file to a session.

    Args:
        session_id: Session ID
        file: Uploaded file
        meal_type: Type of meal (breakfast, lunch, dinner)

    Returns:
        FileUploadResponse indicating success

    Raises:
        HTTPException: If upload fails, session not found, or invalid file
    """
    success, file_id, file_info = await websocket_service.handle_file_upload(
        session_id, file, meal_type.value if meal_type else None
    )

    if not success or not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload file. Session may be invalid or file type not supported.",
        )

    return FileUploadResponse(
        file_id=file_id,
        session_id=session_id,
        status=file_info["status"],
        meal_type=meal_type,
        message="File uploaded successfully",
    )


@router.get("/files/{session_id}", response_model=FilesListResponse)
async def list_files(session_id: str = Path(..., description="Session ID")):
    """List files in a session.

    Args:
        session_id: Session ID

    Returns:
        FilesListResponse containing list of files

    Raises:
        HTTPException: If session not found
    """
    session_info = websocket_service.get_session_status(session_id)
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    files = websocket_service.list_files(session_id)
    return FilesListResponse(session_id=session_id, files=files)


@router.get("/file/{session_id}/{file_id}", name="download_file")
async def download_file(
    session_id: str = Path(..., description="Session ID"),
    file_id: str = Path(..., description="File ID"),
):
    """Download a file from a session.

    Args:
        session_id: Session ID
        file_id: File ID

    Returns:
        File content with appropriate content type

    Raises:
        HTTPException: If session or file not found
    """
    # Get session first to verify it exists
    session_info = websocket_service.get_session_status(session_id)
    if not session_info:
        logger.error(f"Session {session_id} not found when downloading file {file_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Get direct access to the session
    session = session_storage.get_session(session_id)

    # Get the file info using the service
    file_info = websocket_service.get_file(session_id, file_id)

    if not file_info:
        logger.error(f"File {file_id} not found in session {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )

    if "content" not in file_info:
        logger.error(f"File {file_id} has no content in session {session_id}")

        # Additional recovery attempt - if the file exists in the session but content was lost
        if (
            "files" in session
            and file_id in session["files"]
            and "content" in session["files"][file_id]
        ):
            file_info["content"] = session["files"][file_id]["content"]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File content not found"
            )

    # Decode base64 content
    import base64

    try:
        file_content = base64.b64decode(file_info["content"])
    except Exception as e:
        logger.error(f"Error decoding file content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing file content",
        )

    return Response(
        content=file_content,
        media_type=file_info["content_type"],
        headers={
            "Content-Disposition": f"attachment; filename={file_info['filename']}",
            "Content-Length": str(len(file_content)),
        },
    )


@router.post("/extend/{session_id}")
async def extend_session(
    session_id: str = Path(..., description="Session ID"),
    additional_seconds: int = Form(
        ..., ge=60, le=3600, description="Additional time in seconds"
    ),
):
    """Extend the expiry time of a session.

    Args:
        session_id: Session ID
        additional_seconds: Additional time in seconds (60-3600)

    Returns:
        Success message

    Raises:
        HTTPException: If session not found or extension fails
    """
    success = websocket_service.extend_session(session_id, additional_seconds)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return {"message": "Session extended successfully"}


@router.post("/close/{session_id}")
async def close_session(session_id: str = Path(..., description="Session ID")):
    """Close a session.

    Args:
        session_id: Session ID

    Returns:
        Success message

    Raises:
        HTTPException: If session not found or closing fails
    """
    success = websocket_service.close_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    return {"message": "Session closed successfully"}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication.

    Args:
        websocket: WebSocket connection
        session_id: Session ID
    """
    # Try to connect to the session
    connection_successful = await websocket_service.connect_websocket(
        session_id, websocket
    )
    if not connection_successful:
        logger.warning(f"WebSocket connection rejected for session {session_id}")
        await websocket.close(code=1008)  # Policy Violation
        return

    try:
        # Main WebSocket event loop
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            logger.debug(f"Received WebSocket message: {data}")

            # Process messages based on type
            message_type = data.get("type")

            if message_type == "ping":
                # Respond to ping with pong
                await websocket.send_json({"type": "pong"})
            elif message_type == "message":
                # Broadcast message to all clients in the session
                data["session_id"] = session_id
                await session_storage.broadcast_message(session_id, data)
    except WebSocketDisconnect:
        # Handle client disconnect
        await websocket_service.disconnect_websocket(session_id, websocket)
    except Exception as e:
        # Handle other exceptions
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            await websocket_service.disconnect_websocket(session_id, websocket)
        except Exception:
            pass  # Ignore errors during disconnect
