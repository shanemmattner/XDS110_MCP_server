#!/usr/bin/env python3
"""
MCP-Dash Bridge: Connects MCP Server with Plotly Dash UI
Enables collaborative debugging between LLM and human engineers
"""

import asyncio
import json
import redis
import websockets
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DebugSession:
    """Represents a debugging session shared between MCP and UI"""
    session_id: str
    project_name: str
    map_file: Optional[str]
    started_at: datetime
    variables_watching: List[str]
    plots_active: List[Dict]
    triggers_set: List[Dict]
    
    def to_dict(self):
        return {
            **asdict(self),
            'started_at': self.started_at.isoformat()
        }


class MCPDashBridge:
    """
    Bridges MCP Server with Dash UI for collaborative debugging
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.websocket_clients = set()
        self.active_sessions = {}
        self.data_buffer = {}  # Buffer for batch updates
        self.update_interval = 0.1  # 10Hz updates
        
    async def start_bridge(self, mcp_port=3001, ws_port=8081):
        """Start the bridge services"""
        # Start WebSocket server for Dash UI
        ws_server = await websockets.serve(
            self.handle_websocket,
            'localhost',
            ws_port
        )
        logger.info(f"WebSocket server started on port {ws_port}")
        
        # Start MCP listener
        mcp_task = asyncio.create_task(self.mcp_listener(mcp_port))
        
        # Start update loop
        update_task = asyncio.create_task(self.update_loop())
        
        await asyncio.gather(mcp_task, update_task)
        
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections from Dash UI"""
        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                await self.process_ui_message(json.loads(message), websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.remove(websocket)
            
    async def process_ui_message(self, message: Dict, websocket):
        """Process messages from UI"""
        msg_type = message.get('type')
        
        if msg_type == 'subscribe':
            # UI subscribing to variables
            variables = message.get('variables', [])
            session_id = message.get('session_id')
            await self.subscribe_variables(session_id, variables)
            
        elif msg_type == 'command':
            # UI sending command to target
            command = message.get('command')
            await self.execute_command(command)
            
        elif msg_type == 'export':
            # UI requesting data export
            await self.export_data(message)
            
    async def mcp_listener(self, port):
        """Listen for MCP server events"""
        async with websockets.connect(f'ws://localhost:{port}/mcp-events') as ws:
            async for message in ws:
                await self.process_mcp_message(json.loads(message))
                
    async def process_mcp_message(self, message: Dict):
        """Process messages from MCP server"""
        msg_type = message.get('type')
        
        if msg_type == 'session_created':
            # New debugging session started via MCP
            session = DebugSession(**message['data'])
            self.active_sessions[session.session_id] = session
            await self.broadcast_to_ui({
                'type': 'session_started',
                'session': session.to_dict()
            })
            
        elif msg_type == 'variable_read':
            # Variable value read from target
            await self.buffer_variable_update(message['data'])
            
        elif msg_type == 'plot_requested':
            # LLM requested a plot
            await self.create_plot(message['data'])
            
        elif msg_type == 'trigger_set':
            # LLM set a trigger
            await self.add_trigger(message['data'])
            
    async def buffer_variable_update(self, data: Dict):
        """Buffer variable updates for batch sending"""
        var_name = data['name']
        value = data['value']
        timestamp = data.get('timestamp', datetime.now().timestamp())
        
        if var_name not in self.data_buffer:
            self.data_buffer[var_name] = []
        
        self.data_buffer[var_name].append({
            'timestamp': timestamp,
            'value': value
        })
        
        # Store in Redis for persistence
        redis_key = f"var:{var_name}:latest"
        self.redis_client.set(redis_key, json.dumps({
            'value': value,
            'timestamp': timestamp
        }))
        
        # Store history (last 1000 points)
        history_key = f"var:{var_name}:history"
        self.redis_client.lpush(history_key, json.dumps({
            'timestamp': timestamp,
            'value': value
        }))
        self.redis_client.ltrim(history_key, 0, 999)
        
    async def update_loop(self):
        """Send batched updates to UI clients"""
        while True:
            if self.data_buffer and self.websocket_clients:
                # Prepare batch update
                batch_update = {
                    'type': 'batch_update',
                    'timestamp': datetime.now().timestamp(),
                    'updates': []
                }
                
                for var_name, values in self.data_buffer.items():
                    if values:
                        # Send latest value and clear buffer
                        latest = values[-1]
                        batch_update['updates'].append({
                            'name': var_name,
                            'value': latest['value'],
                            'timestamp': latest['timestamp']
                        })
                
                # Clear buffer
                self.data_buffer.clear()
                
                # Broadcast to all UI clients
                await self.broadcast_to_ui(batch_update)
                
            await asyncio.sleep(self.update_interval)
            
    async def broadcast_to_ui(self, message: Dict):
        """Broadcast message to all connected UI clients"""
        if self.websocket_clients:
            message_json = json.dumps(message)
            disconnected = set()
            
            for ws in self.websocket_clients:
                try:
                    await ws.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(ws)
                    
            # Clean up disconnected clients
            self.websocket_clients -= disconnected
            
    async def create_plot(self, plot_config: Dict):
        """Create a new plot in the UI"""
        plot_id = plot_config.get('id', f"plot_{datetime.now().timestamp()}")
        
        # Store plot configuration
        redis_key = f"plot:{plot_id}"
        self.redis_client.set(redis_key, json.dumps(plot_config))
        
        # Notify UI
        await self.broadcast_to_ui({
            'type': 'create_plot',
            'plot': plot_config
        })
        
    async def add_trigger(self, trigger_config: Dict):
        """Add a conditional trigger"""
        trigger_id = trigger_config.get('id', f"trigger_{datetime.now().timestamp()}")
        
        # Store trigger configuration
        redis_key = f"trigger:{trigger_id}"
        self.redis_client.set(redis_key, json.dumps(trigger_config))
        
        # Notify UI
        await self.broadcast_to_ui({
            'type': 'add_trigger',
            'trigger': trigger_config
        })
        
        # Start monitoring for trigger
        asyncio.create_task(self.monitor_trigger(trigger_config))
        
    async def monitor_trigger(self, trigger_config: Dict):
        """Monitor a trigger condition"""
        variable = trigger_config['variable']
        condition = trigger_config['condition']
        threshold = trigger_config.get('threshold')
        action = trigger_config['action']
        
        while True:
            # Get latest value from Redis
            redis_key = f"var:{variable}:latest"
            value_json = self.redis_client.get(redis_key)
            
            if value_json:
                data = json.loads(value_json)
                value = data['value']
                
                # Check condition
                triggered = False
                if condition == '>' and value > threshold:
                    triggered = True
                elif condition == '<' and value < threshold:
                    triggered = True
                elif condition == '==' and value == threshold:
                    triggered = True
                elif condition == '!=' and value != threshold:
                    triggered = True
                elif condition == 'change':
                    # Check if value changed
                    prev_key = f"var:{variable}:prev"
                    prev_json = self.redis_client.get(prev_key)
                    if prev_json:
                        prev_value = json.loads(prev_json)['value']
                        if value != prev_value:
                            triggered = True
                    self.redis_client.set(prev_key, value_json)
                    
                if triggered:
                    await self.execute_trigger_action(action, trigger_config, value)
                    
            await asyncio.sleep(0.1)  # Check at 10Hz
            
    async def execute_trigger_action(self, action: str, trigger_config: Dict, value: Any):
        """Execute trigger action"""
        timestamp = datetime.now().isoformat()
        
        if action == 'log':
            logger.info(f"Trigger fired: {trigger_config['variable']} = {value}")
            
        elif action == 'alert':
            await self.broadcast_to_ui({
                'type': 'alert',
                'message': f"Trigger: {trigger_config['variable']} {trigger_config['condition']} {trigger_config.get('threshold')}",
                'value': value,
                'timestamp': timestamp
            })
            
        elif action == 'capture':
            # Capture all variables at trigger point
            snapshot = await self.capture_snapshot()
            await self.broadcast_to_ui({
                'type': 'snapshot_captured',
                'trigger': trigger_config,
                'snapshot': snapshot,
                'timestamp': timestamp
            })
            
        elif action == 'stop':
            # Request target halt
            await self.send_to_mcp({
                'type': 'halt_target',
                'reason': f"Trigger: {trigger_config}"
            })
            
    async def capture_snapshot(self) -> Dict:
        """Capture current state of all variables"""
        snapshot = {}
        
        # Get all variable keys from Redis
        keys = self.redis_client.keys("var:*:latest")
        
        for key in keys:
            var_name = key.split(':')[1]
            value_json = self.redis_client.get(key)
            if value_json:
                snapshot[var_name] = json.loads(value_json)
                
        return snapshot
        
    async def export_data(self, export_config: Dict):
        """Export data in requested format"""
        format_type = export_config.get('format', 'csv')
        variables = export_config.get('variables', [])
        time_range = export_config.get('time_range')
        
        export_data = {}
        
        for var in variables:
            history_key = f"var:{var}:history"
            history = self.redis_client.lrange(history_key, 0, -1)
            
            export_data[var] = [json.loads(h) for h in history]
            
        if format_type == 'csv':
            csv_content = self.export_to_csv(export_data)
            filename = f"debug_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        elif format_type == 'json':
            json_content = json.dumps(export_data, indent=2)
            filename = f"debug_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        elif format_type == 'matlab':
            mat_content = self.export_to_matlab(export_data)
            filename = f"debug_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mat"
            
        # Send to UI for download
        await self.broadcast_to_ui({
            'type': 'export_ready',
            'filename': filename,
            'content': csv_content if format_type == 'csv' else json_content
        })
        
    def export_to_csv(self, data: Dict) -> str:
        """Convert data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = ['timestamp'] + list(data.keys())
        writer.writerow(headers)
        
        # Combine all timestamps
        all_timestamps = set()
        for var_data in data.values():
            for point in var_data:
                all_timestamps.add(point['timestamp'])
                
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # Write rows
        for ts in sorted_timestamps:
            row = [ts]
            for var in data.keys():
                value = None
                for point in data[var]:
                    if point['timestamp'] == ts:
                        value = point['value']
                        break
                row.append(value if value is not None else '')
            writer.writerow(row)
            
        return output.getvalue()
        
    def export_to_matlab(self, data: Dict) -> bytes:
        """Convert data to MATLAB format"""
        try:
            import scipy.io
            import io
            
            mat_data = {}
            for var_name, var_data in data.items():
                timestamps = [p['timestamp'] for p in var_data]
                values = [p['value'] for p in var_data]
                
                # Clean variable name for MATLAB
                clean_name = var_name.replace('.', '_').replace('[', '_').replace(']', '')
                
                mat_data[clean_name] = {
                    'time': np.array(timestamps),
                    'value': np.array(values)
                }
                
            output = io.BytesIO()
            scipy.io.savemat(output, mat_data)
            return output.getvalue()
            
        except ImportError:
            logger.error("scipy not installed for MATLAB export")
            return b''
            
    async def send_to_mcp(self, message: Dict):
        """Send message to MCP server"""
        async with websockets.connect('ws://localhost:3001/bridge-to-mcp') as ws:
            await ws.send(json.dumps(message))


async def main():
    """Main entry point"""
    bridge = MCPDashBridge()
    await bridge.start_bridge()
    

if __name__ == "__main__":
    asyncio.run(main())