from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.backend.models.schemas import ErrorResponse
from app.backend.services.ollama_service import OllamaService
from app.backend.database.connection import get_db
from app.backend.repositories.api_key_repository import ApiKeyRepository
from src.llm.models import get_models_list, ModelProvider
from sqlalchemy.orm import Session

router = APIRouter(prefix="/language-models")

# Initialize Ollama service
ollama_service = OllamaService()

# Map provider names to API key provider names
PROVIDER_TO_API_KEY = {
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Google": "GOOGLE_API_KEY",
    "Groq": "GROQ_API_KEY",
    "xAI": "XAI_API_KEY",
    "DeepSeek": "DEEPSEEK_API_KEY",
    "GigaChat": "GIGACHAT_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "Azure OpenAI": "AZURE_OPENAI_API_KEY",
}

@router.get(
    path="/",
    responses={
        200: {"description": "List of available language models"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_language_models(db: Session = Depends(get_db)):
    """Get the list of available cloud-based and Ollama language models.
    
    Only returns models from providers that have API keys configured.
    """
    try:
        # Get all active API keys
        api_key_repo = ApiKeyRepository(db)
        api_keys = api_key_repo.get_all_api_keys(include_inactive=False)
        available_providers = {key.provider for key in api_keys}
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Available API key providers: {available_providers}")
        
        # Filter cloud models by available API keys
        all_models = get_models_list()
        filtered_models = []
        
        for model in all_models:
            provider = model.get("provider", "")
            # Check if API key exists for this provider
            api_key_name = PROVIDER_TO_API_KEY.get(provider)
            if api_key_name and api_key_name in available_providers:
                filtered_models.append(model)
                logger.debug(f"Including model {model.get('display_name')} from provider {provider} (API key: {api_key_name})")
            else:
                logger.debug(f"Excluding model {model.get('display_name')} from provider {provider} (API key: {api_key_name}, in available: {api_key_name in available_providers if api_key_name else False})")
        
        # Add available Ollama models (handles all checking internally)
        ollama_models = await ollama_service.get_available_models()
        filtered_models.extend(ollama_models)
        
        logger.info(f"Returning {len(filtered_models)} models (cloud: {len(filtered_models) - len(ollama_models)}, ollama: {len(ollama_models)})")
        return {"models": filtered_models}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_language_models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve models: {str(e)}")

@router.get(
    path="/providers",
    responses={
        200: {"description": "List of available model providers"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_language_model_providers():
    """Get the list of available model providers with their models grouped."""
    try:
        models = get_models_list()
        
        # Group models by provider
        providers = {}
        for model in models:
            provider_name = model["provider"]
            if provider_name not in providers:
                providers[provider_name] = {
                    "name": provider_name,
                    "models": []
                }
            providers[provider_name]["models"].append({
                "display_name": model["display_name"],
                "model_name": model["model_name"]
            })
        
        return {"providers": list(providers.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve providers: {str(e)}") 