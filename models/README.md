# Models Directory

This directory contains AI model configurations and definitions.

## Files

- `Modelfile` - Ollama model configuration for the medical AI assistant

## Usage

The Modelfile defines a custom Ollama model based on `alibayram/medgemma:4b` with specialized cardiovascular disease modeling capabilities.

To use this model:

```bash
# Build the model
ollama create biolink-medical -f models/Modelfile

# Run the model
ollama run biolink-medical
```

## Model Details

- **Base Model**: alibayram/medgemma:4b
- **Specialization**: Cardiovascular disease modeling and computational biology
- **Capabilities**: Patient cohort analysis, epigenomics integration, ML architecture suggestions