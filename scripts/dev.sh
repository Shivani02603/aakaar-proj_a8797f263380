#!/bin/bash
set -euo pipefail

# Start the backend in the background
./scripts/entrypoint.sh &

# Start the frontend development server
cd frontend
npm run dev &

# Wait for both processes to finish
wait