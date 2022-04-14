# event-driven-data-processing
Prefect + AWS EKS

This project automates the deployment of data processing infrastructure using Prefect+AWS EKS, with CircleCI as a CI/CD tool. 

 I started out intending to implement a AWS lambda to trigger data processing prefect flow runs, inspired by [this post ('event driven workfloas with aws lambda')](https://medium.com/the-prefect-blog/event-driven-workflows-with-aws-lambda-2ef9d8cc8f1a), but my focus became more on automating the creation EKS infrastructure where I can use Prefect to deploy arbitrary workflows to that infrastructure. Basically, I am automating the steps outlined in [this post ('distributed data pipelines made easy...')](https://towardsdatascience.com/distributed-data-pipelines-made-easy-with-aws-eks-and-prefect-106984923b30). 

The workflow to use this project is as follows:
1. Make edits. This could be to either add new prefect flows targeted for deployment on EKS, or to edit the underlying infrastructure by modifying the cloudformation template and infra management scripts in /manage_infra
2. Commit to main or merge a dev branch to main to initialize the CI/CD process
   * Use aws cli to copy relevant .py files from the repo to a relevant S3 bucket
   * Use aws cli to create the cloudformation stack. 
      - spins up a small ec2 instance. UserData defines a startup scrip that:
         * sets up kubectl
         * downloads repo files from s3
         * runs start_nr_eks.py: sets up eksctl and optionally sets up New Relic monitoring (currently commented out)
         * launches a fargate-eks cluster
         * runs connect_prefect.py, which: 
            1. automates setting up a connection to Prefect's SaaS offering as detailed [here](https://medium.com/the-prefect-blog/prefect-getting-started-with-operationalizing-your-python-code-999a0bf1dda8)
            2. automates installing prefect's kubernetes agent on the EKS cluster
            3. automates logging into ecr (where code for flows to be run on EKS are stored on Prefect's docker image)
            4. registers prefect flows to Prefect Cloud
            5. starts a local prefect agent
      - connect_prefect.py currently registers 2 prefect flows. Once registered, the Prefect Cloud UI can be used to trigger flow execution or add a schedule.
         1. example_flow.py: has a flow config directing it to be run on the fargate EKS cluster
         2. shutdown_eks.py: has a flow config for a local run (on the ec2 instance)   
      - In future versions, the infra spin-up step could be optional if the user is happy with the stack and just wants to register new prefect flows to be run on EKS (e.g. add more flows alongside example_flow.py)
3. To shutdown the infra, trigger the shutdown_eks.py flow from the Prefect UI; then tear down the cloudformatoin stack from the AWS UI or command line


for local testing of AWS resoure deploy use (from ./.circleci/ folder)

`final_project aws cloudformation deploy --template-file aws_resources.yml --stack-name "eddp-stack-N" --parameter-overrides ID="N" --capabilities CAPABILITY_NAMED_IAM`
