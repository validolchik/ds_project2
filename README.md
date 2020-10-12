<h1>DS course  
Project 2  
Simple Distributed File System</h1>  

All storages and name server supposed to be in a single LAN.  
Client has to be exposed to the open network.  


How to start:  
Storage:  
```
docker run -it -p 3504-3600:3504-3600 r0ach20/dfs_storage_server
```
Name:  
```
docker run -it -p 6235:6235 r0ach20/dfs_storage_server
```
