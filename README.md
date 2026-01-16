# Create a Development Environment with Okteto, Kubernetes, and AWS Services

This is an example of how to develop with a shared environment using Okteto Divert and SQS queues

## Architecture

![Architecture diagram](https://raw.githubusercontent.com/okteto/external-resources-aws/main/docs/architecture.png)

## Run the demo application in Okteto

### Prerequisites:
1. Okteto CLI 3.0 or newer
1. An AWS account
1. An Okteto account ([Sign-up](https://www.okteto.com/try-free/) for 30 day, self-hosted free trial)
1. Create a set of IAM keys for your AWS account (If you are using Okteto Self-Hosted, you can directly assign an AWS Role)
1. Create the following Okteto secrets:

        AWS_ACCESS_KEY_ID: The Acces Key ID of your IAM user
        AWS_SECRET_ACCESS_KEY: The Secret Acces Key of your IAM user
        AWS_REGION: The region in AWS you would like to use for the external resources
1. Install modheader in your browser. 

Make sure this AWS user has permissions to create, read from, and delete the following AWS services:

- SQS Queues
- S3 Buckets

> Alternatively if you are using Okteto Self-Hosted, you can configure your instance to use an AWS role instead of using an Access Key and Secret Access Key.

Once this is configured, anyone with access to your Okteto instance will be able to deploy an development environment automatically, including the required cloud infrastructure.


### Deploy shared environment

This will deploy all the AWS resources and the entire application.  

```
$ git clone https://github.com/okteto/external-resources-tf-aws
$ git checkout rb/with-divert
$ cd external-resources-aws
$ okteto context use $OKTETO_URL
$ okteto preview deploy tacoshop -l okteto-shared
```

### Deploy kitchen service

This will only deploy the kitchen service, which in this demo is the service under development. 

```
$ git clone https://github.com/okteto/external-resources-tf-aws
$ git checkout rb/with-divert
$ cd external-resources-aws
$ okteto context use $OKTETO_URL
$ export OKTETO_TACOSHOP_SHARED_NAMESPACE=tacoshop 
$ okteto deploy -f okteto.kitchen.yaml
```

### Test Divert


