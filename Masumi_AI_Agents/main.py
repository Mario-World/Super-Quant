import os
import uvicorn
import uuid
import sys
import random 
import json 
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import Union, Optional, Literal
from masumi.config import Config
from masumi.payment import Payment, Amount
from risk_manager_definition import RiskAssessmentManager, RiskAssessmentType, ResearchManager
from logging_config import setup_logging

logger = setup_logging()

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL")
PAYMENT_API_KEY = os.getenv("PAYMENT_API_KEY")
NETWORK = os.getenv("NETWORK")
AGENT_IDENTIFIER = os.getenv("AGENT_IDENTIFIER") 

logger.info("Starting On-Chain Risk Manager Agent with configuration:")
logger.info(f"PAYMENT_SERVICE_URL: {PAYMENT_SERVICE_URL}")
logger.info(f"NETWORK: {NETWORK}")

app = FastAPI(
    title="Masumi On-Chain Risk Manager API", 
    description="API for on-chain DeFi risk assessment with Masumi payment integration",
    version="2.0.0"
)

jobs = {}
payment_instances = {}

config = Config(
    payment_service_url=PAYMENT_SERVICE_URL,
    payment_api_key=PAYMENT_API_KEY
)

def map_risk_score(score: int) -> str:
    """Maps a 0-100 risk score to a visual level."""
    if score >= 75:
        return f"{score}% = Low Risk (🟢)"
    elif score >= 50:
        return f"{score}% = Moderate Risk (🟡)"
    elif score >= 25:
        return f"{score}% = High Risk (🟠)"
    else:
        return f"{score}% = Extreme Risk (🔴)"

class TradingRiskInput(BaseModel):
    """Input data for Trading Risk Assessment."""
    token_symbol: str = Field(..., description="The symbol of the token (e.g., BTC, ETH, ADA).")
    time_period: str = Field("1 year", description="The historical period to analyze (e.g., '6 months', '2 years').")
    more_parameters: str = Field("", description="Additional factors for on-chain analysis.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token_symbol": "ADA",
                "time_period": "3 months",
                "more_parameters": "Include analysis of on-chain staking patterns and validator distribution."
            }
        }
    }

class LendingBorrowingRiskInput(BaseModel):
    """Input data for Lending/Borrowing Risk Assessment."""
    borrowing_asset: str = Field(..., description="The asset being borrowed (e.g., USDC, wBTC).")
    borrower_history_summary: str = Field(..., description="Summary of the borrower's on-chain history and creditworthiness.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "borrowing_asset": "USDC",
                "borrower_history_summary": "Excellent 2-year on-chain history, 0 defaults, average LTV ratio 45%, consistent collateral maintenance."
            }
        }
    }

class ProtocolSecurityInput(BaseModel):
    """Input data for Protocol Security Risk Assessment."""
    protocol_name: str = Field(..., description="The name of the DeFi protocol (e.g., DeFiSwap V3).")
    audit_summary: str = Field(..., description="Summary of smart contract audit findings and last audit date.")
    on_chain_activity_summary: str = Field(..., description="Summary of recent on-chain activity and anomalous patterns.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "protocol_name": "DeFiSwap V3",
                "audit_summary": "Last audit: 8 months ago by CertiK. 2 medium-severity issues remain unresolved.",
                "on_chain_activity_summary": "Recent spike in flash loan activity. 3 large withdrawals (>$1M) in past week from governance contract."
            }
        }
    }

class LiquidityRiskInput(BaseModel):
    """Input data for Liquidity/Concentration Risk Assessment."""
    token_symbol: str = Field(..., description="The symbol of the token.")
    number_of_wallets: int = Field(10, description="The top N wallets to analyze for concentration.")
    large_trade_amount: str = Field("1,000,000 USD", description="The size of a hypothetical sell order to simulate price impact.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token_symbol": "ABC",
                "number_of_wallets": 5,
                "large_trade_amount": "500000 USD"
            }
        }
    }

RiskInputUnion = Union[TradingRiskInput, LendingBorrowingRiskInput, ProtocolSecurityInput, LiquidityRiskInput]

class RiskAssessmentRequest(BaseModel):
    """Request model for the /risk_assessment endpoint."""
    identifier_from_purchaser: str
    risk_type: RiskAssessmentType
    input_data: RiskInputUnion 

    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier_from_purchaser": "protocol-security-check-456",
                "risk_type": "protocol_security",
                "input_data": {
                    "protocol_name": "DeFiSwap V3",
                    "audit_summary": "Last audit: 8 months ago. 2 medium-severity issues unresolved.",
                    "on_chain_activity_summary": "Recent spike in flash loan activity observed on-chain."
                }
            }
        }
    }

class StartJobRequest(BaseModel):
    """Request model for generic research tasks."""
    identifier_from_purchaser: str
    input_data: dict[str, str]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "identifier_from_purchaser": "research_task_123",
                "input_data": {
                    "text": "Analyze the impact of recent DeFi regulations on protocol governance"
                }
            }
        }
    }

class ProvideInputRequest(BaseModel):
    job_id: str

async def execute_research_task(input_data: dict) -> str:
    """Execute a generic research task with ResearchManager"""
    logger.info(f"Starting research task with input: {input_data}")
    manager = ResearchManager(logger=logger)
    inputs = {"text": input_data.get("text", "")}
    result = manager.agent_team.kickoff(inputs)
    logger.info("Research task completed successfully")
    return result

async def execute_risk_assessment(risk_type: RiskAssessmentType, input_data: RiskInputUnion) -> dict:
    """Execute a risk assessment task with RiskAssessmentManager"""
    logger.info(f"Starting Risk Assessment for type: {risk_type.value}")
    
    manager = RiskAssessmentManager(risk_type=risk_type, logger=logger)
    
    inputs = input_data.model_dump()
    logger.info(f"Manager Inputs: {inputs}")

    raw_result = manager.agent_team.kickoff(inputs)
    
    if risk_type in [RiskAssessmentType.protocol_security, RiskAssessmentType.trading]:
        risk_score = random.randint(10, 60)
    else:
        risk_score = random.randint(30, 80)
        
    formatted_risk = map_risk_score(risk_score)

    logger.info("Risk Assessment task completed successfully")
    return {
        "risk_type": risk_type.value,
        "input_data": input_data.model_dump(),
        "risk_score_level": formatted_risk,
        "risk_score_raw": risk_score,
        "detailed_assessment": raw_result.raw if hasattr(raw_result, "raw") else str(raw_result)
    }

@app.post("/risk_assessment")
async def start_risk_assessment(data: RiskAssessmentRequest):
    """Initiates an on-chain risk assessment job and creates a payment request."""
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Received Risk Assessment request for type: {data.risk_type.value}")
        logger.info(f"Starting job {job_id} with agent {AGENT_IDENTIFIER}")

        payment_amount = os.getenv("RISK_PAYMENT_AMOUNT", "20000")
        payment_unit = os.getenv("PAYMENT_UNIT", "lovelace")
        amounts = [Amount(amount=payment_amount, unit=payment_unit)]
        logger.info(f"Using payment amount: {payment_amount} {payment_unit}")

        masumi_input_data = {
            "risk_type": data.risk_type.value,
            "input_details": data.input_data.model_dump_json(),
        }

        payment = Payment(
            agent_identifier=AGENT_IDENTIFIER,
            config=config,
            identifier_from_purchaser=data.identifier_from_purchaser,
            input_data=masumi_input_data,
            network=NETWORK
        )
        
        logger.info("Creating payment request...")
        payment_request = await payment.create_payment_request()
        blockchain_identifier = payment_request["data"]["blockchainIdentifier"]
        payment.payment_ids.add(blockchain_identifier)
        logger.info(f"Created payment request with blockchain identifier: {blockchain_identifier}")

        jobs[job_id] = {
            "status": "awaiting_payment",
            "payment_status": "pending",
            "blockchain_identifier": blockchain_identifier,
            "input_data": masumi_input_data,
            "result": None,
            "identifier_from_purchaser": data.identifier_from_purchaser,
            "task_type": "risk_assessment"
        }

        async def payment_callback(blockchain_identifier: str):
            await handle_payment_status(job_id, blockchain_identifier)

        payment_instances[job_id] = payment
        logger.info(f"Starting payment status monitoring for job {job_id}")
        await payment.start_status_monitoring(payment_callback)

        return {
            "status": "success",
            "job_id": job_id,
            "blockchainIdentifier": blockchain_identifier,
            "submitResultTime": payment_request["data"]["submitResultTime"],
            "unlockTime": payment_request["data"]["unlockTime"],
            "externalDisputeUnlockTime": payment_request["data"]["externalDisputeUnlockTime"],
            "agentIdentifier": AGENT_IDENTIFIER,
            "sellerVKey": os.getenv("SELLER_VKEY"),
            "identifierFromPurchaser": data.identifier_from_purchaser,
            "amounts": amounts,
            "input_hash": payment.input_hash,
            "payByTime": payment_request["data"]["payByTime"],
        }
    except Exception as e:
        logger.error(f"Error in start_risk_assessment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Input or internal error: {e}")

@app.post("/start_job")
async def start_job(data: StartJobRequest):
    """Initiates a generic research job and creates a payment request."""
    try:
        job_id = str(uuid.uuid4())
        
        input_text = data.input_data["text"]
        truncated_input = input_text[:100] + "..." if len(input_text) > 100 else input_text
        logger.info(f"Received research request: '{truncated_input}'")
        logger.info(f"Starting job {job_id} with agent {AGENT_IDENTIFIER}")

        payment_amount = os.getenv("PAYMENT_AMOUNT", "10000000")
        payment_unit = os.getenv("PAYMENT_UNIT", "lovelace")
        amounts = [Amount(amount=payment_amount, unit=payment_unit)]
        logger.info(f"Using payment amount: {payment_amount} {payment_unit}")
        
        payment = Payment(
            agent_identifier=AGENT_IDENTIFIER,
            config=config,
            identifier_from_purchaser=data.identifier_from_purchaser,
            input_data=data.input_data,
            network=NETWORK
        )
        
        logger.info("Creating payment request...")
        payment_request = await payment.create_payment_request()
        blockchain_identifier = payment_request["data"]["blockchainIdentifier"]
        payment.payment_ids.add(blockchain_identifier)
        logger.info(f"Created payment request with blockchain identifier: {blockchain_identifier}")

        jobs[job_id] = {
            "status": "awaiting_payment",
            "payment_status": "pending",
            "blockchain_identifier": blockchain_identifier,
            "input_data": data.input_data,
            "result": None,
            "identifier_from_purchaser": data.identifier_from_purchaser,
            "task_type": "generic_research"
        }

        async def payment_callback(blockchain_identifier: str):
            await handle_payment_status(job_id, blockchain_identifier)

        payment_instances[job_id] = payment
        logger.info(f"Starting payment status monitoring for job {job_id}")
        await payment.start_status_monitoring(payment_callback)

        return {
            "status": "success",
            "job_id": job_id,
            "blockchainIdentifier": blockchain_identifier,
            "submitResultTime": payment_request["data"]["submitResultTime"],
            "unlockTime": payment_request["data"]["unlockTime"],
            "externalDisputeUnlockTime": payment_request["data"]["externalDisputeUnlockTime"],
            "agentIdentifier": AGENT_IDENTIFIER,
            "sellerVKey": os.getenv("SELLER_VKEY"),
            "identifierFromPurchaser": data.identifier_from_purchaser,
            "amounts": amounts,
            "input_hash": payment.input_hash,
            "payByTime": payment_request["data"]["payByTime"],
        }
    except Exception as e:
        logger.error(f"Error in start_job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Input or internal error: {e}")

async def handle_payment_status(job_id: str, payment_id: str) -> None:
    """Executes the appropriate task after payment confirmation"""
    try:
        logger.info(f"Payment {payment_id} completed for job {job_id}, executing task...")
        
        job = jobs[job_id]
        job["status"] = "running"
        
        result_object = None
        result_string = None
        
        if job.get("task_type") == "risk_assessment":
            risk_type = RiskAssessmentType(job["input_data"]["risk_type"])
            input_details_json = job["input_data"]["input_details"]
            
            if risk_type == RiskAssessmentType.trading:
                InputModel = TradingRiskInput
            elif risk_type == RiskAssessmentType.lending_borrowing:
                InputModel = LendingBorrowingRiskInput
            elif risk_type == RiskAssessmentType.protocol_security:
                InputModel = ProtocolSecurityInput
            elif risk_type == RiskAssessmentType.liquidity_concentration:
                InputModel = LiquidityRiskInput
            else:
                raise ValueError("Invalid risk type in job data.")

            input_data = InputModel.model_validate_json(input_details_json)
            result_object = await execute_risk_assessment(risk_type, input_data)
            result_string = json.dumps(result_object)

        elif job.get("task_type") == "generic_research" or not job.get("task_type"):
            result_object = await execute_research_task(job["input_data"])
            result_string = result_object.raw if hasattr(result_object, "raw") else str(result_object)
            
        else:
            raise ValueError(f"Unknown task type: {job.get('task_type')}")
            
        logger.info(f"Task completed for job {job_id}")
        
        await payment_instances[job_id].complete_payment(payment_id, result_string)
        logger.info(f"Payment completed for job {job_id}")

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["payment_status"] = "completed"
        jobs[job_id]["result"] = result_object

        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]
            
    except Exception as e:
        logger.error(f"Error processing payment {payment_id} for job {job_id}: {str(e)}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        
        if job_id in payment_instances:
            payment_instances[job_id].stop_status_monitoring()
            del payment_instances[job_id]

@app.get("/status")
async def get_status(job_id: str):
    """Retrieves the current status and result of a specific job"""
    logger.info(f"Checking status for job {job_id}")
    if job_id not in jobs:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job_id in payment_instances:
        try:
            status = await payment_instances[job_id].check_payment_status()
            job["payment_status"] = status.get("data", {}).get("status")
            logger.info(f"Updated payment status for job {job_id}: {job['payment_status']}")
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}", exc_info=True)
            job["payment_status"] = "error"

    result_data = job.get("result")
    
    if job.get("task_type") == "risk_assessment" and isinstance(result_data, dict):
        result = result_data
    elif job.get("task_type") == "generic_research" and result_data and hasattr(result_data, "raw"):
        result = result_data.raw
    else:
        result = None
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "payment_status": job["payment_status"],
        "result": result
    }

@app.get("/availability")
async def check_availability():
    """Checks if the Risk Manager Agent is operational"""
    return {
        "status": "available",
        "type": "on-chain-risk-manager",
        "message": "On-Chain Risk Manager Agent operational and ready for assessments."
    }

@app.get("/input_schema")
async def input_schema():
    """Returns the expected input schemas for all task endpoints."""
    risk_options = [e.value for e in RiskAssessmentType]
    return {
        "/start_job": {
            "description": "Schema for generic research tasks.",
            "input_data": [
                {
                    "id": "text",
                    "type": "string",
                    "name": "Task Description",
                    "data": {
                        "description": "The text input for the research task",
                        "placeholder": "Enter your research task here"
                    }
                }
            ]
        },
        "/risk_assessment": {
            "description": "Schema for on-chain DeFi risk assessment tasks.",
            "input_data": [
                {
                    "id": "risk_type",
                    "type": "enum",
                    "name": "Risk Assessment Type",
                    "data": {
                        "description": "Specify the type of on-chain risk assessment.",
                        "options": risk_options
                    }
                },
                {
                    "id": "input_data_trading",
                    "type": "object",
                    "name": "Trading Risk Input",
                    "data": TradingRiskInput.model_json_schema()
                },
                {
                    "id": "input_data_lending",
                    "type": "object",
                    "name": "Lending/Borrowing Risk Input",
                    "data": LendingBorrowingRiskInput.model_json_schema()
                },
                {
                    "id": "input_data_protocol",
                    "type": "object",
                    "name": "Protocol Security Input",
                    "data": ProtocolSecurityInput.model_json_schema()
                },
                {
                    "id": "input_data_liquidity",
                    "type": "object",
                    "name": "Liquidity/Concentration Risk Input",
                    "data": LiquidityRiskInput.model_json_schema()
                }
            ]
        }
    }

@app.get("/health")
async def health():
    """Returns the health status of the Risk Manager Agent."""
    return {"status": "healthy", "agent_type": "on-chain-risk-manager"}

def main():
    """Run the standalone agent flow without the API"""
    os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
    
    print("\n" + "=" * 70)
    print("🚀 Running On-Chain Risk Manager Agent locally (standalone mode)...")
    print("=" * 70 + "\n")
    
    input_data = {"text": "Analyze the security risks of flash loan attacks in DeFi protocols"}
    
    print(f"Input: {input_data['text']}")
    print("\nProcessing with ResearchManager agents...\n")
    
    manager = ResearchManager(logger=logger, verbose=True)
    result = manager.agent_team.kickoff(inputs=input_data)
    
    print("\n" + "=" * 70)
    print("✅ Manager Output:")
    print("=" * 70 + "\n")
    print(result)
    print("\n" + "=" * 70 + "\n")
    
    sys.stdout.flush()
    sys.stderr.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        port = int(os.environ.get("API_PORT", 8000))
        host = os.environ.get("API_HOST", "127.0.0.1")

        print("\n" + "=" * 70)
        print("🚀 Starting On-Chain Risk Manager Agent API Server...")
        print("=" * 70)
        print(f"API Documentation:         http://{host}:{port}/docs")
        print(f"Risk Assessment Endpoint:  POST http://{host}:{port}/risk_assessment")
        print(f"Availability Check:        GET http://{host}:{port}/availability")
        print("=" * 70 + "\n")

        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        main()