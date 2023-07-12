# kedro-on-azure

The repository is a playground for experiments about using [Kedro](https://github.com/kedro-org/kedro) on Azure.

The project template is created by `kedro new` with `kedro~=0.18.0` and Python 3.10.12.

---

- [Pre-requisite](#pre-requisite)
- [Experiments](#experiments)
  - [E01. Authentication for ADLS Access](#e01-authentication-for-adls-access)

---

## Pre-requisite

- Azure account (such as a `Pay-As-You-Go` subscription)
- [`azure-cli`](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

To install the Python dependencies:

```bash
pip install -r src/requirements.txt
```

Now let's create some resources on Azure for our playground:

```bash
RG=kedro-on-azure
REGION=southeastasia
STORAGE=k9kedroonazure  # this needs to be GLOBALLY unique
CONTAINER=test

# init a local az session
az login

# create a resource group
az group create -n ${RG} -l ${REGION}

# create a storage account
az storage account create --name ${STORAGE} --resource-group ${RG}

# create a container under the storage account
az storage fs create -n ${CONTAINER} --account-name ${STORAGE}

# create and upload a test file
echo "test" > /tmp/test.txt
az storage fs file upload -s /tmp/test.txt -p test-dir/test.txt -f ${CONTAINER} --account-name ${STORAGE}

# check if the file is actually there
az storage blob list --account-name ${STORAGE} --container-name ${CONTAINER} -o table
```

## Experiments

### [E01. Authentication for ADLS Access](./docs/adls-authentication.md)
