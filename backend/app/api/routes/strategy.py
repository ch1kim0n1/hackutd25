from app.agents.agent_network import AgentNetwork

async def run_strategy(agent_network: AgentNetwork, strategy_id: str, user_id: str):
    """
    Publishes a message to the agent network to execute a strategy.
    """
    message = {
        "strategy_id": strategy_id,
        "user_id": user_id
    }
    await agent_network.publish("strategy_execute", message)
    return {"status": "submitted", "strategy_id": strategy_id}
