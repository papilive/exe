"""
WebSocket consumers for real-time execution updates.
"""
import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.conf import settings
from .models import ExecutionLog, ExecutableFile
from .execution import ExecutionManager

logger = logging.getLogger(__name__)

class ExecutionConsumer(AsyncWebsocketConsumer):
    """Consumer to handle real-time execution output."""

    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.execution_id = self.scope['url_route']['kwargs'].get('execution_id')
            self.execution_group_name = f'execution_{self.execution_id}' if self.execution_id else 'execution_general'

            # Validate user authentication
            if not self.scope['user'].is_authenticated:
                logger.warning(f"Unauthenticated user attempted WebSocket connection")
                await self.close()
                return

            # Ensure virtual display is running (only on Linux)
            if not getattr(settings, 'IS_WINDOWS', False):
                try:
                    ExecutionManager.ensure_virtual_display()
                except Exception as e:
                    logger.error(f"Error ensuring virtual display: {e}")

            # Join execution group
            await self.channel_layer.group_add(
                self.execution_group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"WebSocket connection established for execution {self.execution_id}")

            # Send initial status message
            initial_message = {
                'type': 'connection_established',
                'message': 'Conectado al flujo de salida en tiempo real',
                'execution_id': self.execution_id,
                'timestamp': timezone.now().isoformat()
            }

            # Add VNC URL only if not on Windows
            if not getattr(settings, 'IS_WINDOWS', False):
                initial_message['vnc_url'] = f'http://localhost:{getattr(ExecutionManager, "NOVNC_PORT", 6080)}/vnc.html'

            await self.send(text_data=json.dumps(initial_message))

        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        try:
            # Leave execution group
            await self.channel_layer.group_discard(
                self.execution_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for execution {self.execution_id}, code: {close_code}")
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {e}")

    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'check_status':
                # Check execution status and send back
                execution_status = await self.get_execution_status(self.execution_id)
      