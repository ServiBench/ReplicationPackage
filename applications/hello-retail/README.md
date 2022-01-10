# Hello, Retail!

Hello, Retail! is a Nordstrom Technology open-source project. Hello, Retail! is a 100% serverless, event-driven framework and functional proof-of-concept showcasing a central unified log approach as applied to the retail problem space. All code and patterns are intended to be re-usable for scalable applications large and small.

# Deploy

```shell
# in the root directory of the repository, install dependencies, STAGE=prod, REGION=us-east-1, COMPANY=yourcompany, TEAM=yourteam
./install.sh REGION STAGE COMPANY TEAM
# before calling, adjust the sb config in hello_retail_benchmark.py accordingly
sb prepare
```
