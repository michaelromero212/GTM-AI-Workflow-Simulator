"""
AI Agent implementation with Hugging Face LLM integration
"""
import os
import re
import time
from typing import Optional, Dict, Any
import requests
from prompts import (
    get_system_prompt,
    get_user_prompt,
    get_mock_response,
    ESCALATION_PATTERNS,
    ESCALATION_RESPONSE,
    ESCALATION_TYPES
)


class GTMAgent:
    """
    AI Agent for GTM Operations
    Supports lead summary, follow-up suggestions, risk analysis, and data hygiene tasks
    """
    
    def __init__(self, hf_token: Optional[str] = None, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        """
        Initialize the agent
        
        Args:
            hf_token: Hugging Face API token (optional, will use mock responses if not provided)
            model: Hugging Face model to use
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.model = model
        # Use the new Hugging Face router endpoint (api-inference.huggingface.co is deprecated)
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else None
        
    def _should_escalate(self, query: str) -> Optional[Dict[str, str]]:
        """
        Check if query matches escalation patterns
        
        Returns:
            Dict with escalation info if should escalate, None otherwise
        """
        query_lower = query.lower()
        
        # Check each escalation pattern
        if any(re.search(pattern, query) for pattern in ESCALATION_PATTERNS):
            # Determine escalation type
            if re.search(r"(?i)(pricing|discount|price|cost)", query):
                return ESCALATION_TYPES["pricing"]
            elif re.search(r"(?i)(legal|contract|BAA|DPA|compliance|security questionnaire)", query):
                return ESCALATION_TYPES["legal"]
            elif re.search(r"(?i)(should we|is this strategic|prioritize|executive)", query):
                return ESCALATION_TYPES["executive"]
            elif re.search(r"(?i)(roadmap|when will|future feature|upcoming)", query):
                return ESCALATION_TYPES["roadmap"]
            else:
                return ESCALATION_TYPES["technical"]
        
        return None
    
    def _call_hf_api(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Call Hugging Face Inference API using OpenAI-compatible chat completions format
        
        Args:
            prompt: Full prompt to send
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text or None if error
        """
        if not self.hf_token:
            return None
        
        # Use the new OpenAI-compatible chat completions endpoint
        api_url = "https://router.huggingface.co/v1/chat/completions"
        
        # Parse the prompt to extract system and user messages
        # The prompt format is: <s>[INST] {system}\n\n{user} [/INST]
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                # OpenAI format returns choices[0].message.content
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0].get("message", {}).get("content", "").strip()
                return None
            elif response.status_code == 503:
                # Model loading, wait and retry once
                time.sleep(10)
                response = requests.post(
                    api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0].get("message", {}).get("content", "").strip()
            else:
                print(f"Hugging Face API error: {response.status_code} - {response.text[:200]}")
            
            return None
            
        except Exception as e:
            print(f"Error calling Hugging Face API: {e}")
            return None
    
    def process_task(
        self,
        task_type: str,
        user_id: str,
        **task_params
    ) -> Dict[str, Any]:
        """
        Process a GTM task
        
        Args:
            task_type: Type of task (lead_summary, follow_up, risk_analysis, data_hygiene)
            user_id: User identifier
            **task_params: Task-specific parameters
            
        Returns:
            Dict with response, metadata, and metrics
        """
        start_time = time.time()
        
        # Build prompts
        system_prompt = get_system_prompt(task_type)
        user_prompt = get_user_prompt(task_type, **task_params)
        
        # Check for escalation patterns
        full_context = f"{user_prompt} {str(task_params)}"
        escalation_info = self._should_escalate(full_context)
        
        if escalation_info:
            # Should escalate to human
            response_text = ESCALATION_RESPONSE.format(**escalation_info)
            abstained = True
            confidence = "escalation"
        else:
            # Attempt LLM generation
            full_prompt = f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]"
            response_text = self._call_hf_api(full_prompt)
            
            if response_text is None:
                # Fall back to mock response
                response_text = get_mock_response(task_type, **task_params)
                response_text += "\n\n_Note: Using mock response. Set HF_TOKEN environment variable to enable real LLM._"
            
            abstained = False
            
            # Extract confidence if present
            confidence = "medium"
            if "Confidence: High" in response_text or "Confidence: high" in response_text:
                confidence = "high"
            elif "Confidence: Low" in response_text or "Confidence: low" in response_text:
                confidence = "low"
        
        resolution_time = time.time() - start_time
        
        return {
            "response": response_text,
            "task_type": task_type,
            "user_id": user_id,
            "abstained": abstained,
            "confidence": confidence,
            "resolution_time_seconds": round(resolution_time, 2),
            "model_used": self.model if self.hf_token else "mock",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


# Convenience function for quick testing
def demo_agent():
    """Demo the agent with sample tasks"""
    agent = GTMAgent()
    
    print("=" * 60)
    print("GTM AI Agent Demo")
    print("=" * 60)
    
    # Demo 1: Lead Summary
    print("\n📋 Task: Lead Summary")
    result = agent.process_task(
        task_type="lead_summary",
        user_id="demo_user",
        lead_name="Jane Smith",
        company_name="Acme Financial Services",
        industry="Banking",
        source="AWS Marketplace",
        additional_context="Visited pricing page twice this week"
    )
    print(f"\n{result['response']}")
    print(f"\n⏱️  Resolution time: {result['resolution_time_seconds']}s")
    print(f"🎯 Confidence: {result['confidence']}")
    print(f"🤖 Model: {result['model_used']}")
    
    # Demo 2: Follow-up
    print("\n" + "=" * 60)
    print("📧 Task: Follow-Up Suggestion")
    result = agent.process_task(
        task_type="follow_up",
        user_id="demo_user",
        customer_name="Acme Corp",
        interaction_date="2026-01-10",
        interaction_type="Product Demo",
        summary="Showed lakehouse architecture, CTO very engaged",
        deal_stage="Stage 2: Technical Validation"
    )
    print(f"\n{result['response']}")
    print(f"\n⏱️  Resolution time: {result['resolution_time_seconds']}s")
    
    # Demo 3: Escalation (pricing question)
    print("\n" + "=" * 60)
    print("⚠️  Task: Escalation Test (Pricing)")
    result = agent.process_task(
        task_type="follow_up",
        user_id="demo_user",
        customer_name="Acme Corp",
        interaction_date="2026-01-10",
        interaction_type="Pricing Discussion",
        summary="Customer asking for 40% discount",
        deal_stage="Stage 3: Negotiation"
    )
    print(f"\n{result['response']}")
    print(f"\n🚫 Abstained: {result['abstained']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo_agent()
