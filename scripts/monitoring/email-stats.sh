#!/bin/bash
# Email Notification Statistics
# Shows email activity breakdown

echo "========================================="
echo "  Email Notification Statistics"
echo "  $(date)"
echo "========================================="
echo ""

# Time period
PERIOD="${1:-24h}"
echo "Period: Last $PERIOD"
echo ""

# Total emails sent
TOTAL=$(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "Email sent" || echo "0")
echo "📧 Total Emails Sent: $TOTAL"
echo ""

# By notification type
echo "By Notification Type:"
echo "  - Task Assignments:    $(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "send_task_email" || echo "0")"
echo "  - Document Effective:  $(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "send_document_effective" || echo "0")"
echo "  - Document Obsolete:   $(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "send_document_obsolete" || echo "0")"
echo "  - Workflow Timeout:    $(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "send_workflow_timeout" || echo "0")"
echo "  - Test Emails:         $(docker compose logs celery_worker --since="$PERIOD" 2>/dev/null | grep -c "send_test_email" || echo "0")"
echo ""

# Failures
FAILURES=$(docker compose logs backend celery_worker --since="$PERIOD" 2>/dev/null | grep -ci "failed.*email\|error.*smtp" || echo "0")
echo "❌ Failures: $FAILURES"
if [ $TOTAL -gt 0 ]; then
    FAILURE_RATE=$(awk "BEGIN {printf \"%.1f\", ($FAILURES/$TOTAL)*100}")
    echo "   Failure Rate: $FAILURE_RATE%"
fi
echo ""

# Success rate
if [ $TOTAL -gt 0 ]; then
    SUCCESS=$((TOTAL - FAILURES))
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS/$TOTAL)*100}")
    echo "✅ Success Rate: $SUCCESS_RATE%"
else
    echo "ℹ️  No email activity in this period"
fi

echo ""
echo "========================================="
