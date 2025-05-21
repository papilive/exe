"""
Utilities for executing Windows executables and streaming output in real-time.
"""
import os
import asyncio
import json
import uuid
import subprocess
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import sys
import platform

# Check if running on Windows for proper imports
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32process
    except ImportError:
        print("WARNING: pywin32 not installed. Windows-specific features disabled.")

class ExecutionManager:
    """Manager for executable file execution with real-time output streaming."""

    @staticmethod
    def execute_file_async(executable_path, arguments=None, execution_id=None):
        """
        Execute a file asynchronously and stream output in real-time.

        Args:
            executable_path: Path to the executable file
            arguments: Command line arguments as string
            execution_id: Unique ID for this execution

        Returns:
            execution_id: The ID for this execution
        """
        if execution_id is None:
            execution_id = str(uuid.uuid4())

        # Start async execution in a separate thread to not block Django
        async_to_sync(ExecutionManager._execute_and_stream)(
            executable_path, arguments, execution_id
        )

        return execution_id

    @staticmethod
    async def _execute_and_stream(executable_path, arguments, execution_id):
        """
        Execute the file and stream output via WebSockets.

        This runs in an async context.
        """
        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'

        # Prepare command
        cmd = [executable_path]
        if arguments:
            cmd.extend(arguments.split())

        # Send initial status
        await channel_layer.group_send(
            group_name,
            {
                'type': 'execution_status',
                'status': 'starting',
                'message': f'Iniciando ejecución de {os.path.basename(executable_path)}'
            }
        )

        success = False
        exit_code = -1
        output_buffer = []

        try:
            # Execute the command with real-time output streaming
            if IS_WINDOWS:
                # Windows-specific execution
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            else:
                # Non-Windows (for development/testing)
                # In production, this should only run on Windows
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            # Send started status
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'execution_status',
                    'status': 'running',
                    'message': 'Proceso iniciado'
                }
            )

            # Stream stdout
            async def read_stream(stream, prefix):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                    output_buffer.append(f"{prefix}: {decoded_line}")

                    # Send to WebSocket
                    await channel_layer.group_send(
                        group_name,
                        {
                            'type': 'execution_output',
                            'output': f"{prefix}: {decoded_line}"
                        }
                    )

            # Create tasks to read both stdout and stderr
            stdout_task = asyncio.create_task(read_stream(process.stdout, "STDOUT"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "STDERR"))

            # Wait for both tasks to complete and get exit code
            await asyncio.gather(stdout_task, stderr_task)
            exit_code = await process.wait()
            success = exit_code == 0

            # Final output send
            final_output = '\n'.join(output_buffer)

            # Send completion status
            await channel_layer.group_send(
                group_name,
                {
                    'type': 'execution_output',
                    'output': final_output,
                    'complete': True,
                    'success': success,
                    'exit_code': exit_code
                }
            )

            await channel_layer.group_send(
                group_name,
                {
                    'type': 'execution_status',
                    'status': 'completed',
                    'message': 'Ejecución finalizada'
                }
            )

            return {
                'success': success,
                'output': final_output,
                'exit_code': exit_code
            }

        except asyncio.TimeoutError:
            error_msg = 'Ejecución cancelada por timeout'
            output_buffer.append(error_msg)

            await channel_layer.group_send(
                group_name,
                {
                    'type': 'execution_output',
                    'output': error_msg,
                    'complete': True,
                    'success': False,
                    'exit_code': -1
                }
            )

            return {
                'success': False,
                'output': '\n'.join(output_buffer),
                'exit_code': -1
            }

        except Exception as e:
            error_msg = f'Error durante la ejecución: {str(e)}'
            output_buffer.append(error_msg)

            await channel_layer.group_send(
                group_name,
                {
                    'type': 'execution_output',
                    'output': error_msg,
                    'complete': True,
                    'success': False,
                    'exit_code': -1
                }
            )

            return {
                'success': False,
                'output': '\n'.join(output_buffer),
                'exit_code': -1
            }
