# Create a Development Environment with Okteto, Kubernetes, and AWS Services

This is an example of how to configure and deploy a development environment that includes polyglot microservices, an AWS SQS queue, and an S3 bucket. The AWS infrastructure is deployed using Terraform.

## Architecture

![Architecture diagram](https://raw.githubusercontent.com/okteto/external-resources-aws/main/docs/architecture.png)

## Run the demo application in Okteto

### Prerequisites:
1. Okteto CLI 2.14 or newer
1. Access to an AWS account
1. An Okteto account ([Sign-up](https://www.okteto.com/try-free/) for 30 day, self-hosted free trial)
1. Configure your Okteto instance [to use an IAM role to create AWS resources](https://www.okteto.com/docs/admin/cloud-credentials/aws-cloud-credentials/)

When creating the IAM Role, make sure it has permissions to create, read from, and delete the following AWS services:

- SQS Queues
- S3 Buckets

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

Happy coding!
