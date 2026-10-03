import os
import json
from google import genai
from google.genai import types
from agent.tools import check_duplicate_complaints, create_grievance_ticket, link_to_existing_grievance
from dotenv import load_dotenv

load_dotenv()

class GrievanceAgent:
    def __init__(self):
        # Initialize the Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            self.client = None
            print("Warning: GEMINI_API_KEY is not set or invalid. Agent will run in fallback/demo mode.")
        else:
            self.client = genai.Client(api_key=api_key)
            # You can now change the model name in your .env file
            self.model_id = os.environ.get("MODEL_NAME", "gemini-3.1-pro")

    def run(self, student_id: str, complaint_text: str, location: str):
        """
        Main execution loop for the agent.
        """
        if not self.client:
            return self._fallback_mode(student_id, complaint_text, location)

        system_instruction = """
        You are the CampusCare AI, an intelligent college grievance resolution agent.
        Your job is to read a student's complaint, understand it, and process it using the provided tools.
        
        Follow this strict process:
        1. Classify the complaint into exactly one of these categories: Academic, Examination, Hostel, Finance, IT, Library, Transport, Facilities, Security, Other.
        2. Assess Priority (Low, Medium, High, Critical) based on safety, people affected, duration, and service interruption.
        3. Route to a Department (Hostel Administration, IT Support, Finance Office, Examination Cell, Library Administration, Maintenance Department, Security Office, General Administration).
        4. Check for duplicate complaints using the check_duplicate_complaints tool.
        5. If a highly similar ongoing duplicate exists (is_duplicate=True), use the link_to_existing_grievance tool.
        6. If no duplicate exists, create a new ticket using the create_grievance_ticket tool.
        
        Always explain your reasoning concisely before making the final decision.
        """
        
        # Define the tools (functions) available to the model
        tools = [
            check_duplicate_complaints,
            create_grievance_ticket,
            link_to_existing_grievance
        ]
        
        # Tool configuration for the model
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.1
        )
        
        prompt = f"Student ID: {student_id}\nLocation: {location}\nComplaint: {complaint_text}\n\nAnalyze this complaint and take the appropriate action."
        
        # We start a chat session for tool calling
        chat = self.client.chats.create(model=self.model_id, config=config)
        
        response = chat.send_message(prompt)
        
        # Handle the function calls (if the model decides to use them)
        action_result = None
        final_ticket_info = None
        
        # The model might need a few turns if it chains tool calls (e.g., check_duplicate -> create_ticket)
        for _ in range(3): # Max 3 turns to prevent infinite loops
            if response.function_calls:
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args
                    
                    if name == "check_duplicate_complaints":
                        result = check_duplicate_complaints(**args)
                    elif name == "create_grievance_ticket":
                        result = create_grievance_ticket(**args)
                        final_ticket_info = result
                        # We also capture the AI's internal reasoning from the args
                        final_ticket_info['ai_reason'] = args.get('ai_reason', 'Processed by AI Agent')
                        final_ticket_info['category'] = args.get('category', 'Unknown')
                        final_ticket_info['priority'] = args.get('priority', 'Unknown')
                        final_ticket_info['department'] = args.get('department', 'Unknown')
                    elif name == "link_to_existing_grievance":
                        result = link_to_existing_grievance(**args)
                        final_ticket_info = result
                        final_ticket_info['ai_reason'] = "Linked to duplicate issue."
                        final_ticket_info['category'] = 'N/A'
                        final_ticket_info['priority'] = 'N/A'
                        final_ticket_info['department'] = 'N/A'
                    
                    # Send tool result back to the model
                    response = chat.send_message(types.Part.from_function_response(
                        name=name,
                        response={"result": result}
                    ))
            else:
                break
                
        # If no tool was called to create/link a ticket, fallback (failsafe)
        if not final_ticket_info:
            return self._fallback_mode(student_id, complaint_text, location)
            
        return {
            "ticket_info": final_ticket_info,
            "agent_response": response.text
        }
        
    def _fallback_mode(self, student_id: str, complaint_text: str, location: str):
        """Fallback mode for when API is unavailable or fails."""
        text_lower = complaint_text.lower()
        
        # Simple heuristic classification covering all categories
        if "wi-fi" in text_lower or "internet" in text_lower or "network" in text_lower or "wifi" in text_lower or "server" in text_lower:
            category = "IT"
            department = "IT Support"
        elif "hostel" in text_lower or "room" in text_lower or "electricity" in text_lower or "water supply" in text_lower or "mess" in text_lower:
            category = "Hostel"
            department = "Hostel Administration"
        elif "fee" in text_lower or "payment" in text_lower or "refund" in text_lower or "scholarship" in text_lower:
            category = "Finance"
            department = "Finance Office"
        elif "exam" in text_lower or "hall ticket" in text_lower or "result" in text_lower or "marksheet" in text_lower:
            category = "Examination"
            department = "Examination Cell"
        elif "library" in text_lower or "book" in text_lower or "library card" in text_lower:
            category = "Library"
            department = "Library Administration"
        elif "bus" in text_lower or "transport" in text_lower or "shuttle" in text_lower:
            category = "Transport"
            department = "General Administration"
        elif "projector" in text_lower or "chair" in text_lower or "fan" in text_lower or "classroom" in text_lower or "lab" in text_lower:
            category = "Facilities"
            department = "Maintenance Department"
        elif "security" in text_lower or "theft" in text_lower or "safety" in text_lower or "guard" in text_lower:
            category = "Security"
            department = "Security Office"
        elif "professor" in text_lower or "lecture" in text_lower or "attendance" in text_lower or "syllabus" in text_lower:
            category = "Academic"
            department = "General Administration"
        else:
            category = "Other"
            department = "General Administration"
            
        # Priority assessment based on keywords
        if "safety" in text_lower or "fire" in text_lower or "flood" in text_lower or "theft" in text_lower or "emergency" in text_lower:
            priority = "Critical"
        elif "since" in text_lower or "urgent" in text_lower or "not working" in text_lower or "broken" in text_lower or "50" in text_lower:
            priority = "High"
        elif "slow" in text_lower or "minor" in text_lower or "replacement" in text_lower:
            priority = "Low"
        else:
            priority = "Medium"
            
        reason = f"[Fallback Mode] Classified as {category} ({priority} priority). Routed to {department}."
        
        # Check duplicate manually
        dup_check = check_duplicate_complaints(complaint_text, category)
        if dup_check.get("is_duplicate"):
            res = link_to_existing_grievance(student_id, complaint_text, dup_check["ticket_id"])
            res['category'] = category
            res['priority'] = priority
            res['department'] = department
            res['ai_reason'] = reason
            return {"ticket_info": res, "agent_response": "Processed using fallback mode."}
            
        # Create ticket
        res = create_grievance_ticket(
            student_id=student_id, 
            complaint_text=complaint_text, 
            category=category, 
            priority=priority, 
            department=department, 
            location=location, 
            ai_reason=reason
        )
        res['category'] = category
        res['priority'] = priority
        res['department'] = department
        res['ai_reason'] = reason
        
        return {
            "ticket_info": res,
            "agent_response": "Processed using deterministic fallback mode (No API Key detected)."
        }
