1. Prepare artifacts for the application, including docker images etc.
2. Run operator-sdk command to create an Ansible type operator.
3. Modify the scaffolding code to build the operator:
* Add the tasks to ansible playbook
* Modify or add CRDs and CRs
* Modify the role and rolebinding
* Build docker image for the operator
* Update Deployment to use the docker image
4. Two approaches to install the operator and deploy application.
- Install manually
  - create serviceaccount
  - create role and rolebinding
  - create the operator deployment
  - deploy the application with customresource
- Install through OLM
  - generate clusterserviceversion
  - update csv and verify with operator-courier
  - build image for operator-registry
  - create catalogsource using the registry image
    - if the sourcenamespace has an operatorgroup watching the targetnamespaces, then the operator can be installed to the targetnamespace
    - otherwise, need to create an operatorgroup
  - create the operator deployment with a subscription
  - deploy the application by creating an instance of the provided API