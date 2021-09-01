# event-driven-data-processing
AWS Lambda + Prefect + AWS EKS


for local testing of AWS resoure deploy use (from ./.circleci/ folder)

`final_project aws cloudformation deploy --template-file aws_resources.yml --stack-name "eddp-stack-N" --parameter-overrides ID="N" --capabilities CAPABILITY_NAMED_IAM`


### dev workflow
* on local repo:
 - make updates (install libraries, edit sourcecode)
 - build the docker image locally
 - push the new docker image to ECR
 - deploy (if not already avail.) aws_resources.yml

* ssh into the deployed EC2 instance
 - set up the machine (awscli, eks, etc--record set up instructions to draft a startup script for CI/CD)
    * to add python packages use, e.g., `poetry add "prefect[kubernetes,aws]"`
 - pull the most up-to-date docker image from ECR and run it

 * troubleshoot & go back to local repo to make updates

* app/connect_prefect.py
    - automates (in a prefect flow) setting up a connection to Prefect's SaaS offering as detailed [here](https://medium.com/the-prefect-blog/prefect-getting-started-with-operationalizing-your-python-code-999a0bf1dda8)
    - uses AWS SecretsManager to obtain login token for prefect