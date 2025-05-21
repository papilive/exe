"""
WebSocket consumers for real-time execution updates.
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ExecutionLog, ExecutableFile

class ExecutionConsumer(AsyncWebsocketConsumer):
    """Consumer to handle real-time execution output."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.execution_id = self.scope['url_route']['kwargs']['execution_id']
        self.execution_group_name = f'execution_{self.execution_id}'

        # Join execution group
        await self.channel_layer.group_add(
            self.execution_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial status message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al flujo de salida en tiempo real',
            'execution_id': self.execution_id
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave execution group
        await self.channel_layer.group_discard(
            self.execution_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'check_status':
            # Check execution status and send back
            execution_status = await self.get_execution_status(self.execution_id)
            await self.send(text_data=json.dumps({
                'type': 'status_update',
                'status': execution_status
            }))

    # Receive message from execution group
    async def execution_output(self, event):
        """Handle execution output updates."""
        # Send output to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'execution_output',
            'output': event['output'],
            'complete': event.get('complete', False),
            'success': event.get('success', None),
            'exit_code': event.get('exit_code', None)
        }))

    async def execution_status(self, event):
        """Handle execution status updates."""
        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'execution_status',
            'status': event['status'],
            'message': event.get('message', '')
        }))

    @database_sync_to_async
    def get_execution_status(self, execution_id):
        """Get current execution status from database."""
        try:
            log = ExecutionLog.objects.get(id=execution_id)
            return {
                'status': 'completed' if log.success is not None else 'running',
                'success': log.success,
                'exit_code': log.exit_code,
                'output': log.output,
                'executed_at': log.executed_at.isoformat(),
                'executable_name': log.executable.name
            }
        except ExecutionLog.DoesNotExist:
            return {
                'status': 'not_found',
                'message': f'No se encontró la ejecución con ID {execution_id}'
            }
