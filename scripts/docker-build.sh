#!/bin/bash

# Nexora AI Docker Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="nexora-ai"
TAG="latest"
REGISTRY=""
PLATFORM="linux/amd64"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -t, --tag TAG         Image tag (default: latest)"
            echo "  -r, --registry REG    Registry prefix"
            echo "  -p, --platform PLAT   Target platform (default: linux/amd64)"
            echo "  --push                Push image after build"
            echo "  -h, --help            Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Set full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

echo -e "${GREEN}🏗️  Building Docker image...${NC}"
echo -e "Image: ${YELLOW}$FULL_IMAGE_NAME${NC}"
echo -e "Platform: ${YELLOW}$PLATFORM${NC}"

# Build the Docker image
docker build \
    --platform "$PLATFORM" \
    --tag "$FULL_IMAGE_NAME" \
    --file Dockerfile \
    .

echo -e "${GREEN}✅ Build completed successfully!${NC}"

# Push if requested
if [ "$PUSH" = true ]; then
    echo -e "${GREEN}📤 Pushing image to registry...${NC}"
    docker push "$FULL_IMAGE_NAME"
    echo -e "${GREEN}✅ Push completed successfully!${NC}"
fi

# Show image size
echo -e "${GREEN}📊 Image information:${NC}"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo -e "${GREEN}🚀 Image ready: $FULL_IMAGE_NAME${NC}"
echo -e "${YELLOW}💡 To run: docker run -p 8000:8000 $FULL_IMAGE_NAME${NC}"
echo -e "${YELLOW}💡 To run with compose: docker-compose up${NC}" 