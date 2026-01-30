import os
from datetime import datetime
import json

def get_log_filename():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'retrieval_service_{ts}.log'

class ToolLogger:
    def __init__(self, log_dir='.'):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, get_log_filename())

    def log_tool_call(self, tool_name, tool_input, tool_output):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'tool': tool_name,
            'input': tool_input,
            'output': tool_output
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, default=str) + '\n')

tool_logger = ToolLogger()
