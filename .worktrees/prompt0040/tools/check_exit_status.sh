#!/bin/bash

# 1. Automatically detect the latest build number from your dist folder
LATEST_BUILD=$(ls -d dist/build_*/ 2>/dev/null | sed 's|dist/build_||;s|/||' | sort -n | tail -1)

# 2. Define the path to the status file on your Windows drive
STATUS_FILE="/mnt/c/Rastan-Genesis/exit_status_build_${LATEST_BUILD}.txt"

# 3. Check if the file actually exists
if [ ! -f "$STATUS_FILE" ]; then
    echo "----------------------------------------------------------"
    echo "ERROR: Exit status file not found for Build ${LATEST_BUILD}."
    echo "Path: ${STATUS_FILE}"
    echo "Did you close BlastEm yet?"
    echo "----------------------------------------------------------"
    exit 1
fi

# 4. Read the exit code and strip any weird Windows line endings
EXIT_CODE=$(cat "$STATUS_FILE" | tr -d '\r\n ')

# 5. Determine if it was a success or a crash
if [ "$EXIT_CODE" == "0" ]; then
    RESULT="SUCCESS (0)"
else
    RESULT="CRASH/ERROR (${EXIT_CODE})"
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 6. Format the Markdown entry for the log
echo "" >> AGENTS_LOG.md
echo "### [Emulator Exit Audit - Build ${LATEST_BUILD}]" >> AGENTS_LOG.md
echo "- **Status Code:** ${EXIT_CODE}" >> AGENTS_LOG.md
echo "- **Result:** ${RESULT}" >> AGENTS_LOG.md
echo "- **Timestamp:** ${TIMESTAMP}" >> AGENTS_LOG.md
echo "" >> AGENTS_LOG.md

# 7. Cleanup the temporary Windows file
rm "$STATUS_FILE"

echo "----------------------------------------------------------"
echo "Log updated for Build ${LATEST_BUILD} with status: ${RESULT}"
echo "Windows temporary status file has been cleared."
echo "----------------------------------------------------------"