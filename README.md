## EBUCore+ Demonstrator Kit

We can try out the EBUCore+ Demonstrator Kit in three ways. 

1) Community Edition 
2) Hybrid Installation
3) Local Installation


## Community Edition
 
The community edition is the shared instance which is directly available [Here](https://ebucore-plus-dk.org/)


For hybrid and local installation, we would need to have Prerequisites fulfilled 

## Prerequisites

[Docker Compose](https://docs.docker.com/compose/)

Docker Desktop for Windows or Mac includes Docker Compose. Run this command to verify:

```bash
docker-compose version
```

If you use the Linux operating system, Install [Docker Compose](https://docs.docker.com/compose/install/).

## Installation

Clone the repository

```bash
git clone https://github.com/ebu/coreplus-demo.git
```


## Hybrid Installation
 
In the hybrid installation, the user would have their own Jupyter lab environment in which they could play with which would be connected to the cloud backend services.

### Intallation

To install the hybrid version we will go to the terminal in the coreplus-demo directory and run this command.

```bash
docker-compose -f .\docker-compose-hybrid.yml up -d
```


The CDK would be available on the browser at [http://localhost:8888](http://localhost:8888)

Similarly, we can compose it down with the command

```bash
docker-compose -f .\docker-compose-hybrid.yml down
```

## Local Installation
 
In the local installation, the user would get both the frontend and the backend running n their local instance which they could use locally on their machine.

### Installation

To install the hybrid version we will go to the terminal in the coreplus-demo directory and run this command.

```bash
docker-compose -f .\docker-compose-local.yml up -d
```

Similarly, we can compose it down with the command

```bash
docker-compose -f .\docker-compose-local.yml down
```

The CDK would be available on the browser at [http://localhost:8888](http://localhost:8888)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
