# E01. Authentication for ADLS Access

Most of the built-in kedro datasets supports [`fsspec`](https://github.com/fsspec) for remote backend storage.
For ADLS, [`adlfs`](https://github.com/fsspec/adlfs) is the go-to implementation.

There are in general two ways to authenticate the access to ADLS:
1. using account access key
2. using [service principal](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals) (with role-based access control)

The first approach requires 1 credential per storage account,
and the second approach only requires 1 credential for the service principal itself.
For a fully credential-less approach we will need to leverage Azure [managed identity](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview).
However, managed identity is only attachable to an Azure resource (such as a VM) but not a local machine.
For a development workflow where developers need to run their code from local,
service principal is the go-to approach,
especially when the application needs to access data across storage accounts or even across subscriptions.

For completeness, we will cover both access key and service principal use case.

## Using account access key

There are 3 patterns of providing credentials for a catalog item in our `catalog.yml`:

```yml
data1:
    type: text.TextDataSet
    filepath: abfs://${container}/${path}

data2:
    type: text.TextDataSet
    filepath: abfs://${container}/${path}
    fs_args:
        account_name: ${storage_account}

data3:
    type: text.TextDataSet
    filepath: abfs://${container}/${path}
    credentials: adls
```

For the 1st pattern, we do not specify any credentials at all.
We rely on the fact that `adlfs` will parse the following two keys from the environment variables:

```
AZURE_STORAGE_ACCOUNT_NAME
AZURE_STORAGE_ACCOUNT_KEY
```

To test it:

```bash
export AZURE_STORAGE_ACCOUNT_NAME=${STORAGE}
export AZURE_STORAGE_ACCOUNT_KEY=$(az storage account keys list -n ${STORAGE} -g ${RG} --query "[0].value" -o tsv)

kedro run -e pattern1 -p test --nodes data1
```

This can also be done by providing a local `.env` with the help of `python-dotenv` to inject the environment variables at the beginning of a Kedro session.
(Refer to [`settings.py`](../src/a_kedro_project/settings.py) for details.)

In the 2nd pattern, we leverage `fs_args` to provide the storage account name explicitly.
This will allow us to specify multiple storage accounts on dataset-level.
And we no longer need to specify `AZURE_STORAGE_ACCOUNT_NAME` as our environment variable anymore.

To test it:

```bash
unset AZURE_STORAGE_ACCOUNT_NAME
kedro run -e pattern2 -p test --nodes data2
```

One thing noteworthy: `fs_args` has higher priority over the environment variable.
So even if the `AZURE_STORAGE_ACCOUNT_NAME` is set to some other values,
the value from `fs_args` overwrites.

The 3rd pattern is based on Kedro's credential injection mechanism.
We will need to provide a local `credentials.yml` config file with the following format:

```yml
adls:  # this is just a key to be refered in the catalog.yml
  account_name: ${storage_account}  # we can also use globals for interpolation
  account_key: xxx
```

so that the credentials will be injected at runtime.
This is indeed a secure way of doing the following:

```yml
data4:
    type: text.TextDataSet
    filepath: abfs://${container}/${path}
    fs_args:
        account_name: ${storage_account}
        account_key: xxx  # we don't want to hardcode our secret here!
```

where we assume `catalog.yml` is going to be committed while `credentials.yml` should remain secret and strictly available only from local.

The convention is to put `credentials.yml` under `conf/local`.
For our code base we put it under `conf/pattern3` instead for easy demo purpose.
We just need to make sure we `gitignore` all `credentials.yml` in our code base so we don't expose ourself.

To test it:

```bash
unset AZURE_STORAGE_ACCOUNT_NAME
unset AZURE_STORAGE_ACCOUNT_KEY

kedro run -e pattern3 -p test --nodes data3
```

Since `credentials.yml` can be further interpolated by globals or [ameneded by hooks](https://docs.kedro.org/en/stable/hooks/common_use_cases.html#use-hooks-to-load-external-credentials),
it can be easily extended to integrate with other external secret managers.

### Using service principal

By using service princial,
we can eliminate the need of access key.
The only credential we need to take care is the password of the service principal itself.

A service principal can be configured with roles for its access to data.
Such access can be across multiple storage accounts, and even multiple subscriptions.
This is a much more solid approach than using access key.

```bash
# create a service principal
# we capture the output and save password directly into a variable so it won't be printed out
# there is no way to fetch the password of a service principal with azure-cli
APP_SECRET=$(az ad sp create-for-rbac --name "kedro-on-azure" | jq -r '.password')

# attach a built-in role to the service principal that allows it to read/write to the container
APP_ID=$(az ad sp list --filter "startswith(displayName, 'kedro-on-azure')" --query "[0].appId" -o tsv)
SUBS_ID=$(az account show --query id -o tsv)

az role assignment create \
    --role "Storage Blob Data Contributor" \
    --assignee ${APP_ID} \
    --scope "/subscriptions/${SUBS_ID}/resourceGroups/${RG}/providers/Microsoft.Storage/storageAccounts/${STORAGE}/blobServices/default/containers/${CONTAINER}"

# check
az role assignment list --all --assignee ${APP_ID}
```

For `adlfs` to identify service principal credential, the following 3 environment variables are required:

```bash
export AZURE_STORAGE_CLIENT_ID=${APP_ID}
export AZURE_STORAGE_TENANT_ID=$(az account tenant list --query '[0].tenantId' -o tsv)
export AZURE_STORAGE_CLIENT_SECRET=${APP_SECRET}

# we can test that it works with the 2nd pattern, where we only specify the account name in fs_args
kedro run -e pattern2 -p test --nodes data2

# it will also works with the 1st pattern, if we specify the account name in env var
export AZURE_STORAGE_ACCOUNT_NAME=${STORAGE}
kedro run -e pattern1 -p test --nodes data1
```
