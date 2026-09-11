import os
import time
import uuid
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (
    ContainerGroup, Container, ResourceRequirements, ResourceRequests,
    ImageRegistryCredential, OperatingSystemTypes
)

load_dotenv()


class AzureSandboxUnavailable(Exception):
    """Raised whenever the Azure backend can't be used, for any reason."""
    pass


def run_in_sandbox_azure(code: str, timeout_seconds: int = 5) -> dict:
    try:
        SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        ACR_LOGIN_SERVER = os.getenv("ACR_LOGIN_SERVER")
        ACR_USERNAME = os.getenv("ACR_USERNAME")
        ACR_PASSWORD = os.getenv("ACR_PASSWORD")

        if not all([SUBSCRIPTION_ID, RESOURCE_GROUP, ACR_LOGIN_SERVER, ACR_USERNAME, ACR_PASSWORD]):
            raise AzureSandboxUnavailable("Azure environment variables are not fully configured.")

        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET")
        )
        client = ContainerInstanceManagementClient(credential, SUBSCRIPTION_ID)

        container_group_name = f"sandbox-{uuid.uuid4().hex[:12]}"
        wrapped_command = ["timeout", str(timeout_seconds), "python", "-c", code]

        container_group = ContainerGroup(
            location="eastus",
            containers=[
                Container(
                    name="sandbox-run",
                    image=f"{ACR_LOGIN_SERVER}/eval-sandbox:latest",
                    resources=ResourceRequirements(requests=ResourceRequests(memory_in_gb=0.5, cpu=0.5)),
                    command=wrapped_command
                )
            ],
            os_type=OperatingSystemTypes.LINUX,
            restart_policy="Never",
            image_registry_credentials=[
                ImageRegistryCredential(server=ACR_LOGIN_SERVER, username=ACR_USERNAME, password=ACR_PASSWORD)
            ]
        )

        client.container_groups.begin_create_or_update(
            RESOURCE_GROUP, container_group_name, container_group
        ).result()

        max_wait = timeout_seconds + 30
        waited = 0
        group = None
        while waited < max_wait:
            group = client.container_groups.get(RESOURCE_GROUP, container_group_name)
            state = group.containers[0].instance_view.current_state.state if group.containers[0].instance_view else None
            if state == "Terminated":
                break
            time.sleep(2)
            waited += 2

        logs = client.containers.list_logs(RESOURCE_GROUP, container_group_name, "sandbox-run").content
        exit_code = None
        if group.containers[0].instance_view and group.containers[0].instance_view.current_state:
            exit_code = group.containers[0].instance_view.current_state.exit_code

        client.container_groups.begin_delete(RESOURCE_GROUP, container_group_name)

        return {
            "stdout": logs if exit_code == 0 else "",
            "stderr": logs if exit_code != 0 else "",
            "exit_code": exit_code if exit_code is not None else -1,
            "timed_out": exit_code == 124
        }

    except AzureSandboxUnavailable:
        raise
    except Exception as e:
        # Catches auth failures, disabled subscriptions, network errors, anything else Azure throws
        raise AzureSandboxUnavailable(str(e)) from e