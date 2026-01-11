# BioLink Development TODO

## Phase 1: Chat Interface Foundation ✅
- [x] Create chat UI component for landing page
- [x] Build backend endpoint for Azure chat service integration
- [x] Implement conversation history management
- [x] Add configuration for Azure endpoint/URI
- [x] Connect frontend to backend chat API

## Phase 2: Agent Tool Integration (PRIORITY)
Convert all existing functionalities into agent-accessible tools:

### Patient Management Tools
- [ ] `search_patients` - Search and filter patient registry
- [ ] `get_patient_profile` - Retrieve individual patient details
- [ ] `get_patient_vitals` - Get vital signs and measurements
- [ ] `get_patient_imaging` - Retrieve Echo/MRI data
- [ ] `export_patients` - Export patient data to CSV

### Cohort Builder Tools
- [ ] `build_cohort` - Create cohort with demographic filters
- [ ] `add_clinical_filters` - Apply clinical criteria
- [ ] `add_temporal_filters` - Apply enrollment date/duration filters
- [ ] `add_data_availability_filters` - Filter by required data types
- [ ] `get_cohort_estimate` - Get estimated patient count
- [ ] `execute_cohort_query` - Run cohort query and get results
- [ ] `export_cohort` - Export cohort to CSV/JSON

### Analytics Tools
- [ ] `get_registry_overview` - Get overview statistics
- [ ] `get_demographics_analysis` - Analyze demographics
- [ ] `get_clinical_metrics` - Get clinical distributions
- [ ] `get_geographic_distribution` - Analyze geographic data
- [ ] `get_enrollment_trends` - Get enrollment over time
- [ ] `get_data_quality_metrics` - Analyze data completeness

### Chart Builder Tools
- [ ] `create_chart` - Create custom visualization
- [ ] `get_available_fields` - List all chartable fields
- [ ] `get_chart_data` - Get aggregated data for charts
- [ ] `export_chart` - Export chart as image/data

### Data Dictionary Tools
- [ ] `search_data_dictionary` - Search variable definitions
- [ ] `get_field_metadata` - Get field statistics and descriptions
- [ ] `get_category_fields` - List fields by category

### Navigation Tools
- [ ] `navigate_to` - Navigate to different sections
- [ ] `open_patient_profile` - Open specific patient view
- [ ] `switch_view` - Change current view/component

## Phase 3: Agent System Prompt & Context
- [ ] Define comprehensive system prompt for the agent
- [ ] Create tool schemas for function calling
- [ ] Implement tool execution framework
- [ ] Add error handling and validation for tool calls
- [ ] Create response formatting for tool results

## Phase 4: Advanced Features
- [ ] Add streaming responses for chat
- [ ] Implement multi-turn conversation context
- [ ] Add chat history persistence
- [ ] Create conversation export functionality
- [ ] Add voice input/output (optional)

## Phase 5: Testing & Refinement
- [ ] Test all tool integrations
- [ ] Validate agent responses
- [ ] Optimize performance
- [ ] Add usage analytics
- [ ] Documentation for agent capabilities

---

**Current Focus**: Phase 1 - Chat Interface Foundation
**Next**: Phase 2 - Convert functionalities to agent tools
