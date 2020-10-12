# DS course  
# Project 2  
# Simple Distributed File System 

All storages and name server supposed to be in a single LAN.  
Client has to be exposed to the open network.  


## How to start:  
Storage:  
```
docker run -it -p 3504-3600:3504-3600 r0ach20/dfs_storage_server
```
Name:  
```
docker run -it -p 6235:6235 r0ach20/dfs_name_server
```
Only one storage could be deployed on a single machine.  
After starting system is ready to use, and clients can connect to the name server.  
Client:  
```
docker run -it -p 3504-3600:3504-3600 r0ach20/dfs_client (ip address of the name server)
```
or
```
python3 client.py (ip address of the name server)
```

## Architectural diagram
![diag](https://github.com/validolchik/ds_project2/blob/main/images/DS2.png)

## Protocols  
### Read and write  
When client wants to transfer a file to a DFS he requests name-server and name-server gives him storage port to listen on (and file size in case of download/read), then storage-server connects to a announced port and start file transferring.

### Storage discover and synchronization  
Every 5 seconds name-server broadcasts message and waiting responses from storage-servers. Then collect answered storage-servers and tell them to synchronize their files.

### Everything else
Every other message inthe system follows simple `type][arg1][arg2][padding` sturcture followed by the response `type][body_length][body`

Reference to table of protocols, more detailed: https://docs.google.com/spreadsheets/d/1Ov3wcuMT1hI4QgR1GAVh3E5hFbQBPmeyS_unEH2pSok/edit?usp=sharing  

## Contribution
Evgeniy - storage, name - servers, readme, presentation, report;
Renat - client, fixing storage, name - servers, architectural diagram, presentation, report.

## Docker images
# Client
https://hub.docker.com/repository/docker/r0ach20/dfs_client
# Name-server
https://hub.docker.com/repository/docker/r0ach20/dfs_name_server
# Storage-server
https://hub.docker.com/repository/docker/r0ach20/dfs_storage_server

