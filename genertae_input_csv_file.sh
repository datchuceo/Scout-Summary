#!/bin/bash

REPORT="confor.csv"

echo "BUCKET,SERVER,Private_IP,OS_NAME,MIN_DATE,MAX_DATE,No.of.DATES,No.FILES,Total_SIZE,GOOD_FILES,FAILED_FILES,Comments" > "$REPORT"

for bucket in */; do
    [ -d "$bucket" ] || continue

    for srv in "$bucket"*/; do
        [ -d "$srv" ] || continue

        bucket_name=$(basename "$bucket")
        server_name=$(basename "$srv")

        first_json=$(find "$srv" -type f -name "*.json" | head -1)

        if [ -n "$first_json" ]; then
            private_ip=$(jq -r '.server_inventory.server.PrivateIP // "Not Found"' "$first_json")
            os_name=$(jq -r '.server_inventory.server.CurrentOS // "Not Found"' "$first_json")
            status=$(jq -r '.collection_metadata.status // ""' "$first_json")

            comments=$(jq -r '.collection_metadata.errors[0] // empty' "$first_json")

            if [ -z "$comments" ]; then
                comments="OK"
            fi
        else
            private_ip="Not Found"
            os_name="Not Found"
            comments="No JSON found"
        fi

        min_date=$(find "$srv" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" 2>/dev/null | sort | head -1)
        max_date=$(find "$srv" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" 2>/dev/null | sort | tail -1)

        dates=$(find "$srv" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
        files=$(find "$srv" -type f 2>/dev/null | wc -l)

        size=$(du -sh "$srv" 2>/dev/null | awk '{print $1}')

        total_json=$(find "$srv" -type f -name "*.json" 2>/dev/null | wc -l)

        good=$(find "$srv" -type f -name "*.json" \
            -exec grep -l '"status"[[:space:]]*:[[:space:]]*"success"' {} \; \
            2>/dev/null | wc -l)

        failed=$((total_json - good))

        echo "$bucket_name,$server_name,$private_ip,\"$os_name\",$min_date,$max_date,$dates,$files,$size,$good,$failed,\"$comments\"" >> "$REPORT"

    done
done

echo "Report created successfully: $REPORT"