import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Type

import dotenv
import yaml

from auto_trader.account import KisAccount, UpbitAccount
from auto_trader.account.base import BaseAccount
from auto_trader.agent import AssetAllocateAgent, CostAverageAgent, LeverageSwingAgent
from auto_trader.agent.base import BaseAgent

# Agent registry
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "AssetAllocateAgent": AssetAllocateAgent,
    "CostAverageAgent": CostAverageAgent,
    "LeverageSwingAgent": LeverageSwingAgent,
}

# Account registry
ACCOUNT_REGISTRY: Dict[str, Type[BaseAccount]] = {
    "kis": KisAccount,
    "upbit": UpbitAccount,
}


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(description="Auto Trading System")
    parser.add_argument(
        "-aaa",
        "--AssetAllocateAgent",
        action="store_true",
        help="Run Asset Allocation Agent",
    )
    parser.add_argument(
        "-caa",
        "--CostAverageAgent",
        action="store_true",
        help="Run Cost Average Agent",
    )
    parser.add_argument(
        "-lsa",
        "--LeverageSwingAgent",
        action="store_true",
        help="Run Leverage Swing Agent",
    )
    return parser


def load_config_file(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file {config_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to load configuration file {config_path}: {e}")
        sys.exit(1)


def create_account(acc_no: str, auth_config: dict) -> BaseAccount:
    """Create account instance based on account number."""
    account_type = "upbit" if acc_no == "upbit" else "kis"

    if account_type not in ACCOUNT_REGISTRY:
        raise ValueError(f"Unsupported account type: {account_type}")

    account_class = ACCOUNT_REGISTRY[account_type]
    return account_class(acc_no=acc_no, **auth_config[acc_no])


def create_agent(agent_name: str, account: BaseAccount, config: dict) -> BaseAgent:
    """Create agent instance."""
    if agent_name not in AGENT_REGISTRY:
        raise ValueError(f"Unsupported agent: {agent_name}")

    agent_class = AGENT_REGISTRY[agent_name]
    return agent_class(acnt=account, config=config)


def run_agent(agent_name: str, base_dir: Path, auth_config: dict) -> None:
    """Run specified trading agent."""
    print(f"Starting {agent_name}...")

    # Load agent configuration
    config_path = base_dir / "auto_trader" / "config" / f"{agent_name}.yaml"
    agent_config = load_config_file(config_path)

    # Process each account configuration
    for acc_no, account_config in agent_config.items():
        try:
            print(f"Processing account: {acc_no}")

            # Create account and agent
            account = create_account(acc_no, auth_config)
            agent = create_agent(agent_name, account, account_config)

            # Run the agent
            agent.run()
            print(f"Successfully completed {agent_name} for account {acc_no}")

        except Exception as e:
            print(f"Error running {agent_name} for account {acc_no}: {e}")
            continue


def main():
    """Main function."""
    # Load environment variables
    dotenv.load_dotenv()

    # Setup paths
    base_dir = Path(__file__).parent
    auth_path = base_dir / "auto_trader" / "config" / "auth.yaml"

    # Load authentication configuration
    auth_config = load_config_file(auth_path)

    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Check if any agent is specified
    agents_to_run = [agent for agent in AGENT_REGISTRY.keys() if getattr(args, agent)]

    if not agents_to_run:
        print("No agents specified. Use -h for help.")
        sys.exit(1)

    # Run specified agents
    for agent_name in agents_to_run:
        run_agent(agent_name, base_dir, auth_config)

    print("All agents completed.")


if __name__ == '__main__':
    main()
