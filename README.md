Raft Lite Deployment Report
Student: Temirlan Galymtayev
Course: Distributed Computing – AWS EC2-based

*1.	Cluster Startup
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
<img width="974" height="227" alt="image" src="https://github.com/user-attachments/assets/da644734-4ef8-46bc-a3e4-56d2dadfe210" />

<img width="974" height="95" alt="image" src="https://github.com/user-attachments/assets/54afa88c-867d-4fa9-9280-bd48b08dfc44" />

<img width="974" height="77" alt="image" src="https://github.com/user-attachments/assets/95cf1ae3-3d08-4da5-9689-d14fd773944a" />


   ________________________________________
*2.	Scenario: Leader Election
Steps:
1.	Wait 3–5 seconds after startup.
2.	Observe logs for candidate timeout and leader election.
Example logs:
[Node B] Timeout → Candidate (term 3)
[Node B] Became Leader (term 3)
<img width="974" height="37" alt="image" src="https://github.com/user-attachments/assets/06c13cca-f5e5-42da-ab82-2e7807c07266" />

<img width="974" height="128" alt="image" src="https://github.com/user-attachments/assets/6b741fdc-6a39-41ef-bc80-e3525b00b23a" />

  ________________________________________
*3.	Scenario: Log Replication
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
<img width="974" height="116" alt="image" src="https://github.com/user-attachments/assets/184e77cd-2798-4c9a-bba9-caa414b3fba4" />


On C node:
<img width="974" height="48" alt="image" src="https://github.com/user-attachments/assets/08f8ccbc-ff2a-430d-babc-8a45f7a38af7" />

 ________________________________________
*4.	Scenario: Leader Crash
Steps:
1.	Kill the leader node process (e.g., Node B): CTRL+C

 <img width="974" height="126" alt="image" src="https://github.com/user-attachments/assets/a8554e68-2e94-48a0-953d-254f8b20f44b" />

2.	Observe remaining nodes:
[Node C] Timeout → Candidate (term 4)
[Node C] Became Leader (term 4)


3.	Send a new command to the new leader:
curl -X POST http://:/command -H "Content-Type: application/json" -d '{"cmd":"SET y=10"}'

<img width="974" height="122" alt="image" src="https://github.com/user-attachments/assets/2f9bc486-649c-4e34-a91f-b5f5eec7f7c9" />

 
4.	Verify /status: Followers applied new command. Logs are consistent.

<img width="1062" height="53" alt="image" src="https://github.com/user-attachments/assets/54cf4e1d-5330-4901-8e93-2aa2d9bc4d09" />

 
________________________________________
*5.	Scenario: Follower Crash
Steps:
1.	Kill a follower (Node A): CTRL+C
2.	Send command to leader:
curl -X POST http://:/command -H "Content-Type: application/json" -d '{"cmd":"SET z=20"}'
Node C:
 <img width="974" height="73" alt="image" src="https://github.com/user-attachments/assets/437a3365-31da-42da-aae2-27b7f2bcdfdc" />

3.	Restart follower:
Node A:
 <img width="974" height="30" alt="image" src="https://github.com/user-attachments/assets/896003f3-f013-4ee2-9a9f-e55f2d620bb2" />


4.	Verify /status: Follower catches up automatically. Logs updated. commitIndex correct.
 <img width="974" height="48" alt="image" src="https://github.com/user-attachments/assets/3d791d45-51b2-446c-84ed-c141c5ede1f9" />

*6.	Client Read Commands
•	Check all committed entries using /status:
curl http://:/status
•	All nodes should have the same committed logs:
"log":[{"term":3,"cmd":"SET x=5"}, {"term":4,"cmd":"SET y=10"}, {"term":4,"cmd":"SET z=20"}],
"commitIndex":2
   <img width="764" height="45" alt="image" src="https://github.com/user-attachments/assets/b5e7c905-f0f4-4b0a-bff0-7508cf88febc" />
    
   <img width="603" height="58" alt="image" src="https://github.com/user-attachments/assets/ac9b12c2-5f96-48c3-91c1-9335b562507a" />
    
   <img width="603" height="58" alt="image" src="https://github.com/user-attachments/assets/0de312b7-6b2a-4376-b58f-a9effd33cff3" />

   <img width="603" height="58" alt="image" src="https://github.com/user-attachments/assets/d828b662-e3f1-4881-86ba-d8eae5de58d1" />


________________________________________

