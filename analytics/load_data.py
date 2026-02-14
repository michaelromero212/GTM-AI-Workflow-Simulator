"""
Data loading and database setup for analytics
Supports DuckDB with extended schema (workflow_stage, time_saved_minutes, prompt_version)
"""
import pandas as pd
import duckdb
from pathlib import Path


class DataLoader:
    """Load agent run data into DuckDB for analytics"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
    def load_csv_to_db(self, csv_path: str, table_name: str = "agent_runs"):
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Ensure new columns exist (backward compat with old CSVs)
        if 'workflow_stage' not in df.columns:
            df['workflow_stage'] = 'Pipeline Generation'
        if 'time_saved_minutes' not in df.columns:
            df['time_saved_minutes'] = 0.0
        if 'prompt_version' not in df.columns:
            df['prompt_version'] = 'v1.0'
        
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM df
        """)
        return df
    
    def execute_query(self, query: str):
        return self.conn.execute(query).fetchdf()
    
    def get_summary_stats(self):
        query = """
        SELECT 
            COUNT(*) as total_runs,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT task_type) as task_types,
            AVG(resolution_time_seconds) as avg_resolution_time,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as acceptance_rate,
            AVG(user_rating) as avg_rating,
            AVG(CASE WHEN abstained THEN 1.0 ELSE 0.0 END) * 100 as abstention_rate,
            AVG(CASE WHEN error_occurred THEN 1.0 ELSE 0.0 END) * 100 as error_rate,
            SUM(time_saved_minutes) as total_time_saved,
            ROUND(SUM(time_saved_minutes) / 60.0, 1) as total_hours_saved
        FROM agent_runs
        """
        return self.execute_query(query)
    
    def get_metrics_by_version(self):
        query = """
        SELECT 
            agent_version,
            COUNT(*) as total_tasks,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct,
            AVG(user_rating) as avg_satisfaction,
            AVG(resolution_time_seconds) as avg_resolution_time,
            AVG(CASE WHEN error_occurred THEN 1.0 ELSE 0.0 END) * 100 as error_rate,
            AVG(CASE WHEN abstained THEN 1.0 ELSE 0.0 END) * 100 as abstention_rate
        FROM agent_runs
        GROUP BY agent_version
        ORDER BY agent_version
        """
        return self.execute_query(query)
    
    def get_metrics_by_task_type(self):
        query = """
        SELECT 
            task_type,
            COUNT(*) as total_tasks,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct,
            AVG(user_rating) as avg_satisfaction,
            AVG(resolution_time_seconds) as avg_resolution_time
        FROM agent_runs
        GROUP BY task_type
        ORDER BY total_tasks DESC
        """
        return self.execute_query(query)
    
    def get_daily_trends(self):
        query = """
        SELECT 
            STRFTIME(timestamp, '%Y-%m-%d') as date,
            COUNT(*) as total_tasks,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct,
            AVG(user_rating) as avg_satisfaction,
            COUNT(DISTINCT user_id) as active_users
        FROM agent_runs
        GROUP BY STRFTIME(timestamp, '%Y-%m-%d')
        ORDER BY date
        """
        return self.execute_query(query)
    
    def get_pipeline_funnel(self):
        """Get CRM stage distribution for funnel chart"""
        query = """
        SELECT 
            crm_stage,
            COUNT(*) as count,
            SUM(opportunity_value) as total_value,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct
        FROM agent_runs
        GROUP BY crm_stage
        ORDER BY 
            CASE crm_stage
                WHEN 'MQL' THEN 1
                WHEN 'SAL' THEN 2
                WHEN 'SQL' THEN 3
                WHEN 'Discovery' THEN 4
                WHEN 'Technical Validation' THEN 5
                WHEN 'Value/Impact' THEN 6
                WHEN 'Negotiation' THEN 7
                WHEN 'Closed Won' THEN 8
                WHEN 'Closed Lost' THEN 9
                ELSE 10
            END
        """
        return self.execute_query(query)
    
    def get_metrics_by_workflow_stage(self):
        """Get metrics grouped by GTM workflow stage"""
        query = """
        SELECT 
            workflow_stage,
            COUNT(*) as total_tasks,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct,
            ROUND(SUM(time_saved_minutes), 1) as total_time_saved,
            ROUND(AVG(time_saved_minutes), 1) as avg_time_saved,
            AVG(user_rating) as avg_satisfaction
        FROM agent_runs
        GROUP BY workflow_stage
        ORDER BY total_tasks DESC
        """
        return self.execute_query(query)
    
    def get_time_saved_summary(self):
        """Get time savings by task type"""
        query = """
        SELECT 
            task_type,
            COUNT(*) as total_runs,
            ROUND(SUM(time_saved_minutes), 1) as total_minutes_saved,
            ROUND(AVG(time_saved_minutes), 1) as avg_minutes_saved,
            ROUND(SUM(time_saved_minutes) / 60.0, 1) as total_hours_saved
        FROM agent_runs
        GROUP BY task_type
        ORDER BY total_minutes_saved DESC
        """
        return self.execute_query(query)
    
    def get_audit_log(self, limit=50, task_type=None, version=None, outcome=None):
        """Get audit log with optional filters"""
        where_clauses = []
        if task_type:
            where_clauses.append(f"task_type = '{task_type}'")
        if version:
            where_clauses.append(f"agent_version = '{version}'")
        if outcome == 'accepted':
            where_clauses.append("user_accepted = true")
        elif outcome == 'rejected':
            where_clauses.append("user_accepted = false")
        elif outcome == 'escalated':
            where_clauses.append("abstained = true")
        elif outcome == 'error':
            where_clauses.append("error_occurred = true")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            run_id, timestamp, user_id, task_type, agent_version,
            ROUND(resolution_time_seconds, 2) as resolution_time,
            CASE WHEN user_accepted THEN 'Accepted' ELSE 'Rejected' END as outcome,
            user_rating, abstained, error_occurred,
            lead_source, crm_stage, opportunity_value,
            workflow_stage, time_saved_minutes, prompt_version
        FROM agent_runs
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        return self.execute_query(query)
    
    def get_prompt_version_metrics(self):
        """Get performance by prompt version"""
        query = """
        SELECT 
            prompt_version,
            COUNT(*) as total_runs,
            AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100 as accuracy_pct,
            AVG(user_rating) as avg_satisfaction,
            AVG(resolution_time_seconds) as avg_resolution_time
        FROM agent_runs
        GROUP BY prompt_version
        ORDER BY prompt_version
        """
        return self.execute_query(query)
    
    def close(self):
        self.conn.close()


def main():
    """Demo the data loader"""
    data_dir = Path(__file__).parent.parent / "data"
    csv_file = data_dir / "sample_agent_runs.csv"
    
    if not csv_file.exists():
        print(f"❌ Sample data file not found: {csv_file}")
        return
    
    loader = DataLoader(":memory:")
    loader.load_csv_to_db(str(csv_file))
    
    print("\n" + "=" * 70)
    print("📊 OVERALL SUMMARY STATISTICS")
    print("=" * 70)
    summary = loader.get_summary_stats()
    print(summary.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("🔀 A/B TEST COMPARISON (Agent Version)")
    print("=" * 70)
    ab_comparison = loader.get_metrics_by_version()
    print(ab_comparison.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("📋 METRICS BY TASK TYPE")
    print("=" * 70)
    by_task = loader.get_metrics_by_task_type()
    print(by_task.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("🔄 METRICS BY WORKFLOW STAGE")
    print("=" * 70)
    by_workflow = loader.get_metrics_by_workflow_stage()
    print(by_workflow.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("⏱️  TIME SAVINGS BY TASK TYPE")
    print("=" * 70)
    time_saved = loader.get_time_saved_summary()
    print(time_saved.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("📈 PIPELINE FUNNEL")
    print("=" * 70)
    funnel = loader.get_pipeline_funnel()
    print(funnel.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("📅 DAILY TRENDS")
    print("=" * 70)
    trends = loader.get_daily_trends()
    print(trends.to_string(index=False))
    
    print("\n" + "=" * 70)
    print("🔖 PROMPT VERSION PERFORMANCE")
    print("=" * 70)
    pv = loader.get_prompt_version_metrics()
    print(pv.to_string(index=False))
    
    loader.close()
    print("\n✅ Analytics demo complete")


if __name__ == "__main__":
    main()
