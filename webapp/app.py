"""
FastAPI Web Application for AI Agent Operations Dashboard
Premium GTM Ops Platform with live data, SQL Explorer, Workflow Builder, and Audit Log
"""
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sys
import csv
import uuid
from datetime import datetime
from typing import Optional

# Add agent and analytics to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "agent"))
sys.path.insert(0, str(ROOT_DIR / "analytics"))

from agent import GTMAgent
from load_data import DataLoader

app = FastAPI(title="GTM AI Ops Platform")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Initialize agent and data
agent = GTMAgent()
data_path = ROOT_DIR / "data" / "sample_agent_runs.csv"


def get_loader():
    """Get a fresh DataLoader instance with latest data"""
    loader = DataLoader(":memory:")
    if data_path.exists():
        loader.load_csv_to_db(str(data_path))
    return loader


def log_agent_run(run_data: dict):
    """Append a new agent run to the CSV"""
    csv_path = str(data_path)
    fieldnames = [
        "run_id", "timestamp", "user_id", "task_type", "agent_version",
        "resolution_time_seconds", "user_accepted", "user_rating", "abstained",
        "error_occurred", "lead_source", "crm_stage", "opportunity_value",
        "workflow_stage", "time_saved_minutes", "prompt_version"
    ]
    file_exists = data_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(run_data)


# ──────────────────────── API ENDPOINTS ────────────────────────


@app.get("/api/ai-status")
async def ai_status():
    """Check AI/LLM connection health by pinging the Hugging Face API"""
    import time as _time
    import requests as _requests

    # No token configured
    if not agent.hf_token:
        return JSONResponse({
            "status": "no_token",
            "model": agent.model,
            "message": "No HF_TOKEN configured — agent uses mock responses",
            "latency_ms": None
        })

    # Attempt a lightweight API call
    try:
        start = _time.time()
        resp = _requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {agent.hf_token}"},
            json={
                "model": agent.model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            },
            timeout=15,
        )
        latency = round((_time.time() - start) * 1000)

        if resp.status_code == 200:
            return JSONResponse({
                "status": "connected",
                "model": agent.model,
                "message": "LLM is responding",
                "latency_ms": latency
            })
        else:
            return JSONResponse({
                "status": "disconnected",
                "model": agent.model,
                "message": f"API returned {resp.status_code}: {resp.text[:120]}",
                "latency_ms": latency
            })
    except Exception as exc:
        return JSONResponse({
            "status": "disconnected",
            "model": agent.model,
            "message": str(exc)[:150],
            "latency_ms": None
        })


# ──────────────────────── ROUTES ────────────────────────


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Performance Overview page"""
    try:
        loader = get_loader()
        summary = loader.get_summary_stats()
        by_task = loader.get_metrics_by_task_type()
        by_version = loader.get_metrics_by_version()
        trends = loader.get_daily_trends()
        time_saved = loader.get_time_saved_summary()
        
        summary_dict = summary.to_dict('records')[0] if len(summary) > 0 else {}
        task_data = by_task.to_dict('records')
        version_data = by_version.to_dict('records')
        trend_data = trends.to_dict('records')
        time_saved_data = time_saved.to_dict('records')
        
        loader.close()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "summary": summary_dict,
            "by_task": task_data,
            "by_version": version_data,
            "trends": trend_data,
            "time_saved": time_saved_data,
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "summary": None,
            "error": str(e)
        })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, page: int = 1, per_page: int = 15):
    """KPI Dashboard page"""
    try:
        loader = get_loader()
        summary = loader.get_summary_stats()
        by_task = loader.get_metrics_by_task_type()
        by_version = loader.get_metrics_by_version()
        trends = loader.get_daily_trends()
        funnel = loader.get_pipeline_funnel()
        
        summary_dict = summary.to_dict('records')[0] if len(summary) > 0 else {}
        task_data = by_task.to_dict('records')
        version_data = by_version.to_dict('records')
        trend_data = trends.to_dict('records')
        funnel_data = funnel.to_dict('records')
        
        # Paginated runs
        all_runs = loader.execute_query(
            "SELECT * FROM agent_runs ORDER BY timestamp DESC"
        )
        total_runs = len(all_runs)
        total_pages = max(1, (total_runs + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        runs_page = all_runs.iloc[start_idx:end_idx].to_dict('records')
        
        loader.close()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "summary": summary_dict,
            "by_task": task_data,
            "by_version": version_data,
            "trends": trend_data,
            "funnel": funnel_data,
            "runs": runs_page,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page,
            "total_runs": total_runs,
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "summary": None,
            "error": str(e)
        })


@app.get("/workflow", response_class=HTMLResponse)
async def workflow(request: Request):
    """Workflow Builder page"""
    try:
        loader = get_loader()
        workflow_metrics = loader.get_metrics_by_workflow_stage()
        time_saved = loader.get_time_saved_summary()
        summary = loader.get_summary_stats()
        
        wf_data = workflow_metrics.to_dict('records')
        ts_total = time_saved.to_dict('records')
        summary_dict = summary.to_dict('records')[0] if len(summary) > 0 else {}
        
        # Aggregate time saved
        total_minutes = sum(row.get('total_minutes_saved', 0) for row in ts_total)
        total_hours = round(total_minutes / 60.0, 1)
        total_runs = sum(row.get('total_runs', 0) for row in ts_total)
        
        loader.close()
        
        return templates.TemplateResponse("workflow.html", {
            "request": request,
            "workflow_metrics": wf_data,
            "time_saved": {
                "total_minutes_saved": total_minutes,
                "total_hours_saved": total_hours,
                "total_runs": total_runs
            },
            "total_runs": summary_dict.get('total_runs', 0),
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("workflow.html", {
            "request": request,
            "workflow_metrics": None,
            "time_saved": None,
            "total_runs": 0,
            "error": str(e)
        })


@app.get("/audit", response_class=HTMLResponse)
async def audit(request: Request, task_type: str = "", version: str = "", outcome: str = ""):
    """Governance & Audit Log page"""
    try:
        loader = get_loader()
        summary = loader.get_summary_stats()
        prompt_versions = loader.get_prompt_version_metrics()
        audit_log = loader.get_audit_log(
            limit=100,
            task_type=task_type or None,
            version=version or None,
            outcome=outcome or None
        )
        
        summary_dict = summary.to_dict('records')[0] if len(summary) > 0 else {}
        pv_data = prompt_versions.to_dict('records')
        audit_data = audit_log.to_dict('records')
        
        loader.close()
        
        return templates.TemplateResponse("audit.html", {
            "request": request,
            "summary": summary_dict,
            "prompt_versions": pv_data,
            "audit_log": audit_data,
            "filters": {
                "task_type": task_type,
                "version": version,
                "outcome": outcome
            },
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("audit.html", {
            "request": request,
            "summary": None,
            "prompt_versions": None,
            "audit_log": None,
            "filters": {},
            "error": str(e)
        })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Agent Lab page (GET)"""
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "success": False,
        "error": None
    })


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, task_type: str = Form(...), file: UploadFile = File(...)):
    """Agent Lab - file upload processing"""
    try:
        # Validate file type
        allowed_extensions = {".csv", ".txt", ".json"}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "error": f"Invalid file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}",
                "success": False
            })
        
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8", errors="ignore")[:5000]
        
        # Save uploaded file
        upload_dir = ROOT_DIR / "data" / "uploaded_inputs"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        file_path = upload_dir / safe_name
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process with agent
        result = agent.process_task(
            task_type=task_type,
            user_id="web_upload",
            additional_context=text_content
        )
        
        # Log the run
        workflow_stages = {
            "lead_summary": "Pipeline Generation",
            "follow_up": "Deal Execution",
            "risk_analysis": "Deal Execution",
            "data_hygiene": "Onboarding & Adoption",
        }
        log_agent_run({
            "run_id": f"WEB{uuid.uuid4().hex[:6].upper()}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": "web_upload",
            "task_type": task_type,
            "agent_version": "A",
            "resolution_time_seconds": round(result.get("resolution_time_seconds", 0), 2),
            "user_accepted": True,
            "user_rating": 0,
            "abstained": result.get("abstained", False),
            "error_occurred": result.get("error", False),
            "lead_source": "Web Upload",
            "crm_stage": "SQL",
            "opportunity_value": 0,
            "workflow_stage": workflow_stages.get(task_type, "Pipeline Generation"),
            "time_saved_minutes": round(result.get("resolution_time_seconds", 0) * 3, 1),
            "prompt_version": "v2.0"
        })
        
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "success": True,
            "filename": file.filename,
            "result": result.get("response", "No response generated"),
            "confidence": result.get("confidence", "N/A"),
            "resolution_time": result.get("resolution_time_seconds", 0),
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": str(e),
            "success": False
        })


@app.post("/agent/query")
async def agent_query(
    request: Request,
    task_type: str = Form(...),
    # Lead Summary fields
    lead_name: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    additional_context: Optional[str] = Form(None),
    # Follow-up fields
    customer_name: Optional[str] = Form(None),
    interaction_date: Optional[str] = Form(None),
    interaction_type: Optional[str] = Form(None),
    deal_stage: Optional[str] = Form(None),
    summary: Optional[str] = Form(None),
    # Risk Analysis fields
    deal_name: Optional[str] = Form(None),
    last_activity_date: Optional[str] = Form(None),
    engagement_summary: Optional[str] = Form(None),
    stakeholders: Optional[str] = Form(None),
    # Data Hygiene fields
    record_type: Optional[str] = Form(None),
    record_name: Optional[str] = Form(None),
    fields_present: Optional[str] = Form(None),
    fields_missing: Optional[str] = Form(None),
):
    """Agent query endpoint - returns JSON for AJAX playground"""
    try:
        # Build kwargs based on task type
        kwargs = {}
        if task_type == "lead_summary":
            kwargs = {
                "lead_name": lead_name or "Unknown",
                "company_name": company_name or "Unknown",
                "industry": industry or "Unknown",
                "source": source or "Unknown",
                "additional_context": additional_context or ""
            }
        elif task_type == "follow_up":
            kwargs = {
                "customer_name": customer_name or "Unknown",
                "interaction_date": interaction_date or "Unknown",
                "interaction_type": interaction_type or "Unknown",
                "deal_stage": deal_stage or "Unknown",
                "summary": summary or ""
            }
        elif task_type == "risk_analysis":
            kwargs = {
                "deal_name": deal_name or "Unknown",
                "deal_stage": deal_stage or "Unknown",
                "last_activity_date": last_activity_date or "Unknown",
                "engagement_summary": engagement_summary or "",
                "stakeholders": stakeholders or "Unknown"
            }
        elif task_type == "data_hygiene":
            kwargs = {
                "record_type": record_type or "Unknown",
                "record_name": record_name or "Unknown",
                "fields_present": fields_present or "",
                "fields_missing": fields_missing or ""
            }
        
        # Process with agent
        result = agent.process_task(
            task_type=task_type,
            user_id="web_playground",
            **kwargs
        )
        
        # Log the run
        workflow_stages = {
            "lead_summary": "Pipeline Generation",
            "follow_up": "Deal Execution",
            "risk_analysis": "Deal Execution",
            "data_hygiene": "Onboarding & Adoption",
        }
        log_agent_run({
            "run_id": f"PLY{uuid.uuid4().hex[:6].upper()}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": "web_playground",
            "task_type": task_type,
            "agent_version": "A",
            "resolution_time_seconds": round(result.get("resolution_time_seconds", 0), 2),
            "user_accepted": True,
            "user_rating": 0,
            "abstained": result.get("abstained", False),
            "error_occurred": result.get("error", False),
            "lead_source": "Playground",
            "crm_stage": "SQL",
            "opportunity_value": 0,
            "workflow_stage": workflow_stages.get(task_type, "Pipeline Generation"),
            "time_saved_minutes": round(result.get("resolution_time_seconds", 0) * 3, 1),
            "prompt_version": "v2.0"
        })
        
        return JSONResponse({
            "success": True,
            "response": result.get("response", ""),
            "confidence": result.get("confidence", "N/A"),
            "resolution_time": result.get("resolution_time_seconds", 0),
            "abstained": result.get("abstained", False),
            "task_type": task_type
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/explorer", response_class=HTMLResponse)
async def explorer(request: Request):
    """Operational Diagnostics page"""
    try:
        loader = get_loader()
        
        # Get data catalog info
        schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agent_runs' ORDER BY ordinal_position"
        try:
            schema = loader.execute_query(schema_query)
            schema_data = schema.to_dict('records')
        except:
            schema_data = []
        
        # Get row count
        count = loader.execute_query("SELECT COUNT(*) as cnt FROM agent_runs")
        row_count = count.to_dict('records')[0]['cnt'] if len(count) > 0 else 0
        
        loader.close()
        
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "schema": schema_data,
            "row_count": row_count,
            "error": None
        })
    except Exception as e:
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "schema": [],
            "row_count": 0,
            "error": str(e)
        })


@app.post("/explorer/query", response_class=HTMLResponse)
async def run_query(request: Request, query: str = Form(...)):
    """Execute diagnostic query"""
    try:
        # Basic SQL injection protection
        forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
        upper_query = query.upper().strip()
        for word in forbidden:
            if word in upper_query:
                raise ValueError(f"Forbidden SQL keyword: {word}. Only SELECT queries allowed.")
        
        if not upper_query.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
        
        loader = get_loader()
        results = loader.execute_query(query)
        
        schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agent_runs' ORDER BY ordinal_position"
        try:
            schema = loader.execute_query(schema_query)
            schema_data = schema.to_dict('records')
        except:
            schema_data = []
        
        count = loader.execute_query("SELECT COUNT(*) as cnt FROM agent_runs")
        row_count = count.to_dict('records')[0]['cnt'] if len(count) > 0 else 0
        
        loader.close()
        
        columns = list(results.columns)
        rows = results.to_dict('records')
        
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "schema": schema_data,
            "row_count": row_count,
            "query": query,
            "columns": columns,
            "rows": rows,
            "result_count": len(rows),
            "error": None
        })
    except Exception as e:
        loader = get_loader()
        schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'agent_runs' ORDER BY ordinal_position"
        try:
            schema = loader.execute_query(schema_query)
            schema_data = schema.to_dict('records')
        except:
            schema_data = []
        count = loader.execute_query("SELECT COUNT(*) as cnt FROM agent_runs")
        row_count = count.to_dict('records')[0]['cnt'] if len(count) > 0 else 0
        loader.close()
        
        return templates.TemplateResponse("explorer.html", {
            "request": request,
            "schema": schema_data,
            "row_count": row_count,
            "query": query,
            "error": str(e)
        })
