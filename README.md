Raft Lite Deployment Report
Student: Temirlan Galymtayev
Course: Distributed Computing – AWS EC2-based

1.	Cluster Startup
Description:
The same node.py code was deployed on all 3 nodes. Each node was started with its own ID, port, and peers.
Commands:
Node A: python3 node.py --id A --port 8000 --peers http://172.31.20.250:8001,http://172.31.16.147:8002
Node B: python3 node.py --id B --port 8001 --peers http://172.31.28.165:8000,http://172.31.16.147:8002
Node C: python3 node.py --id C --port 8002 --peers http://172.31.28.165:8000,http://172.31.20.250:8001
Observations:
•	All nodes start as Followers.
•	After a short timeout, one node becomes Leader automatically.
•	Status check example: curl http://172.31.28.165:8000/status
   ________________________________________
2.	Scenario: Leader Election
Steps:
1.	Wait 3–5 seconds after startup.
2.	Observe logs for candidate timeout and leader election.
Example logs:
[Node B] Timeout → Candidate (term 3)
[Node B] Became Leader (term 3)
  ________________________________________
3.	Scenario: Log Replication
Step 1 – Send Command to Leader:
curl -X POST http://:/command -H "Content-Type: application/json" -d '{"cmd":"SET x=5"}'
Step 2 – Verification:
curl http://:/status
Expected Output (all nodes):
"log":[{"term":3,"cmd":"SET x=5"}],
"commitIndex":0
Observations:
•	Leader appends command to its log.
•	Followers replicate the log via AppendEntries.
•	Majority acknowledgment → entry committed.
•	All nodes applied the entry.
On B node:
 

On C node:
 ________________________________________
4.	Scenario: Leader Crash
Steps:
1.	Kill the leader node process (e.g., Node B): CTRL+C
 
2.	Observe remaining nodes:
[Node C] Timeout → Candidate (term 4)
[Node C] Became Leader (term 4)


3.	Send a new command to the new leader:
curl -X POST http://:/command -H "Content-Type: application/json" -d '{"cmd":"SET y=10"}'

 
4.	Verify /status: Followers applied new command. Logs are consistent.
 
________________________________________
5.	Scenario: Follower Crash
Steps:
1.	Kill a follower (Node A): CTRL+C
2.	Send command to leader:
curl -X POST http://:/command -H "Content-Type: application/json" -d '{"cmd":"SET z=20"}'
Node C:
 
3.	Restart follower:
Node A:
 

4.	Verify /status: Follower catches up automatically. Logs updated. commitIndex correct.
 
6.	Client Read Commands
•	Check all committed entries using /status:
curl http://:/status
•	All nodes should have the same committed logs:
"log":[{"term":3,"cmd":"SET x=5"}, {"term":4,"cmd":"SET y=10"}, {"term":4,"cmd":"SET z=20"}],
"commitIndex":2
    
________________________________________

