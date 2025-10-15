from __future__ import annotations

from marshmallow import Schema, fields, validate


# PUBLIC_INTERFACE
class MessageSchema(Schema):
    """Schema representing a single chat message."""
    id = fields.Int(dump_only=True, description="Unique ID of the message")
    session_id = fields.Int(required=True, description="Parent session ID")
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["user", "assistant"]),
        description="Role of the message author",
    )
    content = fields.Str(required=True, description="Raw text content of the message")
    created_at = fields.DateTime(dump_only=True, format="iso", description="Creation timestamp")
    updated_at = fields.DateTime(dump_only=True, format="iso", description="Last update timestamp")


# PUBLIC_INTERFACE
class ChatSessionSchema(Schema):
    """Schema representing a chat session."""
    id = fields.Int(dump_only=True, description="Unique ID of the chat session")
    title = fields.Str(allow_none=True, description="Optional title for the session")
    created_at = fields.DateTime(dump_only=True, format="iso", description="Creation timestamp")
    updated_at = fields.DateTime(dump_only=True, format="iso", description="Last update timestamp")


# PUBLIC_INTERFACE
class ChatSessionDetailSchema(ChatSessionSchema):
    """Schema for a chat session including its messages."""
    messages = fields.List(fields.Nested(MessageSchema), description="Messages in the session")


# PUBLIC_INTERFACE
class CreateSessionSchema(Schema):
    """Request body schema for creating a new session."""
    title = fields.Str(
        required=False,
        allow_none=True,
        description="Optional title for the session"
    )


# PUBLIC_INTERFACE
class PostMessageRequestSchema(Schema):
    """Request body schema for posting a user message in a session."""
    content = fields.Str(required=True, description="User message content to send to the assistant")


# PUBLIC_INTERFACE
class PostMessageResponseSchema(Schema):
    """Response schema for posting a message and receiving assistant reply."""
    session_id = fields.Int(required=True, description="Session ID the messages belong to")
    user_message = fields.Nested(MessageSchema, required=True, description="Stored user message")
    assistant_message = fields.Nested(
        MessageSchema, required=True, description="Stored assistant message reply"
    )
