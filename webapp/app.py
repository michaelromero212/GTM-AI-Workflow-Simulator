"""
FastAPI Web Application for AI Agent Operations Dashboard
Premium GTM Ops Platform with live data and SQL Explorer
"""
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
import csv
import uuid
from datetime import datetime
from typing import Optional

# Add agent and analytics to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))
sys.path.insert(0, str(Path(__file__).parent.parent / "analytics"))

from agent import GTMAgent
from load_data import DataLoader

app = FastAPI(title="GTM Ops Platform")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize agent
agent = GTMAgent()

# Data file path
data_file = Path(__file__).parent.parent / "data" / "sample_agent_runs.csv"


def log_agent_run(task_type: str, user_id: str, resolution_time: float, 
                  abstained: bool, error: bool, user_accepted: bool = True, 
                  user_rating: int = 4):
    """Append a new agent run to the CSV file for live updates"""
    run_id = f"WEB{datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_row = {
        'run_id': run_id,
        'timestamp': timestamp,
        'user_id': user_id,
        'task_type': task_type,
        'agent_version': 'A',
        'resolution_time_seconds': round(resolution_time, 2),
        'user_accepted': user_accepted,
        'user_rating': user_rating,
        'abstained': abstained,
        'error_occurred': error,
        'lead_source': 'Web Upload',
        'crm_stage': 'Discovery',
        'opportunity_value': 0
    }
    
    # Append to CSV
    with open(data_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_row.keys())
        writer.writerow(new_row)
    
    return run_id


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page - Operational Hub with real insights"""
    loader = DataLoader(":memory:")
    
    try:
        loader.load_csv_to_db(str(data_file))
        
        summary_df = loader.get_summary_stats()
        
        by_source_query = """
        SELECT lead_source, 
               COUNT(*) as volume, 
               ROUND(AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy 
        FROM agent_runs 
        GROUP BY lead_source 
        ORDER BY accuracy DESC
        """
        by_source_df = loader.execute_query(by_source_query)
        
        recent_query = """
        SELECT task_type, user_id, 
               CASE WHEN user_accepted THEN 'Accepted' ELSE 'Rejected' END as outcome,
               resolution_time_seconds,
               timestamp
        FROM agent_runs 
        ORDER BY timestamp DESC 
        LIMIT 5
        """
        recent_df = loader.execute_query(recent_query)
        
        ab_df = loader.get_metrics_by_version()
        
        loader.close()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "summary": summary_df.iloc[0].to_dict() if not summary_df.empty else None,
            "top_sources": by_source_df.head(3).to_dict('records'),
            "low_sources": by_source_df.tail(2).to_dict('records'),
            "recent_activity": recent_df.to_dict('records'),
            "ab_comparison": ab_df.to_dict('records'),
            "error": None
        })
    except Exception as e:
        loader.close()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": str(e)
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """KPI Dashboard with interactive charts"""
    loader = DataLoader(":memory:")
    
    try:
        loader.load_csv_to_db(str(data_file))
        
        summary_df = loader.get_summary_stats()
        by_version_df = loader.get_metrics_by_version()
        by_task_df = loader.get_metrics_by_task_type()
        trends_df = loader.get_daily_trends()
        
        by_source_query = """
        SELECT lead_source, COUNT(*) as volume, 
               ROUND(AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy 
        FROM agent_runs GROUP BY lead_source ORDER BY accuracy DESC
        """
        by_source_df = loader.execute_query(by_source_query)
        
        loader.close()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "summary": summary_df.iloc[0].to_dict() if not summary_df.empty else None,
            "ab_comparison": by_version_df.to_dict('records'),
            "by_task": by_task_df.to_dict('records'),
            "by_source": by_source_df.to_dict('records'),
            "trends": trends_df.to_dict('records'),
            "error": None
        })
    except Exception as e:
        loader.close()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "error": str(e)
        })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """File upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    task_type: str = Form(...)
):
    """Handle file upload, process with agent, and log to database"""
    try:
        contents = await file.read()
        text_content = contents.decode('utf-8')
        
        # Save uploaded file
        upload_dir = Path(__file__).parent.parent / "data" / "uploaded_inputs"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_file = upload_dir / f"{timestamp}_{file.filename}"
        
        with open(saved_file, 'wb') as f:
            f.write(contents)
        
        # Process with agent
        result = agent.process_task(
            task_type=task_type,
            user_id="web_user",
            lead_name="Uploaded Lead",
            company_name="From File",
            industry="Unknown",
            source="Web Upload",
            additional_context=text_content[:1000]
        )
        
        # LOG THE RUN TO CSV (Live Loop!)
        log_agent_run(
            task_type=task_type,
            user_id="web_user",
            resolution_time=result['resolution_time_seconds'],
            abstained=result['abstained'],
            error=False
        )
        
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "success": True,
            "filename": file.filename,
            "result": result['response'],
            "confidence": result['confidence'],
            "resolution_time": result['resolution_time_seconds']
        })
        
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": str(e)
        })


@app.get("/explorer", response_class=HTMLResponse)
async def explorer_page(request: Request):
    """Operational Diagnostics page - allows PMs to audit agent performance and logs"""
    return templates.TemplateResponse("explorer.html", {"request": request})


@app.post("/explorer", response_class=HTMLResponse)
async def execute_query(request: Request, query: str = Form(...)):
    """Execute SQL query and return results"""
    loader = DataLoader(":memory:")
    
    try:
        loader.load_csv_to_db(str(data_file))
        
        # Basic SQL injection prevention - only allow SELECT
        clean_query = query.strip()
        if not clean_query.upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Block dangerous keywords
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
        for keyword in dangerous:
            if keyword in clean_query.upper():
                raise ValueError(f"Unsafe keyword detected: {keyword}")
        
        result_df = loader.execute_query(clean_query)
        loader.close()
        
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "query": query,
            "columns": list(result_df.columns),
            "results": result_df.to_dict('records'),
            "error": None
        })
        
    except Exception as e:
        loader.close()
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "query": query,
            "error": str(e)
        })


@app.post("/agent/query")
async def agent_query(
    request: Request,
    task_type: str = Form(...),
    lead_name: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    additional_context: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
    interaction_date: Optional[str] = Form(None),
    interaction_type: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    deal_stage: Optional[str] = Form(None),
    deal_name: Optional[str] = Form(None),
    last_activity_date: Optional[str] = Form(None),
    engagement_summary: Optional[str] = Form(None),
    stakeholders: Optional[str] = Form(None)
):
    """Process agent query"""
    try:
        kwargs = {}
        
        if task_type == "lead_summary":
            kwargs = {
                "lead_name": lead_name or "Unknown",
                "company_name": company_name or "Unknown",
                "industry": industry or "Unknown",
                "source": source or "Manual Entry",
                "additional_context": additional_context or "No additional context"
            }
        elif task_type == "follow_up":
            kwargs = {
                "customer_name": customer_name or "Unknown",
                "interaction_date": interaction_date or datetime.now().strftime("%Y-%m-%d"),
                "interaction_type": interaction_type or "General",
                "summary": summary or "No summary provided",
                "deal_stage": deal_stage or "Unknown"
            }
        elif task_type == "risk_analysis":
            kwargs = {
                "deal_name": deal_name or "Unknown Deal",
                "deal_stage": deal_stage or "Unknown",
                "last_activity_date": last_activity_date or datetime.now().strftime("%Y-%m-%d"),
                "engagement_summary": engagement_summary or "No engagement data",
                "stakeholders": stakeholders or "Unknown"
            }
        
        result = agent.process_task(
            task_type=task_type,
            user_id="web_user",
            **kwargs
        )
        
        # Log the run
        log_agent_run(
            task_type=task_type,
            user_id="web_user",
            resolution_time=result['resolution_time_seconds'],
            abstained=result['abstained'],
            error=False
        )
        
        return {
            "success": True,
            "response": result['response'],
            "confidence": result['confidence'],
            "resolution_time": result['resolution_time_seconds'],
            "abstained": result['abstained']
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
