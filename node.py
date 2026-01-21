#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request
import argparse
import json
import threading
import time
import random

# =======================
# Global Raft State
# =======================
NODE_ID = ""
PORT = 0
PEERS = []

state = "Follower"        # Follower | Candidate | Leader
currentTerm = 0
votedFor = None
leaderId = None

log = []                  # [{term, cmd}]
commitIndex = -1
lastApplied = -1

lastHeartbeat = time.time()
lock = threading.Lock()

# =======================
# Utility
# =======================
def majority():
    return (len(PEERS) + 1) // 2 + 1


def send_post(url, data):
    try:
        req = request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


# =======================
# Election Logic
# =======================
def start_election():
    global state, currentTerm, votedFor

    with lock:
        state = "Candidate"
        currentTerm += 1
        votedFor = NODE_ID
        votes = 1

    print(f"[Node {NODE_ID}] Timeout → Candidate (term {currentTerm})")

    for peer in PEERS:
        res = send_post(peer + "/request_vote", {
            "term": currentTerm,
            "candidateId": NODE_ID
        })

        if res and res.get("voteGranted"):
            votes += 1

    if votes >= majority():
        become_leader()


def become_leader():
    global state, leaderId
    state = "Leader"
    leaderId = NODE_ID
    print(f"[Node {NODE_ID}] Became Leader (term {currentTerm})")


def election_timeout_loop():
    while True:
        timeout = random.uniform(3, 5)
        time.sleep(timeout)
        if state != "Leader" and time.time() - lastHeartbeat > timeout:
            start_election()


# =======================
# Heartbeats
# =======================
def heartbeat_loop():
    while True:
        if state == "Leader":
            for peer in PEERS:
                send_post(peer + "/append_entries", {
                    "term": currentTerm,
                    "leaderId": NODE_ID,
                    "entries": []
                })
        time.sleep(1)


# =======================
# Log Application
# =======================
def apply_entries():
    global lastApplied
    while lastApplied < commitIndex:
        lastApplied += 1
        print(f"[Node {NODE_ID}] Apply → {log[lastApplied]['cmd']}")


# =======================
# HTTP Handler
# =======================
class Handler(BaseHTTPRequestHandler):

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        global currentTerm, votedFor, state, leaderId, lastHeartbeat, commitIndex

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        # ================= RequestVote =================
        if self.path == "/request_vote":
            term = body["term"]
            candidateId = body["candidateId"]

            with lock:
                if term > currentTerm:
                    currentTerm = term
                    votedFor = None
                    state = "Follower"

                voteGranted = False
                if votedFor is None:
                    votedFor = candidateId
                    voteGranted = True

            self._send(200, {
                "term": currentTerm,
                "voteGranted": voteGranted
            })
            return

        # ================= AppendEntries =================
        if self.path == "/append_entries":
            term = body["term"]
            leaderId = body["leaderId"]
            entries = body["entries"]

            with lock:
                if term >= currentTerm:
                    currentTerm = term
                    state = "Follower"
                    lastHeartbeat = time.time()

                for e in entries:
                    log.append(e)
                    print(f"[Node {NODE_ID}] Append log {e}")

                if entries:
                    commitIndex = len(log) - 1
                    apply_entries()

            self._send(200, {"success": True})
            return

        # ================= Client Command =================
        if self.path == "/command":
            if state != "Leader":
                self._send(403, {"error": "Not leader", "leader": leaderId})
                return

            cmd = body.get("cmd")
            entry = {"term": currentTerm, "cmd": cmd}
            log.append(entry)

            print(f"[Leader {NODE_ID}] Append log entry {cmd}")

            acks = 1
            for peer in PEERS:
                res = send_post(peer + "/append_entries", {
                    "term": currentTerm,
                    "leaderId": NODE_ID,
                    "entries": [entry]
                })
                if res:
                    acks += 1

            if acks >= majority():
                commitIndex = len(log) - 1
                print(f"[Leader {NODE_ID}] Entry committed (index={commitIndex})")
                apply_entries()

            self._send(200, {"ok": True})
            return

        self._send(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/status":
            self._send(200, {
                "node": NODE_ID,
                "state": state,
                "term": currentTerm,
                "leader": leaderId,
                "log": log,
                "commitIndex": commitIndex
            })
            return

        self._send(404, {"error": "Not found"})

    def log_message(self, *args):
        return

def main():
    global NODE_ID, PORT, PEERS

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--peers", required=True)
    args = parser.parse_args()

    NODE_ID = args.id
    PORT = args.port
    PEERS = [p.strip() for p in args.peers.split(",")]

    print(f"[Node {NODE_ID}] Started on port {PORT}")

    threading.Thread(target=election_timeout_loop, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
