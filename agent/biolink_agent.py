"""
BioLink Agent Integration with Microsoft Foundry
Connects your existing Azure agent with BioLink API tools
"""

import os
import asyncio
import httpx
from typing import Annotated
from agent_framework.azure import AzureAIClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

# =============================================================================
# CONFIGURATION - Update these with your Azure/Foundry details
# =============================================================================
PROJECT_ENDPOINT = os.environ.get(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://omar-ahmed-abdelhamiid-resource.services.ai.azure.com/api/projects/abdelhamiid-1153",
)
MODEL_DEPLOYMENT = os.environ.get("FOUNDRY_DEPLOYMENT", "gpt-5-nano")
AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "Agent797")

# BioLink API base URL (local development)
BIOLINK_API = "http://localhost:3001/api"

# =============================================================================
# BIOLINK API TOOLS - These functions will be available to your agent
# =============================================================================

async def search_patients(
    search: Annotated[str, "Search by DNA ID, nationality, or city"] = "",
    gender: Annotated[str, "Filter by gender (Male/Female)"] = "",
    age_min: Annotated[int, "Minimum age filter"] = None,
    age_max: Annotated[int, "Maximum age filter"] = None,
    limit: Annotated[int, "Number of results (max 100)"] = 20
) -> str:
    """Search and filter patients in the BioLink registry."""
    async with httpx.AsyncClient() as client:
        params = {
            "page": 1,
            "limit": limit,
            "sortBy": "dna_id",
            "sortOrder": "asc"
        }
        if search:
            params["search"] = search
        if gender:
            params["gender"] = gender
        if age_min:
            params["ageMin"] = age_min
        if age_max:
            params["ageMax"] = age_max
            
        try:
            response = await client.get(f"{BIOLINK_API}/patients", params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get('success'):
                return f"Error: {data.get('error', 'Failed to fetch patients')}"

            patients = data.get('data', [])
            pagination = data.get('pagination', {})
            total = pagination.get('total', len(patients) if isinstance(patients, list) else 0)

            # Format response
            result = f"Found {total} patients matching criteria.\n\n"
            for patient in (patients[:5] if isinstance(patients, list) else []):
                result += f"- {patient.get('dna_id')}: {patient.get('gender', 'N/A')}, Age {patient.get('age', 'N/A')}, "
                result += f"{patient.get('nationality', 'Unknown')} from {patient.get('current_city', 'Unknown')}\n"

            if total > 5:
                result += f"\n...and {total - 5} more patients"

            return result
        except Exception as e:
            return f"Error searching patients: {str(e)}"


async def get_patient_details(
    dna_id: Annotated[str, "Patient DNA ID (e.g., EHV001)"]
) -> str:
    """Get complete clinical details for a specific patient."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BIOLINK_API}/patients/{dna_id}")
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                return f"Patient {dna_id} not found"

            patient = data.get('data', {})
            
            # Format detailed response
            result = f"Patient Details for {dna_id}:\n\n"
            result += f"Demographics:\n"
            result += f"  - Age: {patient.get('age')} years\n"
            result += f"  - Gender: {patient.get('gender')}\n"
            result += f"  - Nationality: {patient.get('nationality')}\n"
            result += f"  - City: {patient.get('current_city')}\n\n"
            
            # Physical examination
            if patient.get('physical'):
                phys = patient['physical']
                result += f"Physical Examination:\n"
                result += f"  - BMI: {phys.get('bmi')}\n"
                result += f"  - Blood Pressure: {phys.get('systolic_bp')}/{phys.get('diastolic_bp')} mmHg\n"
                result += f"  - Heart Rate: {phys.get('heart_rate')} bpm\n\n"
            
            # Medical history
            if patient.get('medical'):
                med = patient['medical']
                conditions = []
                if med.get('high_blood_pressure'):
                    conditions.append("Hypertension")
                if med.get('diabetes_mellitus'):
                    conditions.append("Diabetes")
                if med.get('dyslipidemia'):
                    conditions.append("Dyslipidemia")
                if conditions:
                    result += f"Medical Conditions: {', '.join(conditions)}\n\n"
            
            # Imaging
            has_echo = patient.get('echo') and not patient['echo'].get('missing_echo')
            has_mri = patient.get('mri') and not patient['mri'].get('missing_mri')
            if has_echo or has_mri:
                result += f"Imaging Available: "
                imaging = []
                if has_echo:
                    imaging.append(f"Echo (EF: {patient['echo'].get('ef')}%)")
                if has_mri:
                    imaging.append(f"MRI (LVEF: {patient['mri'].get('lv_ejection_fraction')}%)")
                result += ", ".join(imaging) + "\n"
            
            return result
        except Exception as e:
            return f"Error fetching patient details: {str(e)}"


async def build_cohort(
    age_min: Annotated[int, "Minimum age"] = None,
    age_max: Annotated[int, "Maximum age"] = None,
    gender: Annotated[str, "Gender filter"] = "",
    has_diabetes: Annotated[bool, "Filter for diabetes patients"] = None,
    has_hypertension: Annotated[bool, "Filter for hypertension patients"] = None,
    has_echo: Annotated[bool, "Require echocardiogram data"] = None,
    has_mri: Annotated[bool, "Require MRI data"] = None,
    limit: Annotated[int, "Max results"] = 100
) -> str:
    """Build a patient cohort based on clinical criteria."""
    async with httpx.AsyncClient() as client:
        # Build POST body based on provided criteria
        body = {}
        if age_min is not None:
            body["ageMin"] = age_min
        if age_max is not None:
            body["ageMax"] = age_max
        if gender:
            body["gender"] = [gender]
        if has_diabetes is not None:
            body["hasDiabetes"] = has_diabetes
        if has_hypertension is not None:
            body["hasHypertension"] = has_hypertension
        if has_echo is not None:
            body["hasEcho"] = has_echo
        if has_mri is not None:
            body["hasMri"] = has_mri

        try:
            response = await client.post(f"{BIOLINK_API}/cohort/query", json=body)
            response.raise_for_status()
            data = response.json()

            if not data.get('success'):
                return f"Error: {data.get('error', 'Failed to build cohort')}"

            payload = data.get('data', {})
            cohort = payload.get('patients', [])
            total = payload.get('totalCount', len(cohort))

            result = f"Cohort built with {total} patients\n\n"
            result += "Criteria applied:\n"
            if age_min or age_max:
                result += f"  - Age range: {age_min or 'any'} to {age_max or 'any'}\n"
            if gender:
                result += f"  - Gender: {gender}\n"
            if has_diabetes is not None:
                result += f"  - Diabetes: {'Yes' if has_diabetes else 'No'}\n"
            if has_hypertension is not None:
                result += f"  - Hypertension: {'Yes' if has_hypertension else 'No'}\n"
            if has_echo is not None:
                result += f"  - Echo data: {'Required' if has_echo else 'Excluded'}\n"
            if has_mri is not None:
                result += f"  - MRI data: {'Required' if has_mri else 'Excluded'}\n"

            return result
        except Exception as e:
            return f"Error building cohort: {str(e)}"


async def get_registry_statistics() -> str:
    """Get comprehensive registry overview statistics and analytics."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BIOLINK_API}/analytics/overview")
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                return "Error fetching registry statistics"
            
            stats = data.get('data', {})
            
            result = "Registry Statistics:\n\n"
            result += f"Total Patients: {stats.get('totalPatients', 0)}\n"
            result += f"Male: {stats.get('maleCount', 0)}, Female: {stats.get('femaleCount', 0)}\n"
            result += f"Average Age: {stats.get('averageAge', 'N/A')} years\n"
            result += f"Data Completeness: {stats.get('dataCompleteness', 'N/A')}%\n\n"
            result += f"Imaging Data Available:\n"
            result += f"  - Echo: {stats.get('withEcho', 0)} patients\n"
            result += f"  - MRI: {stats.get('withMri', 0)} patients\n"
            result += f"  - ECG: {stats.get('withEcg', 0)} patients\n"
            
            return result
        except Exception as e:
            return f"Error fetching statistics: {str(e)}"


async def get_demographics_analysis() -> str:
    """Get demographics breakdown: age groups, nationality, marital status."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BIOLINK_API}/analytics/demographics")
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                return "Error fetching demographics"
            demo = data.get("data", {})
            age_gender = demo.get("ageGender", [])
            nationality = demo.get("nationality", [])
            marital = demo.get("maritalStatus", [])

            lines = ["Demographics Analysis:\n"]
            lines.append("Age Groups (Male/Female):")
            for g in age_gender:
                lines.append(
                    f"  - {g.get('age_group')}: M {g.get('male', 0)}, F {g.get('female', 0)}"
                )
            lines.append("\nTop Nationalities:")
            for n in nationality[:10]:
                lines.append(f"  - {n.get('nationality')}: {n.get('count')} patients")
            if marital:
                lines.append("\nMarital Status:")
                for m in marital:
                    lines.append(f"  - {m.get('marital_status')}: {m.get('count')} patients")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching demographics: {str(e)}"


async def get_enrollment_trends() -> str:
    """Get monthly enrollment trends with cumulative counts."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BIOLINK_API}/analytics/enrollment-trends")
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                return "Error fetching enrollment trends"
            trends = data.get("data", [])
            lines = ["Enrollment Trends:"]
            for t in trends:
                lines.append(
                    f"  - {t.get('month')}: enrolled {t.get('enrolled')}, cumulative {t.get('cumulative')}"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching enrollment trends: {str(e)}"


async def get_data_intersections() -> str:
    """Get counts of patients by data intersections (Echo/MRI/ECG combos)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BIOLINK_API}/analytics/data-intersections")
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                return "Error fetching data intersections"
            items = data.get("data", [])
            lines = ["Data Intersections:"]
            for it in items:
                lines.append(f"  - {it.get('combination')}: {it.get('count')} patients")
            return "\n".join(lines)
        except Exception as e:
            return f"Error fetching data intersections: {str(e)}"


# =============================================================================
# MAIN AGENT SETUP
# =============================================================================

async def main():
    """Main function to run the BioLink agent"""
    
    print("🚀 Starting BioLink Agent...")
    # Sanitize endpoint if user pasted a model/resource endpoint
    endpoint = PROJECT_ENDPOINT.rstrip("/")
    if endpoint.endswith("/models"):
        print("⚠️  Detected a model resource endpoint; adjusting to project endpoint")
        endpoint = endpoint[: -len("/models")]
    print(f"📍 Project: {endpoint}")
    print(f"🤖 Agent: {AGENT_NAME}")
    print(f"🔗 API: {BIOLINK_API}\n")
    
    # Connect to your existing Azure agent and add tools
    async with (
        DefaultAzureCredential() as credential,
        AzureAIClient(
            project_endpoint=endpoint,
            model_deployment_name=MODEL_DEPLOYMENT,
            credential=credential,
        ).create_agent(
            name=AGENT_NAME,
            instructions="""You are a helpful medical research assistant with access to the BioLink patient registry.
            
You can:
- Search for patients by various criteria
- Get detailed clinical information for specific patients
- Build cohorts based on demographics and clinical conditions
- Provide registry statistics and analytics

Always provide clear, professional responses. When showing patient data, respect privacy and only show relevant information requested by the user.""",
            tools=[
                search_patients,
                get_patient_details,
                build_cohort,
                get_registry_statistics,
                get_demographics_analysis,
                get_enrollment_trends,
                get_data_intersections
            ],
        ) as agent,
    ):
        print("✅ Agent connected successfully!\n")
        print("=" * 60)
        print("Ask me anything about the BioLink registry!")
        print("Examples:")
        print("  - Find patients with diabetes over 60")
        print("  - Get details for patient EHV001")
        print("  - Show me registry statistics")
        print("  - Build a cohort of hypertensive females with MRI data")
        print("=" * 60)
        print("\nType 'quit' to exit\n")
        
        # Create a thread for the conversation
        thread = agent.get_new_thread()
        
        # Interactive loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Stream the agent's response
            print("Agent: ", end="", flush=True)
            try:
                async for chunk in agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                print("\n")
            except ResourceNotFoundError:
                print("\n❌ Resource not found. Please verify:")
                print("   - Project Endpoint (Foundry Project settings)")
                print("   - Model Deployment name (Foundry Deployments)")
                print("   - Agent name exists in the project (or let the client create it)")
                print("   Tip: set env vars FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_DEPLOYMENT.")
                break
            except ServiceRequestError as e:
                print(f"\n❌ Service request error: {e}")
                print("   Check network connectivity and endpoint correctness.")
                break


if __name__ == "__main__":
    asyncio.run(main())
