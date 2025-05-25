"""
Utilities for executing Windows executables and streaming output in real-time.
"""
import os
import asyncio
import json
import uuid
import subprocess
import logging
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import sys
import platform
import shutil
import signal
import tempfile
import atexit
from pathlib import Path
from django.conf import settings

# Setup logging
logger = logging.getLogger(__name__)

# Check if running on Windows for proper imports
IS_WINDOWS = platform.system() == 'Windows'

# Virtual display configuration
XVFB_DISPLAY = ":99"
NOVNC_PORT = getattr(settings, 'NOVNC_PORT', 6080)

class VirtualDisplay:
    """Manage virtual display for GUI applications."""
    def __init__(self, display=XVFB_DISPLAY):
        self.display = display
        self.xvfb_process = None
        self.vnc_process = None
        self.novnc_process = None
        self.is_running = False
        atexit.register(self.cleanup)

    def start(self):
        """Start virtual display and VNC server."""
        if IS_WINDOWS or self.is_running:
            return
            
        try:
            # Check if Xvfb is available
            if not shutil.which('Xvfb'):
                logger.warning("Xvfb not found, skipping virtual display setup")
                return

            # Start Xvfb
            self.xvfb_process = subprocess.Popen([
                'Xvfb', self.display, '-screen', '0', '1024x768x24', '-ac'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait a bit for Xvfb to start
            asyncio.sleep(1)
            
            # Start x11vnc if available
            if shutil.which('x11vnc'):
                self.vnc_process = subprocess.Popen([
                    'x11vnc', '-display', self.display, '-forever', '-nopw', '-quiet'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Start noVNC if available
            if shutil.which('websockify'):
                novnc_path = "/usr/share/novnc"
                if os.path.exists(novnc_path):
                    self.novnc_process = subprocess.Popen([
                        'websockify', '--web', novnc_path,
                        str(NOVNC_PORT), 'localhost:5900'
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.is_running = True
            logger.info(f"Virtual display started on {self.display}")
            
        except Exception as e:
            logger.error(f"Error starting virtual display: {e}")
            self.cleanup()

    def cleanup(self):
        """Clean up processes on exit."""
        try:
            for process in [self.novnc_process, self.vnc_process, self.xvfb_process]:
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            self.is_running = False
            logger.info("Virtual display cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up virtual display: {e}")

# Global virtual display manager
virtual_display = VirtualDisplay()

# Check if wine is available on Linux
WINE_AVAILABLE = False if IS_WINDOWS else bool(shutil.which('wine'))

# Set up environment variables for WINE
if not IS_WINDOWS and WINE_AVAILABLE:
    wine_prefix = getattr(settings, 'WINE_PREFIX', os.path.expanduser('~/.wine'))
    wine_arch = getattr(settings, 'WINE_ARCH', 'win64')
    
    os.environ['WINEARCH'] = wine_arch
    os.environ['WINEPREFIX'] = wine_prefix
    os.environ['WINEDEBUG'] = '-all'
    
    # Ensure Wine prefix exists
    if not os.path.exists(wine_prefix):
        logger.info("Initializing Wine prefix...")
        try:
            subprocess.run(['winecfg'], check=True, timeout=30)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Wine initialization warning: {e}")

class ExecutionManager:
    """Manager for executable file execution with real-time output streaming."""
    
    NOVNC_PORT = NOVNC_PORT
    MAX_EXECUTION_TIME = getattr(settings, 'EXECUTOR_CONFIG', {}).get('MAX_EXECUTION_TIME', 30)
    MAX_OUTPUT_SIZE = getattr(settings, 'EXECUTOR_CONFIG', {}).get('MAX_OUTPUT_SIZE', 1024 * 1024)
    
    @staticmethod
    def ensure_virtual_display():
        """Ensure virtual display is running."""
        if not IS_WINDOWS and not virtual_display.is_running:
            virtual_display.start()
            if virtual_display.is_running:
                os.environ['DISPLAY'] = XVFB_DISPLAY

    @staticmethod
    def validate_executable(executable_path):
        """Validate if the executable can be run safely."""
        if not os.path.exists(executable_path):
            raise FileNotFoundError(f"Archivo no encontrado: {executable_path}")
        
        if not os.path.isfile(executable_path):
            raise ValueError(f"La ruta no es un archivo: {executable_path}")
        
        # Check file extension
        allowed_extensions = getattr(settings, 'EXECUTOR_CONFIG', {}).get('ALLOWED_EXTENSIONS', ['.exe'])
        file_ext = Path(executable_path).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise ValueError(f"Extensión no permitida: {file_ext}. Permitidas: {allowed_extensions}")
        
        # Check file size (avoid huge files)
        file_size = os.path.getsize(executable_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise ValueError(f"Archivo demasiado grande: {file_size} bytes")
        
        return True

    @staticmethod
    def execute_file_async(executable_path, arguments=None, execution_id=None):
        """
        Execute a file asynchronously and stream output in real-time.

        Args:
            executable_path: Path to the executable file
            arguments: Command line arguments as string
            execution_id: Unique ID for this execution

        Returns:
            dict: execution info including ID and VNC URL
        """
        if execution_id is None:
            execution_id = str(uuid.uuid4())

        try:
            # Validate executable
            ExecutionManager.validate_executable(executable_path)
            
            # Ensure virtual display is running for GUI applications
            ExecutionManager.ensure_virtual_display()

            # Start async execution
            asyncio.create_task(ExecutionManager._execute_and_stream(
                executable_path, arguments, execution_id
            ))

            result = {
                'execution_id': execution_id,
                'status': 'started'
            }
            
            # Add VNC URL only if not on Windows and virtual display is running
            if not IS_WINDOWS and virtual_display.is_running:
                result['vnc_url'] = f'http://localhost:{NOVNC_PORT}/vnc.html'
            
            return result
            
        except Exception as e:
            logger.error(f"Error starting execution: {e}")
            return {
                'execution_id': execution_id,
                'status': 'error',
                'error': str(e)
            }

    @staticmethod
    async def _execute_and_stream(executable_path, arguments, execution_id):
        """
        Execute the file and stream output via WebSockets.
        """
        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'
        
        # Track output size
        total_output_size = 0
        max_output_size = ExecutionManager.MAX_OUTPUT_SIZE

        async def send_message(message_type, **kwargs):
            """Helper to send messages to WebSocket group."""
            try:
                await channel_layer.group_send(group_name, {
                    'type': message_type,
                    **kwargs
                })
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")

        # Prepare command based on platform
        try:
            if IS_WINDOWS:
                cmd = [executable_path]
                env = os.environ.copy()
                creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            else:
                if not WINE_AVAILABLE:
                    error_msg = "Wine no está instalado. No se pueden ejecutar archivos .exe en Linux"
                    await send_message('execution_output', 
                                     output=f"ERROR: {error_msg}",
                                     complete=True, success=False, exit_code=-1)
                    return {'success': False, 'output': error_msg, 'exit_code': -1}
                
                cmd = ['wine', executable_path]
                env = {
                    **os.environ,
                    'WINEDEBUG': '-all',
                    'DISPLAY': os.environ.get('DISPLAY', ':0'),
                    'WINEPREFIX': os.environ.get('WINEPREFIX', os.path.expanduser('~/.wine'))
                }
                creation_flags = 0

            # Add arguments if provided
            if arguments:
                if isinstance(arguments, str):
                    cmd.extend(arguments.split())
                elif isinstance(arguments, list):
                    cmd.extend(arguments)

            # Send initial status
            await send_message('execution_status', 
                             status='starting',
                             message=f'Iniciando ejecución de {os.path.basename(executable_path)}')

            logger.info(f"Executing command: {' '.join(cmd)}")

            # Execute the command with timeout
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env,
                    creationflags=creation_flags if IS_WINDOWS else 0
                ),
                timeout=10  # Timeout for process creation
            )

            await send_message('execution_status', 
                             status='running', 
                             message='Proceso iniciado')

            output_buffer = []
            
            async def read_stream(stream, prefix):
                """Read and stream output from subprocess."""
                nonlocal total_output_size
                
                while True:
                    try:
                        line = await asyncio.wait_for(stream.readline(), timeout=1.0)
                        if not line:
                            break
                            
                        decoded_line = line.decode('utf-8', errors='replace').rstrip()
                        if not decoded_line:
                            continue
                            
                        # Check output size limit
                        line_size = len(decoded_line.encode('utf-8'))
                        if total_output_size + line_size > max_output_size:
                            truncation_msg = f"\n[OUTPUT TRUNCADO - Límite de {max_output_size} bytes alcanzado]"
                            output_buffer.append(truncation_msg)
                            await send_message('execution_output', output=truncation_msg)
                            break
                            
                        total_output_size += line_size
                        formatted_line = f"{prefix}: {decoded_line}"
                        output_buffer.append(formatted_line)

                        await send_message('execution_output', output=formatted_line)
                        
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Error reading stream: {e}")
                        break

            # Create tasks to read both stdout and stderr
            stdout_task = asyncio.create_task(read_stream(process.stdout, "STDOUT"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "STDERR"))

            try:
                # Wait for process completion with timeout
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, return_exceptions=True),
                    timeout=ExecutionManager.MAX_EXECUTION_TIME
                )
                
                exit_code = await asyncio.wait_for(process.wait(), timeout=5)
                success = exit_code == 0

            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                
                timeout_msg = f'Ejecución cancelada por timeout ({ExecutionManager.MAX_EXECUTION_TIME}s)'
                output_buffer.append(timeout_msg)
                await send_message('execution_output', 
                                 output=timeout_msg,
                                 complete=True, success=False, exit_code=-1)
                return {'success': False, 'output': '\n'.join(output_buffer), 'exit_code': -1}

            # Send final results
            final_output = '\n'.join(output_buffer)
            
            await send_message('execution_output',
                             output=final_output,
                             complete=True, success=success, exit_code=exit_code)

            await send_message('execution_status',
                             status='completed',
                             message=f'Ejecución finalizada con código {exit_code}')

            logger.info(f"Execution {execution_id} completed with exit code {exit_code}")
            
            return {
                'success': success,
                'output': final_output,
                'exit_code': exit_code
            }

        except Exception as e:
            error_msg = f'Error durante la ejecución: {str(e)}'
            logger.error(f"Execution error: {e}")
            
            await send_message('execution_output',
                             output=error_msg,
                             complete=True, success=False, exit_code=-1)
            
            await send_message('execution_status',
                             status='error',
                             message=error_msg)

            return {
                'success': False,
                'output': error_msg,
                'exit_code': -1
            }

    @staticmethod
    async def kill_execution(execution_id):
        """
        Kill a running execution by ID.
        This is a placeholder - you'd need to track running processes.
        """
        # TODO: Implement process tracking and killing
        logger.info(f"Kill requested for execution {execution_id}")
        pass