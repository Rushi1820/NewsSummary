import utils
from fastapi import FastAPI, APIRouter
import base64

router=APIRouter()


@router.get("/getcompanynews/{company}")
async def getcompanynews(company:str):

    results= utils.merge_results(company)
    hindi_audio_base64 = convert_to_hindi_audio(results["Coverage Differences"])
    
    results["Audio"] = hindi_audio_base64  # Add Base64 audio
    return results
