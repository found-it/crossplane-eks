#!/usr/bin/env python3

import base64
import json
import pathlib
import subprocess
import sys
import time

import kubernetes


def _kubectl_apply(manifest):
    args = [
        "kubectl",
        "apply",
        "--filename",
        manifest,
    ]

    try:
        subprocess.run(
            args=args,
            check=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError:
        raise


def main():
    namespace = "crossplane-system"

    args = [
        "helm",
        "upgrade",
        "crossplane",
        "--install",
        "--create-namespace",
        "--namespace",
        namespace,
        "--version",
        "1.3.0",
        "--values",
        "values.yaml",
        "crossplane-stable/crossplane",
    ]

    print("Install helm chart")
    try:
        subprocess.run(
            args=args,
            check=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        print(e)
        sys.exit(1)

    kubernetes.config.load_kube_config()
    v1 = kubernetes.client.CoreV1Api()

    try:
        body = kubernetes.client.V1Namespace(
            api_version="v1", kind="Namespace", metadata={"name": namespace}
        )
        v1.create_namespace(body=body)
    except kubernetes.client.rest.ApiException as e:
        if e.status != 409:
            raise
        else:
            print(f"Namespace {namespace} already exists")
    else:
        print(f"Created {namespace}")

    secret_name = "aws-creds"

    body = kubernetes.client.V1Secret(
        type="Opaque",
        api_version="v1",
        kind="Secret",
        metadata={"name": secret_name, "namespace": namespace},
        data={
            "creds": base64.b64encode(pathlib.Path("creds.conf").read_bytes()).decode(
                "utf-8"
            )
        },
    )

    try:
        api_response = v1.create_namespaced_secret(namespace=namespace, body=body)
    except kubernetes.client.rest.ApiException as e:
        if e.status != 409:
            raise
        else:
            print(f"Secret {secret_name} already exists in {namespace}")
    else:
        print(f"Created secret {secret_name} in {namespace}")

    time.sleep(2)
    _kubectl_apply(manifest="manifests/providerconfig.yaml")

    # Wait for the CRDs
    time.sleep(2)
    _kubectl_apply(manifest="manifests/definition.yaml")
    # _kubectl_apply(manifest="manifests/infra.yaml")

    time.sleep(2)
    _kubectl_apply(manifest="manifests/composition-aws.yaml")

    # Wait for cluster
    # AWS grab kubeconfig
    # Update the AWS CM
    # Create clusterrolebinding


if __name__ == "__main__":
    main()
