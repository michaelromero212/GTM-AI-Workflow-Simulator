"""
GTM-focused prompt templates for AI agent
Company context is configurable via COMPANY_CONTEXT env var.
"""
import os

# Configurable company context (defaults to generic GTM language)
COMPANY_CONTEXT = os.getenv("COMPANY_CONTEXT", "your organization")

# System prompts for different task types
SYSTEM_PROMPTS = {
    "lead_summary": f"""You are an AI assistant helping Sales Development Representatives (SDRs) qualify and research leads.

Your role:
- Summarize lead information concisely
- Identify industry fit and use case potential
- Suggest relevant qualification questions
- Recommend next steps

Constraints:
- Never fabricate data or quotes
- If information is incomplete, say so explicitly
- Stay within documented product capabilities
- Escalate pricing, legal, or executive topics

Output format:
- Company Overview (2-3 sentences)
- Industry & Use Case Fit
- Suggested Qualification Questions (2-3)
- Recommended Next Steps
- Confidence: [High/Medium/Low]
""",

    "follow_up": f"""You are an AI assistant helping Account Executives (AEs) with customer follow-ups.

Your role:
- Suggest personalized follow-up actions based on last interaction
- Recommend relevant resources (case studies, docs, proof points)
- Provide timeline guidance for next engagement

Constraints:
- Never write final customer communications (provide drafts only)
- Don't make product commitments or roadmap promises
- Escalate if legal, pricing, or executive involvement needed

Output format:
- Follow-Up Action (email, call, meeting)
- Key Message Points (2-3 bullets)
- Resources to Share (links or titles)
- Timing Recommendation
- Confidence: [High/Medium/Low]
""",

    "risk_analysis": f"""You are an AI assistant helping sales teams identify and mitigate deal risks.

Your role:
- Analyze deal health based on activity patterns and engagement
- Identify risk signals (stalled deals, missing stakeholders, etc.)
- Suggest mitigation actions
- Recommend escalation if needed

Constraints:
- Base analysis only on provided data
- Don't speculate on customer intent without evidence
- Escalate high-risk scenarios to manager review

Output format:
- Risk Level: [Low/Medium/High]
- Key Risk Signals (bullet list)
- Suggested Mitigation Actions (2-3)
- Escalation Recommendation (if applicable)
- Confidence: [High/Medium/Low]
""",

    "data_hygiene": f"""You are an AI assistant helping Sales Operations maintain CRM data quality.

Your role:
- Identify incomplete or outdated CRM records
- Suggest data enrichment opportunities
- Flag duplicate records
- Validate contact information completeness

Constraints:
- Never update CRM fields autonomously
- Only flag issues, don't fix them
- Respect data privacy guidelines

Output format:
- Data Quality Issues (bullet list)
- Suggested Enrichments
- Priority Level: [High/Medium/Low]
- Confidence: [High/Medium/Low]
"""
}

# User prompt templates
USER_PROMPT_TEMPLATES = {
    "lead_summary": """Lead Information:
Name: {lead_name}
Company: {company_name}
Industry: {industry}
Source: {source}
Context: {additional_context}

Please provide a lead summary following the specified format.""",

    "follow_up": """Last Interaction Summary:
Customer: {customer_name}
Date: {interaction_date}
Type: {interaction_type}
Summary: {summary}
Current Deal Stage: {deal_stage}

Please suggest follow-up actions following the specified format.""",

    "risk_analysis": """Deal Information:
Deal Name: {deal_name}
Stage: {deal_stage}
Last Activity: {last_activity_date}
Recent Engagement: {engagement_summary}
Stakeholders: {stakeholders}

Please analyze deal risk following the specified format.""",

    "data_hygiene": """CRM Record:
Record Type: {record_type}
Record Name: {record_name}
Current Fields: {fields_present}
Missing Fields: {fields_missing}

Please analyze data quality following the specified format."""
}

# Escalation patterns - agent should refuse these
ESCALATION_PATTERNS = [
    # Pricing and discounting
    r"(?i)(pricing|discount|price reduction|how much|cost)",
    # Legal and compliance
    r"(?i)(legal|contract|BAA|DPA|compliance|security questionnaire|NDA)",
    # Executive decisions
    r"(?i)(should we|is this strategic|prioritize|executive)",
    # Product roadmap
    r"(?i)(roadmap|when will|future feature|upcoming release)",
    # Competitive deep-dives requiring sales expertise
    r"(?i)(beat|compete with|vs competitor|displacement)",
]

ESCALATION_RESPONSE = """⚠️ **This query requires human expertise**

**Recommended Action**: {escalation_type}

**Reason**: {reason}

**Suggested Owner**: {owner}

Please consult with the appropriate team member for this decision.
"""

ESCALATION_TYPES = {
    "pricing": {
        "escalation_type": "Consult with Sales Manager",
        "reason": "Pricing and discount decisions require manager approval",
        "owner": "Your Sales Manager"
    },
    "legal": {
        "escalation_type": "Consult with Legal Team",
        "reason": "Legal and compliance topics require legal review",
        "owner": "Legal Department"
    },
    "executive": {
        "escalation_type": "Consult with Leadership",
        "reason": "Strategic decisions require executive input",
        "owner": "Sales Leadership"
    },
    "technical": {
        "escalation_type": "Consult with Solutions Engineer",
        "reason": "Technical depth beyond documented capabilities",
        "owner": "Solutions Engineering Team"
    },
    "roadmap": {
        "escalation_type": "Consult with Product Team",
        "reason": "Product roadmap questions require product team input",
        "owner": "Product Management"
    }
}

# Fallback responses when HF_TOKEN not available
MOCK_RESPONSES = {
    "lead_summary": """**Company Overview**
{company_name} is a mid-market organization in the {industry} sector, with potential fit for modern data platform and AI capabilities.

**Industry & Use Case Fit**
- Likely use cases: Data analytics, real-time data streaming, ML/AI workloads
- Industry fit: Moderate to strong based on data-intensive operations

**Suggested Qualification Questions**
1. What are your current data infrastructure challenges?
2. Are you currently using cloud data platforms or streaming technologies?
3. Do you have active ML/AI initiatives or real-time data needs?

**Recommended Next Steps**
- Schedule discovery call within 24-48 hours
- Research company tech stack (LinkedIn, job postings)
- Prepare industry-specific use cases

**Confidence**: Medium (mock response - enable HF_TOKEN for real analysis)
""",

    "follow_up": """**Follow-Up Action**
Send personalized follow-up email within 24 hours

**Key Message Points**
- Thank customer for their time during last interaction
- Reference specific topics discussed
- Propose clear next steps with timeline

**Resources to Share**
- Relevant case study for their industry
- Product documentation aligned with their use case
- Suggested meeting agenda for next conversation

**Timing Recommendation**
Reach out within 24 hours, propose next meeting within 3-5 business days

**Confidence**: Medium (mock response - enable HF_TOKEN for real analysis)
""",

    "risk_analysis": """**Risk Level**: Medium

**Key Risk Signals**
- Extended period without customer engagement
- Missing key stakeholder involvement
- Unclear next steps or timeline

**Suggested Mitigation Actions**
1. Re-engage via multi-threaded outreach (email + LinkedIn)
2. Offer value-add resources (case study, technical whitepaper)
3. Propose executive briefing or ROI workshop

**Escalation Recommendation**
If no response within 3-5 business days, consider manager involvement to assess deal viability

**Confidence**: Medium (mock response - enable HF_TOKEN for real analysis)
""",

    "data_hygiene": """**Data Quality Issues**
- Incomplete contact information
- Missing industry or company size fields
- Outdated last activity timestamp

**Suggested Enrichments**
- Update from LinkedIn for role and company info
- Cross-reference with ZoomInfo or similar tools
- Validate email deliverability

**Priority Level**: Medium

**Confidence**: Medium (mock response - enable HF_TOKEN for real analysis)
"""
}


def get_system_prompt(task_type: str) -> str:
    """Get system prompt for a given task type"""
    return SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS["lead_summary"])


def get_user_prompt(task_type: str, **kwargs) -> str:
    """Build user prompt from template and parameters"""
    template = USER_PROMPT_TEMPLATES.get(task_type, "")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error building prompt: missing parameter {e}"


def get_mock_response(task_type: str, **kwargs) -> str:
    """Get mock response when LLM is not available"""
    template = MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["lead_summary"])
    try:
        return template.format(**kwargs)
    except KeyError:
        # If formatting fails, return template as-is
        return template
