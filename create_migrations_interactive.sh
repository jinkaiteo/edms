#!/bin/bash

# Interactive Migration Creation Script
# This script helps create migrations when Django needs answers to questions

set -e

CONTAINER_NAME="edms_prod_backend"

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              Interactive Migration Creation Script                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "This script will help you create Django migrations."
echo "You'll need to answer some questions from Django."
echo ""
echo "Common questions and recommended answers:"
echo "  1. 'Was fieldX renamed to fieldY?' → Type 'n' (No)"
echo "  2. 'It is impossible to add non-nullable field' → Type '1' (Provide default)"
echo "  3. 'Please enter the default value' → Type 'timezone.now()'"
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "Creating migrations for scheduler app..."
echo ""

docker exec -it $CONTAINER_NAME python manage.py makemigrations scheduler

echo ""
echo "Creating migrations for workflows app..."
echo ""

docker exec -it $CONTAINER_NAME python manage.py makemigrations workflows

echo ""
echo "Creating migrations for documents app..."
echo ""

docker exec -it $CONTAINER_NAME python manage.py makemigrations documents

echo ""
echo "Creating migrations for all other apps..."
echo ""

docker exec -it $CONTAINER_NAME python manage.py makemigrations

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Migrations Created Successfully!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Now applying migrations..."
docker exec $CONTAINER_NAME python manage.py migrate

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Migrations Applied Successfully!                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Running tests..."
./fix_migrations_and_test.sh

