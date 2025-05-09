import os

import logging
import re
from typing import Optional

try:
    import huggingface_hub
except ImportError:
    os.system("pip install huggingface_hub")
    
import requests
from tqdm.auto import tqdm

_MODELS = {
    "tiny.en": "Systran/faster-whisper-tiny.en",
    "tiny": "Systran/faster-whisper-tiny",
    "base.en": "Systran/faster-whisper-base.en",
    "base": "Systran/faster-whisper-base",
    "small.en": "Systran/faster-whisper-small.en",
    "small": "Systran/faster-whisper-small",
    "medium.en": "Systran/faster-whisper-medium.en",
    "medium": "Systran/faster-whisper-medium",
    "large-v1": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
    "large": "Systran/faster-whisper-large-v3",
    "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
    "distil-medium.en": "Systran/faster-distil-whisper-medium.en",
    "distil-small.en": "Systran/faster-distil-whisper-small.en",
    "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
    "large-v3-turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    "turbo": "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
}

def get_logger():
    """Returns the module logger."""
    return logging.getLogger("faster_whisper")

class disabled_tqdm(tqdm):
    def __init__(self, *args, **kwargs):
        kwargs["disable"] = True
        super().__init__(*args, **kwargs)

def download_model(
    size_or_id: str,
    output_dir: Optional[str] = None,
    local_files_only: bool = False,
    cache_dir: Optional[str] = None,
):
    """Downloads a CTranslate2 Whisper model from the Hugging Face Hub.

    Args:
      size_or_id: Size of the model to download from https://huggingface.co/Systran
        (tiny, tiny.en, base, base.en, small, small.en, distil-small.en, medium, medium.en,
        distil-medium.en, large-v1, large-v2, large-v3, large, distil-large-v2,
        distil-large-v3), or a CTranslate2-converted model ID from the Hugging Face Hub
        (e.g. Systran/faster-whisper-large-v3).
      output_dir: Directory where the model should be saved. If not set, the model is saved in
        the cache directory.
      local_files_only:  If True, avoid downloading the file and return the path to the local
        cached file if it exists.
      cache_dir: Path to the folder where cached files are stored.

    Returns:
      The path to the downloaded model.

    Raises:
      ValueError: if the model size is invalid.
    """
    if re.match(r".*/.*", size_or_id):
        repo_id = size_or_id
    else:
        repo_id = _MODELS.get(size_or_id)
        if repo_id is None:
            raise ValueError(
                "Invalid model size '%s', expected one of: %s"
                % (size_or_id, ", ".join(_MODELS.keys()))
            )

    allow_patterns = [
        "config.json",
        "preprocessor_config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.*",
    ]

    kwargs = {
        "local_files_only": local_files_only,
        "allow_patterns": allow_patterns,
        "tqdm_class": disabled_tqdm,
    }

    if output_dir is not None:
        kwargs["local_dir"] = output_dir

    if cache_dir is not None:
        kwargs["cache_dir"] = cache_dir

    try:
        return huggingface_hub.snapshot_download(repo_id, **kwargs)
    except (
        huggingface_hub.utils.HfHubHTTPError,
        requests.exceptions.ConnectionError,
    ) as exception:
        logger = get_logger()
        logger.warning(
            "An error occurred while synchronizing the model %s from the Hugging Face Hub:\n%s",
            repo_id,
            exception,
        )
        logger.warning(
            "Trying to load the model directly from the local cache, if it exists."
        )

        kwargs["local_files_only"] = True
        return huggingface_hub.snapshot_download(repo_id, **kwargs)


if not os.path.exists('./api/app/whisper'):
    model_size = "tiny" # tiny, base, small, medium, large-v2, large-v3
    download_model(model_size, "./api/app/whisper")

print("Model Downloaded")