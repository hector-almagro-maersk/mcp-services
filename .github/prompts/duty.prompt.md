---
mode: agent
model: GPT-4.1
tools: [kubernetesProd, azureStorage]
description: 'Duty report'
---

## Duty Prompt for MCP Services

### Blob Storage Check
1. Using the Azure Storage MCP, check if there are any files left to process in the blob storage containers.
2. If there are pending files, check again immediately up to a maximum of 5 times (they may be in processing).
3. If after 5 attempts there are still pending files, report to the user the file names and the container where they are located.

### Kubernetes Pods Health Check
1. Using the Kubernetes MCP, check the status of all pods.
2. If all pods are in "Running" state and have 0 restarts, report the total number of pods and that everything is OK.
3. If there are pods with a state other than "Running" or with restarts > 0:
   - List each problematic pod with: name, number of restarts, state.
   - For each problematic pod, run a "describe" and check the logs from the last 24 hours.
   - Briefly summarize the issue found in each pod using the information from the describe and the logs.

### Final Report
- If there are pending files in blob storage after 5 attempts, inform the user.
- If there are problematic pods, show the summary for each one.
- If everything is fine, indicate the total number of pods and that the system is working correctly.

