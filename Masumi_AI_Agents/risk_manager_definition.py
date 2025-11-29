from crewai import Agent, Crew, Task
from logging_config import get_logger
from enum import Enum

class RiskAssessmentType(str, Enum):
    """Defines the types of risk assessments the manager can perform."""
    trading = "trading"
    lending_borrowing = "lending_borrowing"
    protocol_security = "protocol_security"
    liquidity_concentration = "liquidity_concentration"

class RiskAssessmentManager:
    """
    On-chain Risk Assessment Manager for DeFi protocols.
    Orchestrates specialized agents to analyze various risk factors.
    """
    def __init__(self, risk_type: RiskAssessmentType, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.risk_type = risk_type
        self.agent_team = self.create_agent_team()
        self.logger.info(f"RiskAssessmentManager initialized for type: {self.risk_type.value}")

    def create_agent_team(self):
        """Creates a specialized team of agents for risk assessment."""
        self.logger.info(f"Creating risk assessment team for {self.risk_type.value}")
        
        data_analyst = Agent(
            role='On-Chain Data Analyst',
            goal=f'Analyze blockchain and market data specific to {self.risk_type.value} risk, calculating key metrics and identifying vulnerabilities.',
            backstory=(
                'Expert in dissecting complex on-chain financial and technical data, '
                'identifying volatility patterns, smart contract exploits, and systemic risk factors '
                'in the DeFi ecosystem. Specializes in real-time blockchain analysis.'
            ),
            verbose=self.verbose,
            allow_delegation=False
        )

        risk_evaluator = Agent(
            role='Risk Evaluation Specialist',
            goal='Synthesize on-chain data analysis into a clear, actionable risk assessment report with justified risk scoring.',
            backstory=(
                'Skilled in communicating complex DeFi risk levels to both technical and non-technical stakeholders, '
                'adhering to industry-standard risk grading scales and providing concrete mitigation strategies '
                'for on-chain operations.'
            ),
            verbose=self.verbose,
            allow_delegation=False
        )

        analysis_task = self._create_specific_analysis_task(data_analyst)
        
        evaluation_task = Task(
            description=(
                "Based on the 'On-Chain Data Analyst's' detailed findings, generate a final, easy-to-read "
                "risk assessment report. The report must clearly state the major risk factors discovered through "
                "on-chain analysis and provide a narrative justifying the final risk score. \n\n"
                "**IMPORTANT**: Do not output just the raw score. Provide a comprehensive summary explaining "
                "WHY the risk is at this level based on blockchain data and market conditions."
            ),
            expected_output='A final, well-structured risk narrative report in Markdown format with actionable insights.',
            agent=risk_evaluator,
            context=[analysis_task]
        )
        
        agent_team = Crew(
            agents=[data_analyst, risk_evaluator],
            tasks=[analysis_task, evaluation_task],
            verbose=self.verbose
        )
        
        self.logger.info("Risk Assessment Manager team setup completed")
        return agent_team

    def _create_specific_analysis_task(self, agent: Agent) -> Task:
        """Helper method to create the correct analysis task based on risk type."""
        
        if self.risk_type == RiskAssessmentType.trading:
            return Task(
                description=(
                    "Analyze the on-chain and market performance of the token: **{token_symbol}** "
                    "over the last **{time_period}**. Calculate key volatility metrics (e.g., historical standard deviation, "
                    "on-chain trading volume, price slippage patterns) and consider the following additional factors: "
                    "**{more_parameters}**. Examine on-chain transaction patterns and holder distribution changes. "
                    "The final output must be a detailed assessment to determine the asset's risk score (0-100)."
                ),
                expected_output='A detailed on-chain and market analysis of the token\'s risk factors with quantitative metrics.',
                agent=agent
            )
        
        elif self.risk_type == RiskAssessmentType.lending_borrowing:
            return Task(
                description=(
                    "Assess the on-chain risk of a loan involving the **{borrowing_asset}** based on the "
                    "borrower's on-chain history: **{borrower_history_summary}**. Analyze the collateral quality "
                    "through on-chain verification, LTV (Loan-to-Value) ratio implications, borrower's on-chain "
                    "transaction history, and protocol-specific risk parameters. Review smart contract interactions "
                    "and historical default patterns. "
                    "The final output must be a detailed credit and on-chain risk assessment to determine the loan's risk score (0-100)."
                ),
                expected_output='A detailed credit and counterparty risk assessment based on on-chain data and borrower behavior.',
                agent=agent
            )
            
        elif self.risk_type == RiskAssessmentType.protocol_security:
            return Task(
                description=(
                    "Conduct a comprehensive **Protocol Security and Smart Contract Risk** assessment for the DeFi protocol: "
                    "**{protocol_name}** using the following inputs:\n"
                    "1. Audit Summary: **{audit_summary}**\n"
                    "2. On-Chain Activity: **{on_chain_activity_summary}**\n\n"
                    "Analyze smart contract code for known vulnerabilities (e.g., reentrancy, integer overflow, flash loan exploits). "
                    "Examine recent on-chain activity for suspicious patterns, large anomalous transactions, or potential economic exploits. "
                    "Review the protocol's TVL stability, governance mechanism security, and historical incident responses. "
                    "The final output must be a detailed assessment to determine the protocol's security risk score (0-100)."
                ),
                expected_output='A detailed security and smart contract risk analysis of the protocol with specific vulnerability assessment.',
                agent=agent
            )
            
        elif self.risk_type == RiskAssessmentType.liquidity_concentration:
            return Task(
                description=(
                    "Assess the **On-Chain Liquidity and Concentration Risk** for the token: **{token_symbol}**. "
                    "Analyze the on-chain distribution: percentage of circulating supply held by the top **{number_of_wallets}** "
                    "wallets (whale risk) using blockchain data. Evaluate liquidity depth by examining the token's 24-hour "
                    "on-chain trading volume against the total liquidity pool TVL across all DEXs. "
                    "Simulate the price impact of a **{large_trade_amount}** sell order on the primary DEX using on-chain liquidity data. "
                    "Analyze historical concentration changes and potential exit liquidity scenarios. "
                    "The final output must be a detailed assessment to determine the asset's concentration and liquidity risk score (0-100)."
                ),
                expected_output='A detailed analysis of on-chain whale holdings, market depth, and potential slippage risk with quantitative metrics.',
                agent=agent
            )
            
        else:
            raise ValueError(f"Unsupported risk type: {self.risk_type.value}")

class ResearchManager:
    """
    General-purpose research and analysis manager.
    Used for generic information gathering and summarization tasks.
    """
    def __init__(self, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.agent_team = self.create_agent_team()
        self.logger.info("ResearchManager initialized")

    def create_agent_team(self):
        """Creates a general-purpose research team."""
        self.logger.info("Creating research team with agents")
        
        researcher = Agent(
            role='Research Analyst',
            goal='Find and analyze key information from various sources',
            backstory='Expert at extracting and organizing information from diverse data sources',
            verbose=self.verbose
        )

        writer = Agent(
            role='Content Synthesizer',
            goal='Create clear, actionable summaries from research findings',
            backstory='Skilled at transforming complex information into digestible insights',
            verbose=self.verbose
        )

        self.logger.info("Created research and synthesizer agents")

        return Crew(
            agents=[researcher, writer],
            tasks=[
                Task(
                    description='Research and analyze: {text}',
                    expected_output='Detailed research findings and analysis about the topic',
                    agent=researcher
                ),
                Task(
                    description='Synthesize research into summary',
                    expected_output='Clear and concise summary of the research findings with key takeaways',
                    agent=writer
                )
            ],
            verbose=self.verbose
        )