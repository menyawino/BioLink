from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Optional, Callable
import operator
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import logging
import numpy as np
from sqlalchemy import text
import re

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    sql_query: Optional[str]
    sql_results: Optional[pd.DataFrame]
    plot_code: Optional[str]
    plot_data: Optional[str]  # base64 encoded image
    final_response: Optional[str]
    error: Optional[str]
    iteration_count: int

class SQLAgentService:
    def __init__(
        self,
        db_url: str,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "phi:latest",
        db: Optional[SQLDatabase] = None,
        llm: Optional[ChatOllama] = None,
        toolkit_factory: Optional[Callable[..., object]] = None,
    ):
        if db is None:
            try:
                self.db = SQLDatabase.from_uri(db_url, sample_rows_in_table_info=3)
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise Exception(f"Database connection failed: {e}")
        else:
            self.db = db

        if llm is None:
            try:
                self.llm = ChatOllama(base_url=ollama_base_url, model=model, temperature=0)
                logger.info(f"LLM initialized with model {model}")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise Exception(f"LLM initialization failed: {e}")
        else:
            self.llm = llm

        factory = toolkit_factory or SQLDatabaseToolkit
        self.toolkit = factory(db=self.db, llm=self.llm)
        self.graph = self._build_graph()
        logger.info("LangGraph agent initialized successfully")

    def validate_database(self) -> bool:
        """Validate that the database has the required tables and data"""
        try:
            # Check if patients table exists
            result = self.db.run("SELECT COUNT(*) FROM patients")
            # Handle different result formats from SQLDatabase
            if isinstance(result, str):
                # Parse string result like '[(0,)]'
                import ast
                try:
                    parsed = ast.literal_eval(result.strip())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        count = int(parsed[0][0])
                    else:
                        count = int(result.strip())
                except:
                    count = int(result.strip())
            else:
                count = int(result)
            logger.info(f"Database validation successful: {count} patients found")
            return True
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False

    def _build_graph(self):
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("query_router", self.query_router)
        graph.add_node("generate_sql", self.generate_sql)
        graph.add_node("execute_sql", self.execute_sql)
        graph.add_node("viz_decider", self.viz_decider)
        graph.add_node("generate_plot", self.generate_plot)
        graph.add_node("respond", self.respond)

        # Add edges
        graph.set_entry_point("query_router")

        # Conditional routing based on query analysis
        graph.add_conditional_edges(
            "query_router",
            self.route_based_on_analysis,
            {"sql": "generate_sql", "direct": "respond"}
        )
        graph.add_edge("generate_sql", "execute_sql")
        graph.add_conditional_edges(
            "execute_sql",
            self.should_visualize,
            {"visualize": "viz_decider", "no_viz": "respond"}
        )
        graph.add_edge("viz_decider", "generate_plot")
        graph.add_edge("generate_plot", "respond")
        graph.add_edge("respond", END)

        # Error handling edges
        graph.add_conditional_edges(
            "execute_sql",
            self.handle_sql_error,
            {"retry": "generate_sql", "fail": END}
        )

        return graph.compile()

    def query_router(self, state: AgentState) -> AgentState:
        """Route the query to determine if it needs SQL and/or visualization"""
        user_query = state["messages"][-1]["content"]
        
        # Simple heuristic-based routing to avoid LLM hanging
        query_lower = user_query.lower()
        
        # Check if this is clearly a database query
        db_keywords = ['patients', 'count', 'how many', 'average', 'mean', 'total', 'sum', 'min', 'max', 'group by', 'where', 'select', 'query', 'data', 'database', 'show', 'plot', 'graph', 'chart', 'distribution', 'histogram', 'visualize', 'display', 'age', 'gender', 'nationality', 'nationalities', 'list', 'what are', 'registry', 'records', 'entries']
        needs_sql = any(keyword in query_lower for keyword in db_keywords)
        
        # For now, if it's not clearly a DB query, respond directly
        if not needs_sql:
            state["final_response"] = "I can help you with patient data queries. Try asking about patient counts, averages, or specific data analysis."
            return state
        
        # Check if visualization would be beneficial
        viz_keywords = ['show', 'plot', 'graph', 'chart', 'distribution', 'histogram', 'scatter', 'bar chart', 'visualize', 'display']
        needs_viz = any(keyword in query_lower for keyword in viz_keywords)
        
        # Determine intent
        if 'count' in query_lower or 'how many' in query_lower:
            intent = "count query"
            needs_viz = False
        elif 'average' in query_lower or 'mean' in query_lower:
            intent = "aggregation query"
            needs_viz = False
        elif needs_viz:
            intent = "visualization query"
        else:
            intent = "data query"

        state["needs_sql"] = needs_sql
        state["needs_viz"] = needs_viz
        state["intent"] = intent
        return state

    def route_based_on_analysis(self, state: AgentState) -> str:
        """Route to SQL processing or direct response based on analysis"""
        if state.get("final_response"):
            return "direct"
        elif state.get("needs_sql", True):
            return "sql"
        else:
            return "direct"

    def generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL query from natural language"""
        user_query = state["messages"][-1]["content"]
        query_lower = user_query.lower()
        logger.info(f"Generating SQL for query: {query_lower}")

        # Fast-path heuristic SQL generation for common queries to avoid LLM timeouts
        heuristic_sql = self._heuristic_sql(query_lower)
        if heuristic_sql:
            state["sql_query"] = heuristic_sql
            logger.info(f"Heuristic SQL used: {heuristic_sql}")
            return state
        
        # Always use LLM to generate SQL
        table_info = self.db.get_table_info()

        prompt = f"""
        Generate a SQL query for this request. Use only SELECT statements, no modifications.
        Database schema:
        {table_info}

        Query: {user_query}

        Return only the SQL query, nothing else. Limit results to 1000 rows.
        Examples:
        - "How many patients?" -> SELECT COUNT(*) FROM patients
        - "Average age by gender" -> SELECT gender, AVG(age) FROM patients GROUP BY gender
        - "Patients with low EF" -> SELECT * FROM patients WHERE ef < 40 LIMIT 1000
        """

        try:
            response = self.llm.invoke(prompt)
            sql_query = response.content.strip()
        except Exception as e:
            logger.error(f"LLM error in generate_sql: {e}")
            state["error"] = f"Failed to generate SQL query: {str(e)}"
            return state

        state["sql_query"] = sql_query
        logger.info(f"Generated SQL: {sql_query}")
        return state

        # Validate SQL (basic check)
        if not self._validate_sql(sql_query):
            state["error"] = "Generated SQL query is invalid or unsafe"
            return state

        state["sql_query"] = sql_query
        return state

    def _heuristic_sql(self, query_lower: str) -> Optional[str]:
        """Return a simple SQL query for common prompts to keep responses fast."""
        if "how many" in query_lower or ("count" in query_lower and "patient" in query_lower):
            return "SELECT COUNT(*) AS count FROM EHVOL"

        if "average age" in query_lower:
            return "SELECT AVG(age) AS avg_age FROM EHVOL WHERE age IS NOT NULL"

        if "age distribution" in query_lower or ("age" in query_lower and "distribution" in query_lower):
            return "SELECT age FROM EHVOL WHERE age IS NOT NULL LIMIT 1000"

        if "count" in query_lower and "gender" in query_lower:
            return "SELECT gender, COUNT(*) AS count FROM EHVOL GROUP BY gender"

        if "average" in query_lower and "ef" in query_lower and ("male" in query_lower or "female" in query_lower):
            return "SELECT gender, AVG(ef) AS avg_ef FROM EHVOL WHERE ef IS NOT NULL GROUP BY gender"

        if "average" in query_lower and "ef" in query_lower:
            return "SELECT AVG(ef) AS avg_ef FROM EHVOL WHERE ef IS NOT NULL"

        return None

    def execute_sql(self, state: AgentState) -> AgentState:
        """Execute the SQL query and get results"""
        try:
            sql_query = state["sql_query"]
            result = self.db.run(sql_query)
            
            # Handle different result formats
            if result:
                result_str = result.strip()
                logger.info(f"SQL result: {result_str[:200]}...")
                
                # For aggregate queries (COUNT, AVG, SUM, etc.), parse the tuple format
                if any(func in sql_query.upper() for func in ['COUNT(', 'AVG(', 'SUM(', 'MIN(', 'MAX(']) and '(' in result_str:
                    try:
                        # Simple parsing for single aggregate results
                        if result_str.startswith('[(') and result_str.endswith(',)]'):
                            # Extract the value between [( and ,)]
                            value_str = result_str[2:-3]  # Remove '[(', ',)]'
                            try:
                                value = float(value_str)
                            except:
                                value = value_str.strip("'\"")

                            # Use generic column name
                            col_name = 'result'
                            df = pd.DataFrame([value], columns=[col_name])
                            logger.info(f"Parsed aggregate result: {df}")
                        else:
                            lines = result_str.split('\n')
                            if len(lines) > 1:
                                headers = [h.strip() for h in lines[0].split('|')]
                                data = [
                                    [cell.strip() for cell in line.split('|')]
                                    for line in lines[1:]
                                    if line.strip()
                                ]
                                df = pd.DataFrame(data, columns=headers)
                            else:
                                df = pd.DataFrame()
                    except Exception as e:
                        logger.error(f"Failed to parse aggregate result: {e}")
                        df = pd.DataFrame()
                else:
                    # Try to parse as list of tuples first (for simple SELECT queries)
                    try:
                        import ast
                        parsed_result = ast.literal_eval(result_str)
                        if isinstance(parsed_result, list) and len(parsed_result) > 0:
                            if isinstance(parsed_result[0], tuple):
                                # Convert list of tuples to DataFrame
                                if len(parsed_result[0]) == 1:
                                    # Single column
                                    df = pd.DataFrame([row[0] for row in parsed_result], columns=['result'])
                                else:
                                    # Multiple columns - use generic names
                                    df = pd.DataFrame(parsed_result, columns=[f'col_{i}' for i in range(len(parsed_result[0]))])
                                logger.info(f"Parsed tuple result: {df.shape}")
                            else:
                                df = pd.DataFrame()
                        else:
                            df = pd.DataFrame()
                    except Exception as e:
                        logger.error(f"Failed to parse result with ast: {e}, result_str: {result_str[:500]}")
                        # Fall back to table parsing
                        lines = result_str.split('\n')
                        if len(lines) > 1:
                            headers = lines[0].split('|')
                            data = [line.split('|') for line in lines[1:] if line.strip()]
                            df = pd.DataFrame(data, columns=headers)
                        else:
                            df = pd.DataFrame()
            else:
                df = pd.DataFrame()

            logger.info(f"Parsed DataFrame shape: {df.shape}")
            state["sql_results"] = df
            state["iteration_count"] = state.get("iteration_count", 0) + 1
            return state
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            state["error"] = str(e)
            return state

    def should_visualize(self, state: AgentState) -> str:
        """Decide if visualization is needed"""
        # Temporarily disable visualization to improve performance
        return "no_viz"
        # if state.get("needs_viz", False) and not state.get("sql_results", pd.DataFrame()).empty:
        #     return "visualize"
        # return "no_viz"

    def viz_decider(self, state: AgentState) -> AgentState:
        """Simple visualization decision - just pass through"""
        # For now, just set basic config and let generate_plot handle the logic
        state["viz_config"] = {
            "plot_type": "histogram",
            "title": "Data Visualization"
        }
        return state

    def generate_plot(self, state: AgentState) -> AgentState:
        """Generate a simple plot from the data"""
        try:
            df = state["sql_results"]
            user_query = state["messages"][-1]["content"]

            if df.empty:
                state["error"] = "No data available for plotting"
                return state

            # Simple plot generation based on query type
            query_lower = user_query.lower()

            plt.figure(figsize=(10, 6))

            if "age" in query_lower and "gender" in query_lower:
                # Age distribution by gender
                if "age" in df.columns and "gender" in df.columns:
                    df_clean = df.dropna(subset=["age", "gender"])
                    if not df_clean.empty:
                        df_clean["age"] = pd.to_numeric(df_clean["age"], errors="coerce")
                        plt.hist([df_clean[df_clean["gender"] == "Male"]["age"],
                                 df_clean[df_clean["gender"] == "Female"]["age"]],
                                label=["Male", "Female"], alpha=0.7)
                        plt.xlabel("Age")
                        plt.ylabel("Count")
                        plt.title("Age Distribution by Gender")
                        plt.legend()
                    else:
                        plt.text(0.5, 0.5, "No valid age/gender data", ha="center", va="center")
                else:
                    plt.text(0.5, 0.5, "Age or gender column not found", ha="center", va="center")

            elif "age" in query_lower:
                # Simple age distribution
                if "age" in df.columns:
                    df_clean = df.dropna(subset=["age"])
                    if not df_clean.empty:
                        df_clean["age"] = pd.to_numeric(df_clean["age"], errors="coerce")
                        plt.hist(df_clean["age"], bins=20, alpha=0.7)
                        plt.xlabel("Age")
                        plt.ylabel("Count")
                        plt.title("Age Distribution")
                    else:
                        plt.text(0.5, 0.5, "No valid age data", ha="center", va="center")
                else:
                    plt.text(0.5, 0.5, "Age column not found", ha="center", va="center")

            else:
                # Generic scatter plot if we have numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) >= 2:
                    plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
                    plt.xlabel(numeric_cols[0])
                    plt.ylabel(numeric_cols[1])
                    plt.title(f"{numeric_cols[0]} vs {numeric_cols[1]}")
                else:
                    plt.text(0.5, 0.5, "Not enough numeric data for plotting", ha="center", va="center")

            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()

            state["plot_data"] = image_base64
            logger.info("Plot generated successfully")
            return state

        except Exception as e:
            logger.error(f"Plot generation error: {e}")
            state["error"] = f"Failed to generate plot: {str(e)}"
            return state

    def respond(self, state: AgentState) -> AgentState:
        """Generate final natural language response"""
        # If response is already set, don't overwrite it
        if state.get("final_response"):
            return state
            
        user_query = state["messages"][-1]["content"]
        df = state.get("sql_results")
        plot_data = state.get("plot_data")
        error = state.get("error")

        if error:
            response = f"I encountered an error: {error}. Please try rephrasing your query."
        else:
            if df is not None and not df.empty:
                response = f"Query executed successfully. Here are the results:\n{df.head(10).to_string()}"
            else:
                response = "Query executed but returned no results."

            # Skip LLM summarization for now to avoid timeouts
            # TODO: Re-enable LLM summarization with faster model or caching

            if plot_data:
                response += f"\n\n![Data Visualization](data:image/png;base64,{plot_data})"

        state["final_response"] = response
        return state

    def handle_sql_error(self, state: AgentState) -> str:
        """Handle SQL execution errors"""
        if state.get("error") and state.get("iteration_count", 0) < 3:
            return "retry"
        return "fail"

    def _validate_sql(self, sql: str) -> bool:
        """Basic SQL validation"""
        sql = sql.upper().strip()
        # Only allow SELECT
        if not sql.startswith("SELECT"):
            return False
        # No dangerous keywords
        dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for word in dangerous:
            if word in sql:
                return False
        return True

    async def run(self, message: str, history: List[dict] = None) -> str:
        """Run the agent on a user message"""
        if history is None:
            history = []

        messages = history + [{"role": "user", "content": message}]

        initial_state = {
            "messages": messages,
            "sql_query": None,
            "sql_results": None,
            "plot_code": None,
            "plot_data": None,
            "final_response": None,
            "error": None,
            "iteration_count": 0
        }

        try:
            # Run synchronous graph.invoke in a thread since we're in async context
            import asyncio
            result = await asyncio.to_thread(self.graph.invoke, initial_state)
            response = result.get("final_response", "I couldn't process your request.")
            
            # Log the result for debugging
            logger.info(f"Agent response: {response[:200]}...")
            
            return response
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try rephrasing your question."