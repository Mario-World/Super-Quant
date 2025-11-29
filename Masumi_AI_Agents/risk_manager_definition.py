from crewai import Agent, Crew, Task
from logging_config import get_logger
from enum import Enum

class RiskAssessmentType(str, Enum):
    """Defines the types of risk assessments the agent can perform."""
    trading = "trading"
    lending_borrowing = "lending_borrowing"

class RiskAssessmentTeam:
    def __init__(self, risk_type: RiskAssessmentType, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.risk_type = risk_type
        self.agent_team = self.create_team()
        self.logger.info(f"RiskAssessmentTeam initialized for type: {self.risk_type.value}")

    def create_team(self):
        self.logger.info(f"Creating risk assessment team for {self.risk_type.value}")
        
        data_analyst = Agent(
            role='Market Data Analyst',
            goal=f'Analyze historical performance and technical data for {self.risk_type.value} risk.',
            backstory='Expert in dissecting complex financial data and identifying volatility and risk factors.',
            verbose=self.verbose
        )

        risk_summarizer = Agent(
            role='Risk Summary Expert',
            goal='Synthesize data analysis into a clear, concise risk assessment report.',
            backstory='Skilled in communicating complex risk levels simply and effectively, adhering to standard risk grading scales.',
            verbose=self.verbose
        )

        if self.risk_type == RiskAssessmentType.trading:
            research_task = Task(
                description=(
                    "Analyze the historical price performance of the token_symbol: **{token_symbol}** "
                    "over the last **{time_period}**. Calculate key volatility metrics (e.g., historical standard deviation) "
                    "and consider the following additional factors: **{more_parameters}**. "
                    "The final output must be a detailed assessment to determine the asset's risk score (0-100)."
                ),
                expected_output='A detailed financial analysis of the token\'s risk factors.',
                agent=data_analyst
            )
        
        elif self.risk_type == RiskAssessmentType.lending_borrowing:
            research_task = Task(
                description=(
                    "Assess the risk of a loan involving the **{borrowing_asset}** based on the "
                    "borrower's summarized history: **{borrower_history_summary}**. Analyze the collateral quality, "
                    "LTV (Loan-to-Value) ratio implications, and borrower reliability. "
                    "The final output must be a detailed credit and market risk assessment to determine the loan\'s risk score (0-100)."
                ),
                expected_output='A detailed credit and counterparty risk assessment for the loan.',
                agent=data_analyst
            )
            
        else:
            raise ValueError(f"Unsupported risk type: {self.risk_type.value}")


        summarize_task = Task(
            description=(
                "Based on the 'Market Data Analyst's' detailed findings, generate a final, easy-to-read "
                "risk assessment report. The report must clearly state the major risk factors and a narrative "
                "justifying the final risk score. **DO NOT include the 0-100 score in the raw output,** "
                "just the detailed narrative."
            ),
            expected_output='A final, well-structured risk narrative report.',
            agent=risk_summarizer,
            context=[research_task]
        )
        
        agent_team = Crew(
            agents=[data_analyst, risk_summarizer],
            tasks=[research_task, summarize_task]
        )
        
        self.logger.info("Risk Assessment Team setup completed")
        return agent_team

class ResearchTeam:
    def __init__(self, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.agent_team = self.create_team()
        self.logger.info("ResearchTeam initialized")

    def create_team(self):
        self.logger.info("Creating research team with agents")
        
        researcher = Agent(
            role='Research Analyst',
            goal='Find and analyze key information',
            backstory='Expert at extracting information',
            verbose=self.verbose
        )

        writer = Agent(
            role='Content Summarizer',
            goal='Create clear summaries from research',
            backstory='Skilled at transforming complex information',
            verbose=self.verbose
        )

        self.logger.info("Created research and writer agents")

        agent_team = Crew(
            agents=[researcher, writer],
            tasks=[
                Task(
                    description='Research: {text}',
                    expected_output='Detailed research findings about the topic',
                    agent=researcher
                ),
                Task(
                    description='Write summary',
                    expected_output='Clear and concise summary of the research findings',
                    agent=writer
                )
            ]
        )
        self.logger.info("Team setup completed")
        return agent_team