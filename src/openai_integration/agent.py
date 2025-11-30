import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import os
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

from tools import TOOLS_SCHEMA, execute_function_call
from .prompts import get_system_prompt

load_dotenv()

class AppointmentAgent:
        
    def __init__(self, model: str = "gpt-4.1-nano", custom_prompt: Optional[str] = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.model = model
        self.conversation_history = []
        self.user_context = {
            "name": None,
            "email": None,
            "reason": None,
            "selected_appointment_id": None
        }
        
        system_prompt = custom_prompt if custom_prompt else get_system_prompt()
        self.conversation_history.append({
            "role": "system",
            "content": system_prompt
        })
    
    
    async def process_message(self, user_message: str) -> str:
        """Process message - now async to handle async tool calls"""
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if not tool_calls:
            assistant_message = response_message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            return assistant_message
        
        self.conversation_history.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"[DEBUG] Calling function: {function_name}")
            print(f"[DEBUG] Arguments: {json.dumps(function_args, indent=2)}")
            
            function_response = await execute_function_call(function_name, function_args)
            
            print(f"[DEBUG] Function response: {json.dumps(function_response, indent=2)}")
            
            if function_name == "collect_user_info":
                for key, value in function_args.items():
                    if value:
                        self.user_context[key] = value
            
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
        
        second_response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history
        )
        
        final_message = second_response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": final_message
        })
        
        return final_message
    
    def get_user_context(self) -> Dict:
        return self.user_context
    
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_history
    
    def reset_conversation(self):
        system_message = self.conversation_history[0]
        self.conversation_history = [system_message]
        self.user_context = {
            "name": None,
            "email": None,
            "reason": None,
            "selected_appointment_id": None
        }
    
    def export_conversation(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump({
                "conversation": self.conversation_history,
                "user_context": self.user_context
            }, f, indent=2)
    
    def update_system_prompt(self, new_prompt: str):
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = new_prompt
            print("[INFO] System prompt updated")


import asyncio

async def test_agent():
    """Test function - now async"""
    agent = AppointmentAgent()
    
    print("=== KVR Appointment Agent Test ===")
    print("Type 'quit' to exit, 'reset' to start over\n")
    
    print("Agent: Hello! This is KVR emergency appointment service. How can I help?\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("\nExporting conversation...")
            agent.export_conversation("conversation_log.json")
            print("Goodbye!")
            break
        
        if user_input.lower() == 'reset':
            agent.reset_conversation()
            print("Agent: Hello! This is KVR emergency appointment service. How can I help?\n")
            continue
        
        if user_input.lower() == 'context':
            print(f"\nCurrent context: {json.dumps(agent.get_user_context(), indent=2)}\n")
            continue
        
        if not user_input:
            continue
        
        try:
            response = await agent.process_message(user_input)
            print(f"Agent: {response}\n")
        except Exception as e:
            print(f"[ERROR] {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(test_agent())
