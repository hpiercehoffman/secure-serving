# Secure Model Serving with AWS Nitro Enclaves

This is a course project for [Harvard CS 243](https://github.com/minlanyu/cs243-site). 

### Introduction ###

What are our options for secure ML model serving in the cloud? Deploying any model to the cloud poses an inherent security risk, since it involves trusting code and data to a third party. As we run ML models on increasingly sensitive data, and as models themselves become more attractive targets for adversarial attacks, we need to be able to minimize our attack surface when deploying ML applications in the cloud.

[AWS Nitro Enclaves](https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html) are one of many possible solutions for improved security in cloud applications. A Nitro Enclave is a secure computing environment which is created from physically partitioned CPUs and memory inside a parent EC2 instance. The Nitro Enclave has no interactive access, persistent storage, or external networking capability. All communication with the outside world goes through a VSOCK channel, a secure local socket connection to the parent instance. Nitro Enclaves also offer the option for cryptographic attestation, an additional level of verification which allows the enclave to cryptographically prove its identity to another party.

If you want to actually deploy an ML model inside a Nitro Enclave, the process is not particularly well-documented. In general, it seems to be uncommon to deploy applications of any complexity within enclaves, possibly due to misinformation about their memory limitations. However, it is completely possible to serve ML applications in an enclave context. In this README, I will document the steps I took to serve a ResNet model inside a Nitro Enclave, as well as instructions for collecting various performance measurements. Please see [the report](https://github.com/hpiercehoffman/secure-serving/blob/main/report/Hannah_Pierce_Hoffman_CS243_FinalReport.pdf) for additional details on the experiments I ran. 

### Installation and Setup ###

Hopefully you have an AWS account. Start by [creating an EC2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html). I recommend a pretty big one: at least `c6a.8xlarge` (32 vCPUs and 64 GB of RAM) or larger. Even small enclaves take a lot of RAM to build, and each instance type has a maximum RAM allocation for enclaves. 
- When creating the instance, make sure to add it to a [security group](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html). If you want to serve internet requests, you should enable TCP and HTTP or HTTPS traffic on port 80 (or port 443 for HTTPS).
- I recommend using Amazon Linux 2 as the base image type, since it seems to have more built-in features compared to Amazon Linux 3.

It's not necessary to generate an SSH key during instance creation, but if you do, generate a PEM key and store it safely on your local machine. If you don't generate a specific SSH key for the instance, you can log in with your personal SSH key, and it will be easier than trying to remember where you stored the unique PEM key for each instance. (Follow [these instructions](https://docs.tritondatacenter.com/public-cloud/getting-started/ssh-keys/generating-an-ssh-key-manually/manually-generating-your-ssh-key-in-mac-os-x) to generate a personal SSH key if you don't have one.)

To log into the VM using your personal SSH key, type the following:    
`ssh -i ~/.ssh/id_rsa ec2-user@<VM External IP>`     
The VM external IP can be found on the EC2 instances page.    

Start by installing docker on the instance:   
`sudo yum install -y docker`   
`sudo service docker start;`    
`sudo usermod -a -G docker ec2-user;`   
`sudo chkconfig docker on`    

Next, install the `nitro-cli` toolkit. This sets up some basic functionalities for building and running Nitro Enclaves. You can also install Git at the same time, since you will need it in the next step.         
`sudo yum install --assumeyes aws-nitro-enclaves-cli aws-nitro-enclaves-cli-devel git`
`sudo usermod -aG ne ec2-user`    

Install the Enclaver toolkit following [these instructions](https://edgebit.io/enclaver/docs/0.x/guide-first/). There are several toolkits that offer utilities for building and running enclaves, but out of three I tried, Enclaver was the only one that actually worked. 

Finally, you need to configure the Nitro Enclaves allocator service to let us build and run large enclaves. If this is not done, you will only be able to run trivial applications.   
`sudo sed -i 's/cpu_count: 2/cpu_count: 8/g' /etc/nitro_enclaves/allocator.yaml`   
`sudo sed -i 's/memory_mib: 512/memory_mib: 8192/g' /etc/nitro_enclaves/allocator.yaml`    
`sudo systemctl start nitro-enclaves-allocator.service && sudo systemctl enable nitro-enclaves-allocator.service`   

I think 8 CPUs and 8 GB of RAM is the maximum allocation on a `c6a.8xlarge` instance, but you could try going higher. If you've allocated values that are too high, `nitro-cli` will tell you when you try to build your first enclave.

### Turning a Docker image into a Nitro Enclave ###

Now you should be ready to start creating enclaves. First, you need to download or create a Docker image on your EC2 instance. The "proper" way to do this is by building the image locally and pushing it to Elastic Container Registry (ECR), then pulling the image from ECR onto the VM. If you're using this route, follow [these instructions](https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html). However, be warned that authenticating to the AWS CLI is quite difficult. If you are a root AWS user, you might need to [create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html) to be able to authenticate properly. The IAM user account generates a series of keys, which you need to enter into the `aws configure sso` command every time you open a new terminal session. I'm sure there is an easier way to do this, but it wasn't easily discernible from the AWS documentation. If you would like to avoid this hassle, you can also push your Dockerfile to a Git repo, clone the repo on EC2, and build the Docker image locally. 

**Note:** When your container runs as an enclave, it will not have any internet access to download Git repos, pretrained models, etc. Therefore, you must include *all* of the necessary files inside the container itself.

Once the Docker image is ready, create an Enclaver YAML file to describe the configuration to be allocated to your enclave. See [this example](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/secure/resnet.yaml) for file format. The memory allocated to your enclave in the YAML file must be less than or equal to the memory limit you set in `/etc/nitro_enclaves/allocator.yaml`. 

Now build the enclave:    
`sudo enclaver build --file resnet.yaml`     

### Running the enclave without Nginx ###

If you are running an ML server in an enclave and you would like to test **without** nginx, you can directly forward incoming traffic from port 80 on the parent VM to the enclave's ingress port. Use the following command:    
`sudo enclaver run --publish 80:9000 resnet-enclave:latest`    

When the enclave is running in this configuration, you can't handle HTTP traffic, but you can still send requests over the internet via SSH. Run the following command on your local machine:   
`ssh -i ~/.ssh/id_rsa -N -f -L 8888:localhost:80  ec2-user@<EC2 public IP>`    

This command connects port 80 of the enclave to port 8888 on your local machine. You can now interact with the enclave via calls to `http://localhost:8888`. 

### Running the enclave with Nginx ### 

To handle HTTP traffic, you can use Nginx as a reverse proxy on your parent EC2 instance. Nginx listens on port 80 and forwards traffic to your enclave's exposed port. In this repo, I provide a [custom Nginx conf file](https://github.com/hpiercehoffman/secure-serving/blob/main/nginx/nginx-basic.conf) which sets up forwarding to a container (regular Docker or enclave) running on port 9000. The custom conf file also increases the maximum allowed size of requests, so we can serve requests up to 50MB in size. Place this file in `/etc/nginx/nginx.conf` and run `sudo systemctl start nginx`. You should now be able to send HTTP requests to the extneral IP address of the parent EC2 instance, and Nginx will pass them along to the enclave.

This is the configuration I use for [internet load testing](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/load_testing.ipynb). I run either an enclave server or a standard Docker server on port 9000 of the parent EC2 instance, then measure their ability to handle concurrent requests. For local load testing, I use the same setup, except I run a [script](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/load_testing.py) directly on the parent instance, so it doesn't matter whether Nginx is running.

### Routing a mixed stream of requests to an enclave server and a standard server ###

What if only some of your incoming traffic is subject to increased privacy restrictions? This *mixed-privacy* scenario could occur if some users have opted into additional privacy protections, or if users are located in different countries with different privacy laws. Or you might be A/B testing a new model which needs to remain secure until it's ready for launch. 

If you want to run an enclave server and a standard server side-by-side to handle a stream of mixed requests, follow these steps:
- Install Node.js following [these instructions](https://stackoverflow.com/questions/72544861/install-node-in-amazon-linux-2) for installing on Amazon Linux 2.
- Create a Node server using [this code](https://github.com/hpiercehoffman/secure-serving/blob/main/routing-server/server.js).
- The Node server runs on port 3000, so we need to update our [Nginx conf file](https://github.com/hpiercehoffman/secure-serving/blob/main/nginx/nginx-node.conf) to forward incoming requests to this port. 
- Restart Nginx with the updated configuration: `sudo systemctl start nginx`
- Start the Node server. You may need to be root to do this. Use command: `sudo "$(which node)" server.js`
- Start the standard server to handle "less secure" requests. In this example, we run the standard server as a [Docker container](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/public/Dockerfile) on port 9000. Run the docker: `docker run -p 9000:9000 resnet-public`
- Start the enclave server on port 9001. `sudo enclaver run --publish 9001:9000 resnet-enclave:latest`

At this point, the Node server should be running on port 3000, with Nginx forwarding incoming requests to Node. The Node server will look at the API prefix of each request. Requests made to `/predict-secure/` will be forwarded to the secure server on port 9001, while requests made to `/predict-public/` will be forwarded to the standard server running on port 9000. It's not necessary to change the name of the prediction endpoint in the servers themselves: for both servers, we are forwarding requests to the `/predict/` endpoint that would be used when running each server individually. All you need to do is ensure that your *client* differentiates between secure and standard requests, and prefixes them with the appropriate API name.

### I/O throughput testing with iperf ###

What's the maximum amount of I/O bandwidth that a Nitro Enclave can handle? How does this compare to the I/O bandwidth for a standard server running in a Docker container? We can answer these questions with the [iperf-vsock](https://github.com/stefano-garzarella/iperf-vsock) utility. Setting this up is somewhat complicated, so we will walk through the steps below:
- First, clone `iperf-vsock` onto your parent EC2 instance using the link above. There is a bug in the latest commit, so you need to checkout commit `9245f9a`.
- Install `iperf-vsock` following the repo instructions. You may need to install libtool first: `sudo apt-get install libtool` 
- Make a Dockerfile which builds and runs `iperf-vsock` inside a Docker container. Use my templates to ensure you have included all necessary libraries:
    - [Standard server](https://github.com/hpiercehoffman/secure-serving/blob/main/perf_tests/iperf/public/Dockerfile)
    - [Enclave server](https://github.com/hpiercehoffman/secure-serving/blob/main/perf_tests/iperf/secure/Dockerfile)
- For a standard server, the `CMD` the Docker runs should be `iperf3 -s`. This is because our standard server is running in a regular Docker container, which communicates with the host VM using a TCP/IP socket. No VSOCK is present.
- For an enclave server, the `CMD` entrypoint should be `iperf3 --vsock -s`. This tells `iperf-vsock` that we're sending bytes through the VSOCK, which is a specialized socket originally intended for a hypervisor to communicate with a VM.
- Now you can build the standard and enclave containers following the instructions above. I provide an [Enclaver config file](https://github.com/hpiercehoffman/secure-serving/blob/main/perf_tests/iperf/secure/iperf.yaml) for building the enclave.
- Run the standard server: 
- Start one of the servers (either run the Docker container for the standard server, or run the enclave using Enclaver). Make sure the server is connected to port 9000. 
- If running the standard server, run the following on the parent EC2 host:
    - `cd iperf-vsock/src`
    - `./iperf3 -c localhost:9000`
- The `iperf` client will send bytes to the standard server for 10 seconds, recording the maximum I/O throughput every second.
- If running the enclave server, you need to determine the **channel ID** of the VSOCK. As far as I can tell, this is a random number and it's not visible anywhere. It seems to start at 4 and increments every time you run a new enclave. Luckily, you can get around this issue with a simple [script](https://github.com/hpiercehoffman/secure-serving/blob/main/perf_tests/iperf/secure/iperf-find-channel-id.sh) which iterates through every possible channel ID from 0-100, calling iperf each time. For me, the magic number was 37.

### Run an enclave server with KMS cryptographic attestation enabled ###

In addition to the performance benchmarks shown in my [report](https://github.com/hpiercehoffman/secure-serving/blob/main/report/Hannah_Pierce_Hoffman_CS243_FinalReport.pdf), I did some preliminary tests for how enclaves with [KMS cryptographic attestation](https://docs.aws.amazon.com/kms/latest/developerguide/services-nitro-enclaves.html) perform. I found that an enclave with KMS enabled behaves very similarly to an enclave without KMS enabled unless you start actively making KMS requests. Fully testing this line of inquiry was ultimately out of scope for my project. However, I will share some setup hints if you would like to get KMS attestation running for your enclave application. 
- Set up allowed egresses for your enclave so it can contact the KMS server. An Enclaver config file with these egresses looks like [this](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/kms/resnet-kms.yaml).
- Change the allowed number of hops for outgoing PUT requests. This is necessary so your enclave can actually contact the KMS server from within a container. The command looks like this: `aws ec2 modify-instance-metadata-options --instance-id <Instance ID, starts with "i-"> --http-put-response-hop-limit 3 --http-endpoint enabled`
- Before running this command on your local machine, you need to run `aws configure sso` and enter the sign-in information from an AWS IAM role. Make sure to enter `json` (all lowercase) when prompted for "output".
- You might also need to [add an AWS role to your EC2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html) so the instance can talk to the KMS server.
- One other note is that the Dockerfile for any enclave that uses KMS **cannot** use multi stage builds. Use a template like [this](https://github.com/hpiercehoffman/secure-serving/blob/main/load_testing/kms/Dockerfile) to ensure that your enclave build is simple enough to work with KMS.
- After this setup process, it should theoretically be possible to build and run an enclave which is able to connect to the KMS server: `sudo enclaver run --publish 9000:8001 resnet-kms:latest`
- In the output of the run command, you should be able to see that the enclave makes contact with the KMS server.


