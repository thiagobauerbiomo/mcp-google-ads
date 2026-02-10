"""Campaign experiment management tools (5 tools)."""

from __future__ import annotations

from typing import Annotated

from ..auth import get_client, get_service
from ..coordinator import mcp
from ..utils import error_response, resolve_customer_id, success_response, validate_numeric_id


@mcp.tool()
def list_experiments(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    limit: Annotated[int, "Maximum number of results"] = 50,
) -> str:
    """List all campaign experiments.

    Experiments allow A/B testing of campaign changes before full implementation.
    """
    try:
        cid = resolve_customer_id(customer_id)
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                experiment.resource_name,
                experiment.name,
                experiment.description,
                experiment.status,
                experiment.start_date,
                experiment.end_date,
                experiment.goals
            FROM experiment
            ORDER BY experiment.name ASC
            LIMIT {limit}
        """
        response = service.search(customer_id=cid, query=query)
        experiments = []
        for row in response:
            experiments.append({
                "resource_name": row.experiment.resource_name,
                "name": row.experiment.name,
                "description": row.experiment.description,
                "status": row.experiment.status.name,
                "start_date": row.experiment.start_date,
                "end_date": row.experiment.end_date,
            })
        return success_response({"experiments": experiments, "count": len(experiments)})
    except Exception as e:
        return error_response(f"Failed to list experiments: {e}")


@mcp.tool()
def create_experiment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    name: Annotated[str, "Experiment name"],
    campaign_id: Annotated[str, "The base campaign ID to experiment on"],
    traffic_split_percent: Annotated[int, "Percentage of traffic for the experiment arm (1-99)"],
    description: Annotated[str | None, "Experiment description"] = None,
    start_date: Annotated[str | None, "Start date (YYYY-MM-DD)"] = None,
    end_date: Annotated[str | None, "End date (YYYY-MM-DD)"] = None,
) -> str:
    """Create a campaign experiment for A/B testing.

    The experiment creates a trial campaign that receives a portion of the original campaign's traffic.
    After the experiment ends, you can promote the trial or end the experiment.
    """
    try:
        cid = resolve_customer_id(customer_id)
        client = get_client()
        experiment_service = get_service("ExperimentService")

        operation = client.get_type("ExperimentOperation")
        experiment = operation.create
        experiment.name = name
        experiment.type_ = client.enums.ExperimentTypeEnum.SEARCH_CUSTOM
        experiment.status = client.enums.ExperimentStatusEnum.SETUP
        experiment.suffix = f" [Experiment]"

        if description:
            experiment.description = description
        if start_date:
            experiment.start_date = start_date
        if end_date:
            experiment.end_date = end_date

        response = experiment_service.mutate_experiments(customer_id=cid, operations=[operation])
        experiment_rn = response.results[0].resource_name
        experiment_id = experiment_rn.split("/")[-1]

        # Create experiment arms (control + treatment)
        arm_service = get_service("ExperimentArmService")

        # Control arm
        control_op = client.get_type("ExperimentArmOperation")
        control = control_op.create
        control.experiment = experiment_rn
        control.name = "Control"
        control.control = True
        control.traffic_split = 100 - traffic_split_percent
        control.campaigns.append(f"customers/{cid}/campaigns/{campaign_id}")

        # Treatment arm
        treatment_op = client.get_type("ExperimentArmOperation")
        treatment = treatment_op.create
        treatment.experiment = experiment_rn
        treatment.name = "Treatment"
        treatment.control = False
        treatment.traffic_split = traffic_split_percent

        arm_service.mutate_experiment_arms(
            customer_id=cid, operations=[control_op, treatment_op]
        )

        # Schedule the experiment
        experiment_service.schedule_experiment(resource_name=experiment_rn)

        return success_response(
            {
                "experiment_id": experiment_id,
                "resource_name": experiment_rn,
                "traffic_split": f"{100 - traffic_split_percent}% control / {traffic_split_percent}% treatment",
            },
            message=f"Experiment '{name}' created and scheduled",
        )
    except Exception as e:
        return error_response(f"Failed to create experiment: {e}")


@mcp.tool()
def get_experiment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    experiment_id: Annotated[str, "The experiment ID"],
) -> str:
    """Get detailed information about a specific experiment including its arms."""
    try:
        cid = resolve_customer_id(customer_id)
        safe_eid = validate_numeric_id(experiment_id, "experiment_id")
        service = get_service("GoogleAdsService")

        query = f"""
            SELECT
                experiment.resource_name,
                experiment.name,
                experiment.description,
                experiment.status,
                experiment.start_date,
                experiment.end_date,
                experiment.goals,
                experiment.suffix
            FROM experiment
            WHERE experiment.resource_name = 'customers/{cid}/experiments/{safe_eid}'
        """
        response = service.search(customer_id=cid, query=query)
        experiment_data = None
        for row in response:
            experiment_data = {
                "resource_name": row.experiment.resource_name,
                "name": row.experiment.name,
                "description": row.experiment.description,
                "status": row.experiment.status.name,
                "start_date": row.experiment.start_date,
                "end_date": row.experiment.end_date,
                "suffix": row.experiment.suffix,
            }

        if not experiment_data:
            return error_response(f"Experiment {experiment_id} not found")

        # Get experiment arms
        arm_query = f"""
            SELECT
                experiment_arm.name,
                experiment_arm.control,
                experiment_arm.traffic_split,
                experiment_arm.campaigns
            FROM experiment_arm
            WHERE experiment_arm.experiment = 'customers/{cid}/experiments/{safe_eid}'
        """
        arm_response = service.search(customer_id=cid, query=arm_query)
        arms = []
        for row in arm_response:
            arms.append({
                "name": row.experiment_arm.name,
                "control": row.experiment_arm.control,
                "traffic_split": row.experiment_arm.traffic_split,
                "campaigns": list(row.experiment_arm.campaigns),
            })

        experiment_data["arms"] = arms
        return success_response(experiment_data)
    except Exception as e:
        return error_response(f"Failed to get experiment: {e}")


@mcp.tool()
def promote_experiment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    experiment_id: Annotated[str, "The experiment ID to promote"],
) -> str:
    """Promote an experiment — apply the treatment changes to the original campaign.

    WARNING: This permanently applies the experiment changes to the base campaign.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_eid = validate_numeric_id(experiment_id, "experiment_id")
        service = get_service("ExperimentService")

        resource_name = f"customers/{cid}/experiments/{safe_eid}"
        service.promote_experiment(resource_name=resource_name)

        return success_response(
            {"experiment_id": experiment_id, "action": "promoted"},
            message=f"Experiment {experiment_id} promoted — changes applied to base campaign",
        )
    except Exception as e:
        return error_response(f"Failed to promote experiment: {e}")


@mcp.tool()
def end_experiment(
    customer_id: Annotated[str, "The Google Ads customer ID"],
    experiment_id: Annotated[str, "The experiment ID to end"],
) -> str:
    """End an experiment without applying changes.

    The experiment's trial campaign will be removed and the base campaign returns to normal.
    """
    try:
        cid = resolve_customer_id(customer_id)
        safe_eid = validate_numeric_id(experiment_id, "experiment_id")
        service = get_service("ExperimentService")

        resource_name = f"customers/{cid}/experiments/{safe_eid}"
        service.end_experiment(resource_name=resource_name)

        return success_response(
            {"experiment_id": experiment_id, "action": "ended"},
            message=f"Experiment {experiment_id} ended — no changes applied",
        )
    except Exception as e:
        return error_response(f"Failed to end experiment: {e}")
