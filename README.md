# Create a Development Environment with Okteto, Kubernetes, and AWS Services

This is an example of how to configure and deploy a development environment that includes polyglot microservices, an AWS SQS queue, and an S3 bucket. The AWS infrastructure is deployed using Terraform.

## Architecture

![Architecture diagram](https://raw.githubusercontent.com/okteto/external-resources-aws/main/docs/architecture.png)

## Run the demo application in Okteto

### Prequisites:
1. Okteto CLI 2.14 or newer
1. An AWS account
1. An Okteto account ([Sign-up](https://www.okteto.com/try-free/) for 30 day, self-hosted free trial)
1. Create a set of IAM keys for your AWS account (If you are using Okteto Self-Hosted, you can directly assign an AWS Role)
1. Create the following Okteto secrets:

        AWS_ACCESS_KEY_ID: The Acces Key ID of your IAM user
        AWS_SECRET_ACCESS_KEY: The Secret Acces Key of your IAM user
        AWS_REGION: The region in AWS you would like to use for the external resources


> If you are using Okteto Self-Hosted, you can configure your instance to use an AWS role instead of using an Acess Key and Secret Access Key.

Once this is configured, anyone with access to your Okteto instance will be able to deploy an development environment automatically, including the required cloud infrastructure.


```
$ git clone https://github.com/okteto/external-resources-tf-aws
$ cd external-resources-aws
$ okteto context use $OKTETO_URL
$ okteto deploy
```

## Develop on the Menu microservice

```
$ okteto up menu
```

## Develop on the Kitchen microservice

```
$ okteto up kitchen
```

## Develop on the Result microservice

```
$ okteto up check
```

## Notes

This isn't an example of a properly architected perfectly designed distributed app... it's a simple
example of the various types of pieces and languages you might see (queues, persistent data, etc), and how to
deal with them in Okteto.
