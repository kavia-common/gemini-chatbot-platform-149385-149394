from __future__ import annotations

from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from ..extensions import db
from ..models import ChatSession, Message
from ..schemas import (
    ChatSessionSchema,
    ChatSessionDetailSchema,
    CreateSessionSchema,
    PostMessageRequestSchema,
    PostMessageResponseSchema,
)
from ..services.gemini_service import GeminiService


blp = Blueprint(
    "Chat",
    "chat",
    url_prefix="/api",
    description="Chat and session management routes",
)


def _get_session_or_404(session_id: int) -> ChatSession:
    session = db.session.get(ChatSession, session_id)
    if session is None:
        abort(HTTPStatus.NOT_FOUND, message=f"Session {session_id} not found")
    return session


@blp.route("/sessions")
class SessionsListResource(MethodView):
    """Manage chat sessions."""

    @blp.response(HTTPStatus.OK, ChatSessionSchema(many=True))
    @blp.doc(summary="List chat sessions", description="Retrieve all chat sessions.")
    def get(self):
        """Return a list of all chat sessions."""
        sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).all()
        return sessions

    @blp.arguments(CreateSessionSchema)
    @blp.response(HTTPStatus.CREATED, ChatSessionSchema)
    @blp.doc(summary="Create chat session", description="Create a new chat session.")
    def post(self, json_data):
        """Create a new chat session.

        Request body:
        - title: Optional title for the session
        """
        session = ChatSession(title=json_data.get("title"))
        db.session.add(session)
        db.session.commit()
        return session, HTTPStatus.CREATED


@blp.route("/sessions/<int:session_id>")
class SessionsResource(MethodView):
    """Retrieve or delete a chat session."""

    @blp.response(HTTPStatus.OK, ChatSessionDetailSchema)
    @blp.doc(
        summary="Get chat session",
        description="Retrieve a chat session by ID, including its messages.",
        responses={404: {"description": "Session not found"}},
    )
    def get(self, session_id: int):
        """Return a chat session with its messages."""
        session = _get_session_or_404(session_id)
        return session

    @blp.response(HTTPStatus.NO_CONTENT)
    @blp.doc(
        summary="Delete chat session",
        description="Delete a chat session and all of its messages.",
        responses={404: {"description": "Session not found"}},
    )
    def delete(self, session_id: int):
        """Delete the specified chat session."""
        session = _get_session_or_404(session_id)
        db.session.delete(session)
        db.session.commit()
        return "", HTTPStatus.NO_CONTENT


@blp.route("/sessions/<int:session_id>/messages")
class SessionMessagesResource(MethodView):
    """Post messages in a session and get assistant reply."""

    @blp.arguments(PostMessageRequestSchema)
    @blp.response(HTTPStatus.OK, PostMessageResponseSchema)
    @blp.doc(
        summary="Send user message",
        description=(
            "Post a user message to a session, invoke Gemini to generate a reply, "
            "and store both user and assistant messages."
        ),
        responses={
            404: {"description": "Session not found"},
            400: {"description": "Invalid request body"},
        },
    )
    def post(self, json_data, session_id: int):
        """Create a user message, call Gemini, and persist the assistant reply.

        Request body:
        - content: User text message to send

        Returns:
        - session_id
        - user_message: Stored user message
        - assistant_message: Stored assistant reply
        """
        session = _get_session_or_404(session_id)
        user_content = json_data["content"]

        # Save user message
        user_msg = Message(session_id=session.id, role="user", content=user_content)
        db.session.add(user_msg)
        db.session.flush()  # get user_msg.id before committing

        # Generate assistant reply via Gemini
        try:
            gemini = GeminiService()
            assistant_text = gemini.generate_reply(user_content)
        except Exception as exc:
            # Rollback user message if generation fails
            db.session.rollback()
            abort(HTTPStatus.BAD_GATEWAY, message=f"Gemini error: {exc}")

        # Save assistant message and commit both
        assistant_msg = Message(session_id=session.id, role="assistant", content=assistant_text)
        db.session.add(assistant_msg)
        db.session.commit()

        return {
            "session_id": session.id,
            "user_message": user_msg,
            "assistant_message": assistant_msg,
        }
